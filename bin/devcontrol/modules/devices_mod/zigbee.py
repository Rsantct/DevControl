#!/usr/bin/env python3

# Path para poder probar el módulo suelto
import  os
import  sys
UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/bin/devcontrol/modules')

import json
import threading
import time
import paho.mqtt.client as mqtt
from   z2m_classifier import obtener_rol_dispositivos
from   fmt import Fmt


MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# QoS por tipo de topic
QoS_TOPIC_BASE = 0
QoS_TOPIC_SET = 2
QoS_TOPIC_GET = 0
QoS_TOPIC_INFO = 0

# Topics genéricos del bridge Zigbee2MQTT
TOPIC_INFO = "zigbee2mqtt/bridge/info"
TOPIC_DEVICES = "zigbee2mqtt/bridge/devices"
TOPIC_GROUPS = "zigbee2mqtt/bridge/groups"

DEVICES = []
GROUPS = []
ZNAME = ""
verbose = False
estado = {}
zigbbee_info = {}

DEVICES_POR_ROL = obtener_rol_dispositivos()

_mqtt_lock = threading.RLock()
_bridge_event = threading.Event()
_pending_lock = threading.Lock()
_pending_responses = {}  # topic -> {"event": Event, "payload": dict | None}
_subscribed_topics = set()

client = mqtt.Client()


def _subscribe_locked(topic, qos=0):
    if topic not in _subscribed_topics:
        rc, _ = client.subscribe(topic, qos)
        if rc == mqtt.MQTT_ERR_SUCCESS:
            _subscribed_topics.add(topic)


def _on_connect(cli, userdata, flags, rc):
    if rc == 0:
        if verbose:
            print(f"✅ Conectado al broker MQTT ({MQTT_HOST}:{MQTT_PORT})")
        with _mqtt_lock:
            # Re-suscribir topics tras reconexión
            previous_topics = list(_subscribed_topics)
            _subscribed_topics.clear()
            for topic in previous_topics:
                _subscribe_locked(topic, 0)
            _subscribe_locked(TOPIC_INFO, QoS_TOPIC_INFO)
            _subscribe_locked(TOPIC_DEVICES, 0)
            _subscribe_locked(TOPIC_GROUPS, 0)
    else:
        print(f"❌ Error de conexión con el broker MQTT: rc={rc}")


def _on_disconnect(cli, userdata, rc):
    if verbose and rc != 0:
        print(f"⚠️ Desconexión inesperada del broker MQTT (rc={rc}); se reintentará automáticamente.")


def _on_message(cli, userdata, msg):
    global DEVICES, GROUPS, estado, zigbbee_info

    topic = msg.topic
    raw_text = msg.payload.decode("utf-8", errors="replace")

    try:
        data = json.loads(raw_text)
    except Exception as e:
        if verbose:
            print(f"Error decodificando JSON en {topic}: {e}")
        return

    if topic == TOPIC_DEVICES:
        DEVICES = data
        if DEVICES and GROUPS:
            _bridge_event.set()
        if verbose:
            print(f"--- Recibidos DEVICES ({len(DEVICES)}) ---")

    elif topic == TOPIC_GROUPS:
        GROUPS = data
        if DEVICES and GROUPS:
            _bridge_event.set()
        if verbose:
            print(f"--- Recibidos GROUPS ({len(GROUPS)}) ---")

    elif topic == TOPIC_INFO:
        zigbbee_info = data
        if verbose:
            keys = list(zigbbee_info.keys()) if isinstance(zigbbee_info, dict) else type(zigbbee_info).__name__
            print("TOPIC_INFO recibido:", keys)

    else:
        # Respuesta de un dispositivo concreto (p. ej. zigbee2mqtt/<friendly_name>)
        estado = data
        if verbose:
            print(f"Mensaje en {topic}: {data}")

        with _pending_lock:
            waiter = _pending_responses.get(topic)
            if waiter is not None:
                waiter["payload"] = data
                waiter["event"].set()


def _ensure_connected(timeout=5.0):
    with _mqtt_lock:
        if not hasattr(client, "_thread") or client._thread is None or not client._thread.is_alive():
            client.on_connect = _on_connect
            client.on_disconnect = _on_disconnect
            client.on_message = _on_message
            client.reconnect_delay_set(min_delay=1, max_delay=10)

            try:
                rc = client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
            except Exception as e:
                print(f"(broker_mqtt_conectar) ERROR conectando a {MQTT_HOST}:{MQTT_PORT}: {e}")
                return False

            if rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"(broker_mqtt_conectar) ERROR código {rc} conectando a {MQTT_HOST}:{MQTT_PORT}")
                return False

            client.loop_start()

        deadline = time.time() + timeout
        while not client.is_connected() and time.time() < deadline:
            time.sleep(0.05)

        return client.is_connected()


def broker_mqtt_conectar(timeout=3):
    return _ensure_connected(timeout=timeout)


def broker_mqtt_desconectar():
    with _mqtt_lock:
        try:
            client.loop_stop()
        except Exception as e:
            if verbose:
                print(f"(broker_mqtt_desconectar) loop_stop error: {e}")
        try:
            client.disconnect()
        except Exception as e:
            if verbose:
                print(f"(broker_mqtt_desconectar) disconnect error: {e}")
        _subscribed_topics.clear()


def actualizar_devices_y_grupos(timeout=3.0, force=False):
    if not _ensure_connected(timeout=timeout):
        return False

    with _mqtt_lock:
        _subscribe_locked(TOPIC_DEVICES, 0)
        _subscribe_locked(TOPIC_GROUPS, 0)

        if force or not (DEVICES and GROUPS):
            _bridge_event.clear()
            if DEVICES and GROUPS and not force:
                return True
            _bridge_event.wait(timeout=timeout)

    return bool(DEVICES and GROUPS)


def is_group(zid):
    for grupo in GROUPS:
        if zid == grupo.get("friendly_name"):
            return True
    return False


def get_miembros_de_grupo(gname="", refresh=False):
    if refresh or not (DEVICES and GROUPS):
        actualizar_devices_y_grupos()

    miembros = []
    for grupo in GROUPS:
        if grupo.get("friendly_name", "") == gname:
            for m in grupo.get("members", []):
                miembros.append({"ieee_address": m.get("ieee_address", "")})

    dev_by_ieee = {
        dev.get("ieee_address"): dev.get("friendly_name")
        for dev in DEVICES
        if dev.get("ieee_address")
    }

    for dev_grupo in miembros:
        ieee = dev_grupo.get("ieee_address")
        if ieee in dev_by_ieee:
            dev_grupo["friendly_name"] = dev_by_ieee[ieee]

    return miembros


def _publicar_a_topic(topic, payload, qos=QoS_TOPIC_SET):
    if not _ensure_connected(timeout=3.0):
        return False

    with _mqtt_lock:
        info = client.publish(topic, json.dumps(payload), qos=qos)
        return info.rc == mqtt.MQTT_ERR_SUCCESS


def enviar_mensaje(device="", pyl={"state": ""}):
    global ZNAME

    target = device or ZNAME
    if not target:
        return False

    ZNAME = target
    topic_set = f"zigbee2mqtt/{target}/set"
    return _publicar_a_topic(topic_set, pyl, qos=QoS_TOPIC_SET)


def consultar_status_device(device="", timeout=5):
    global ZNAME, estado

    target = device or ZNAME
    if not target:
        return {}

    ZNAME = target
    topic_base = f"zigbee2mqtt/{target}"
    topic_get = f"zigbee2mqtt/{target}/get"

    if not _ensure_connected(timeout=3.0):
        return {}

    ev = threading.Event()
    entry = {"event": ev, "payload": None}

    with _pending_lock:
        _pending_responses[topic_base] = entry

    try:
        with _mqtt_lock:
            _subscribe_locked(topic_base, QoS_TOPIC_BASE)

        if not _publicar_a_topic(topic_get, {"state": ""}, qos=QoS_TOPIC_GET):
            return {}

        ev.wait(timeout=timeout)
        result = entry["payload"] if isinstance(entry["payload"], dict) else {}
        estado = result
        return result
    finally:
        with _pending_lock:
            _pending_responses.pop(topic_base, None)


def consultar_estado_grupo(gname="", timeout_dev=3):
    """Un grupo no tiene reporte de estado; consulta a cada miembro."""
    global ZNAME

    actualizar_devices_y_grupos()
    miembros = get_miembros_de_grupo(gname)

    if verbose:
        print("--- (consultar_estado_grupo) miembros:")
        print(json.dumps(miembros, indent=2))

    for miembro in miembros:
        nombre = miembro.get("friendly_name")
        if not nombre:
            continue

        ZNAME = nombre
        status = consultar_status_device(device=nombre, timeout=timeout_dev)
        raw_state = status.get("state", "")
        miembro["state"] = raw_state.lower() if isinstance(raw_state, str) else ""

    if miembros and all(m.get("state") == "off" for m in miembros):
        return "off"

    if any(m.get("state") == "on" for m in miembros):
        return "on"

    return ""


def _init():
    _ensure_connected(timeout=3.0)
    actualizar_devices_y_grupos(timeout=2.0)


_init()
