import json
import threading
import paho.mqtt.client as mqtt

SENSOR_NAMES = {
    "temperature",
    "humidity",
    "pressure",
    "illuminance",
    "occupancy",
    "contact",
    "water_leak",
    "smoke",
    "gas",
    "carbon_monoxide",
    "soil_moisture",
    "battery",
}

POWER_SENSOR_NAMES = {"power", "voltage", "current", "energy"}


def _aplanar_exposes(exposes: list[dict]) -> list[dict]:
    """Devuelve una lista plana con exposes principales y features anidadas."""
    plano = []

    def recorrer(items):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            plano.append(item)
            if isinstance(item.get("features"), list):
                recorrer(item["features"])

    recorrer(exposes)
    return plano


def clasificar_dispositivo(dev: dict) -> str:
    """Devuelve 'bombilla', 'enchufe', 'sensor' o 'otro/desconocido'."""
    definition = dev.get("definition") or {}
    items = _aplanar_exposes(definition.get("exposes", []))

    tipos = {item.get("type") for item in items if item.get("type")}
    nombres = {
        (item.get("name") or item.get("property"))
        for item in items
        if (item.get("name") or item.get("property"))
    }

    if "light" in tipos or nombres.intersection({"brightness", "color_temp", "color_xy", "color_hs"}):
        return "bombilla"

    tiene_switch = "switch" in tipos or (
        "state" in nombres
        and not nombres.intersection({"action", "click"})
        and bool(definition.get("description", "").strip())
    )
    if tiene_switch:
        return "enchufe"

    if nombres.intersection(SENSOR_NAMES) or nombres.intersection(POWER_SENSOR_NAMES):
        return "sensor"

    return "otro/desconocido"


def construir_mapa_dispositivos(devices: list[dict], incluir_coordinador: bool = False) -> dict[str, str]:
    """Construye {friendly_name: tipo} a partir de la lista de zigbee2mqtt/bridge/devices."""
    mapa: dict[str, str] = {}

    for dev in devices or []:
        if not isinstance(dev, dict):
            continue
        if not incluir_coordinador and dev.get("type") == "Coordinator":
            continue

        friendly_name = dev.get("friendly_name")
        if friendly_name:
            mapa[friendly_name] = clasificar_dispositivo(dev)

    return mapa


def obtener_rol_dispositivos(
    broker: str = "127.0.0.1",
    port: int = 1883,
    base_topic: str = "zigbee2mqtt",
    timeout: float = 5.0,
    incluir_coordinador: bool = False,
) -> dict[str, str]:
    """ Consulta zigbee2mqtt/bridge/devices por MQTT y devuelve devices por rol
            {friendly_name: tipo}

        Ejemplo:
         {'estudio_billy_1': 'bombilla',
          'Lampara_pie_b2': 'bombilla',
          'Lampara_pie_b1': 'bombilla',
          'salon_libreria_izq': 'bombilla',
          'salon_libreria_der': 'bombilla',
          'sonoff_1': 'enchufe'}
    """

    resultado: dict[str, str] = {}
    evento_recibido = threading.Event()
    error_conexion: list[str] = []

    def _on_connect_v2(client, userdata, flags, reason_code, properties=None):
        rc_val = getattr(reason_code, "value", reason_code)
        if rc_val == 0:
            client.subscribe(f"{base_topic}/bridge/devices", qos=1)
        else:
            error_conexion.append(f"Error de conexión MQTT (código {rc_val})")
            evento_recibido.set()

    def _on_connect_v1(client, userdata, flags, rc):
        _on_connect_v2(client, userdata, flags, rc, properties=None)

    def on_message(client, userdata, msg):
        nonlocal resultado
        try:
            devices = json.loads(msg.payload.decode("utf-8"))
            resultado = construir_mapa_dispositivos(devices, incluir_coordinador=incluir_coordinador)
        except Exception as exc:
            error_conexion.append(f"Error procesando payload MQTT: {exc}")
        finally:
            evento_recibido.set()
            client.disconnect()

    if hasattr(mqtt, "CallbackAPIVersion"):
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = _on_connect_v2
    else:
        client = mqtt.Client()
        client.on_connect = _on_connect_v1

    client.on_message = on_message

    client.connect(broker, port, keepalive=30)
    client.loop_start()

    try:
        if not evento_recibido.wait(timeout=timeout):
            raise TimeoutError(
                f"Tiempo agotado ({timeout}s) esperando {base_topic}/bridge/devices en {broker}:{port}"
            )
        if error_conexion:
            raise RuntimeError(error_conexion[0])
    finally:
        client.loop_stop()
        client.disconnect()

    return resultado
