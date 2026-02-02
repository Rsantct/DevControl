#!/usr/bin/env python3

import  paho.mqtt.client as mqtt
import  json
import  time
from    fmt import Fmt

MQTT_HOST = "localhost"
MQTT_PORT = 1883

QoS_TOPIC_BASE  = 0
QoS_TOPIC_SET   = 1
QoS_TOPIC_GET   = 0
QoS_TOPIC_INFO  = 0


# Topics genéricos del bridge ZIGBEE2MQTT
# Todo el diccionario de configuración
TOPIC_INFO    = "zigbee2mqtt/bridge/info"
# Devices
TOPIC_DEVICES = "zigbee2mqtt/bridge/devices"
DEVICES       = {}
# Grupos
TOPIC_GROUPS  = "zigbee2mqtt/bridge/groups"
GRUPOS        = {}

client          = mqtt.Client()
ZNAME           = ''
verbose         = False
estado          = {}


def clamp(n, minn=0, maxn=100):
    return max(minn, min(n, maxn))


def prepare_topics(zname=''):

    global flag_conectado, flag_subscribed
    global TOPIC_BASE, TOPIC_GET, TOPIC_SET, TOPIC_INFO

    flag_conectado  = False
    flag_subscribed = False

    if not zname:
        zname = ZNAME

    TOPIC_BASE  = f'zigbee2mqtt/{zname}'
    TOPIC_SET   = f'zigbee2mqtt/{zname}/set'
    TOPIC_GET   = f'zigbee2mqtt/{zname}/get'


def get_miembros_de_grupo(gname=''):

    actualizar_devices_y_grupos()

    miembros = []

    for grupo in GRUPOS:
        if grupo.get('friendly_name', '') == gname:
            for m in grupo.get('members', []):
                miembros.append( {'ieee_address': m.get('ieee_address', '')} )

    # buscambos friendly_name de cada device del grupo
    for dev_grupo in miembros:
        for dev_global in DEVICES:
            if dev_global.get('ieee_address') == dev_grupo.get('ieee_address'):
                dev_grupo['friendly_name'] = dev_global.get('friendly_name')
                break

    return miembros


def consultar_estado_grupo(gname='', timeout_dev=3):
    """ Un grupo no tiene reporte de estado, hay que consultar a cada miembro
        resultado:
            off     si todos están en off
            on      si alguno está en on
    """

    global ZNAME

    actualizar_devices_y_grupos()

    miembros = get_miembros_de_grupo(gname)

    for miembro in miembros:

        ZNAME = miembro.get('friendly_name')

        prepare_topics()

        if broker_mqtt_conectar():
            status = consultar_status_device(timeout=timeout_dev)
            estado = status.get('state', '')
            miembro['state'] = estado
            broker_mqtt_desconectar()
        else:
            print(f'{Fmt.RED}(consultar_estado_grupo) NO CONECTA para {ZNAME}{Fmt.END}')

    if verbose:
        print('--- (consultar_estado_grupo) miembros:')
        print( json.dumps(miembros, indent=2) )


    if all(miembro.get('state') == 'off' for miembro in miembros):
        return 'off'

    elif any(miembro.get('state') == 'on' for miembro in miembros):
        return 'on'

    else:
        return ''


def consultar_status_device(device='', timeout=3):

    global ZNAME, estado

    estado = {}

    if device:
        ZNAME = device

    if not ZNAME:
        return estado

    prepare_topics()

    if not broker_mqtt_conectar():
        return estado

    _publicar('get', {'state': ''})

    # Esperamos a que el driver responda por Zigbee
    start_time = time.time()
    while not estado and (time.time() - start_time) < timeout:
        time.sleep(0.1)

    return estado


def enviar_mensaje( device='', pyl={'state':''} ):

    global ZNAME

    if device:
        ZNAME = device

    if not ZNAME:
        return False

    prepare_topics()

    if not broker_mqtt_conectar():
        return estado

    if _publicar('set', pyl):
        return True

    else:
        return False


def _publicar( modo='set', payload={'state':''} ):
    """ devuelve True si client.publish se ha ejecutado en el servidor,
        en caso contrario devuelve False
    """

    if modo == 'set':
        topic = TOPIC_SET
    elif modo == 'get':
        topic = TOPIC_GET

    ans = client.publish(topic, json.dumps(payload))

    return ans.rc == mqtt.MQTT_ERR_SUCCESS


def on_connect(client, userdata, flags, rc):
    """ handler para en momento de la conexión con el broker MQTT,
        nos subscribimos a mensajes relativos a nuestro TOPIC
    """

    global flag_conectado

    if rc == 0:

        # Nos suscribimos para en adelante recibir respuestas '/get'
        # [( "TOPIC_1", QoS ), ( "TOPIC_2", QoS ), ....]
        #
        #   QoS:
        #   0 (At most once):   El mensaje se envía una vez y no se confirma.
        #                       Es el más rápido y ligero suele usarse en redes locales estables.
        #   1 (At least once):  Asegura que el mensaje llegue, aunque pueda repetirse.
        #   2 (Exactly once):   Garantiza que llegue exactamente una vez (más lento,
        #                       requiere más "papeleo" entre cliente y broker).
        client.subscribe( [ (TOPIC_BASE,  QoS_TOPIC_BASE),
                            (TOPIC_INFO,  QoS_TOPIC_INFO)
                          ]
                        )

        flag_conectado = True

        if verbose:
            print(f"✅ Conectado al broker MQTT, topic base: {Fmt.BLUE}{Fmt.BOLD}{TOPIC_BASE}{Fmt.END}")

        return True

    else:
        print(f"❌ Error de conexión con el broquer MQTT: {rc}")
        return False


def on_subscribe(client, userdata, mid, granted_qos):
    """ actualizda la global <flag_subscribed>
    """
    global flag_subscribed
    flag_subscribed = True
    if verbose:
        print('✅ on_subscribe: flag_subscribed --> True')


def on_message(client, userdata, msg):
    """ handler ejecutado cuando el client recibe
        mensajes en sus subscripciones en el broker MQTT.

        --> actualiza los dict <estado>
    """
    global estado, zigbbee_info

    # Si el mensaje es el estado del dispositivo
    if msg.topic == TOPIC_BASE:

        msg = msg.payload.decode().lower()

        if verbose:
            print('TOPIC_BASE mensaje:', msg)

        try:
            estado = json.loads(msg)

        except Exception as e:
            print(f"Error leyendo TOPIC_BASE: {e}")

    # Si el mensaje es la información de Zigbee2MQTT
    elif msg.topic == TOPIC_INFO:

        msg = msg.payload.decode().lower()

        try:
            zigbbee_info = json.loads(msg)
            if verbose:
                print('TOPIC_INFO mensaje:', zigbbee_info.keys())

        except Exception as e:
            print(f"Error leyendo TOPIC_INFO: {e}")

    else:
        print(f'RECIBIDO msg de TOPIC-DESCONOCIDO: {msg}')


def broker_mqtt_desconectar():

    global flag_conectado

    try:
        client.loop_stop()
        client.disconnect()
    except:
        print('(broker_mqtt_desconectar) ERROR')

    flag_conectado = False


def broker_mqtt_conectar(timeout=3):

    # handlers para eventos asíncronos en el cliente
    client.on_connect   = on_connect
    client.on_subscribe = on_subscribe
    client.on_message   = on_message

    cc = client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    if cc == 0:

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if flag_subscribed:
                break
            time.sleep(0.1)

        # el OK es leyendo el flag_subscribed
        if flag_subscribed:
            return True

        else:
            return False

    else:
        print(f'(broker_mqtt_conectar) ERROR código {cc} conectando con el server MQTT {address}')
        return False


def actualizar_devices_y_grupos():

    def on_connect(client, userdata, flags, rc):
        client.subscribe(TOPIC_DEVICES)
        client.subscribe(TOPIC_GROUPS)

    def on_message(client, userdata, msg):

        global GRUPOS
        global DEVICES

        if msg.topic == TOPIC_DEVICES:
            DEVICES = json.loads(msg.payload.decode())
            if verbose:
                print(f'--- Recibidos DEVICES:')
                print( json.dumps(DEVICES, indent=2) )
                print('--- ')

        elif msg.topic == TOPIC_GROUPS:
            GRUPOS = json.loads(msg.payload.decode())
            if verbose:
                print(f'--- Recibidos GRUPOS:')
                print( json.dumps(GRUPOS, indent=2) )
                print('--- ')

        if DEVICES and GRUPOS:
            tmp_cli.disconnect()


    tmp_cli = mqtt.Client()
    tmp_cli.on_connect = on_connect
    tmp_cli.on_message = on_message

    tmp_cli.connect(MQTT_HOST, MQTT_PORT, 60)

    # loop_forever se detendrá al completar DEVICES y GRUPOS en on_message()
    tmp_cli.loop_forever()
    del tmp_cli


if __name__ == "__main__":

    # Lee desde command line <ZNAME> y <verbose>,
    # el resto de opciones se analizan en main()
    for opc in sys.argv[1:]:

        if '-dev=' in opc:
            ZNAME = opc.split('=')[-1]
            if ZNAME.startswith('"') and ZNAME.endswith('"'):
                ZNAME = ZNAME[1:-1]
            elif ZNAME.startswith("'") and ZNAME.endswith("'"):
                ZNAME = ZNAME[1:-1]

        elif opc == '-v':
            verbose = True

        elif opc == '-h' or opc == '--help':
            print(__doc__)
            sys.exit()

    resultado = do_command_line()

    if type(resultado) == str:
        print( resultado )
    else:
        print( json.dumps(resultado) )

