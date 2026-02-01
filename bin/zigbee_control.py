#!/usr/bin/env python3
"""
    Gestión de dispositivo Zigbee

    Uso:    control_zigbee.py  [-v] -dev=ZIGBEE_DEV  ...comando...

        -v                  respuesta verbose

        estado
        demo

        power_on=on|off     configural el comportamiento al recibir alimentación


        blink [N]           parpadea N veces (1 por defecto)

        on  [N]             brillo 0..100
        on  tc=N            temperatura de color 0..100 (fria...cálida)
        on  timer=N         inicia un temporizador de apagado en N segundos
        off

    Respuesta (stdout):     true, false o un JSON si pedimos el estado

        (En modo verbose la respuesta final siempre aparecerá en la última línea)
"""
import  sys
import  paho.mqtt.client as mqtt
import  json
import  time
from    datetime import datetime

ZTCOLORMIN = 250
ZTCOLORMAX = 454

MQTT_HOST = "localhost"
MQTT_PORT = 1883

QoS_TOPIC_BASE  = 0
QoS_TOPIC_SET   = 1
QoS_TOPIC_GET   = 0
QoS_TOPIC_AVAIL = 0
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
disponibilidad = {'state': 'unknown', 'cuando': ''}
# OjO disponibilidad necesita configuration.yaml en Zigbee2MQTT
#
#   availability: true
#   advanced:
#       # Opcional el driver se marcará 'offline' si no responde en 60 seg.
#       availability_timeout: 60
#
# posibles valores "online", "offline" o "unknown"


class Fmt:
    """
    # Some nice ANSI formats for printouts formatting
    # CREDITS: https://github.com/adoxa/ansicon/blob/master/sequences.txt
    """

    BLACK           = '\033[30m'
    RED             = '\033[31m'
    GREEN           = '\033[32m'
    YELLOW          = '\033[33m'
    BLUE            = '\033[34m'
    MAGENTA         = '\033[35m'
    CYAN            = '\033[36m'
    WHITE           = '\033[37m'
    GRAY            = '\033[90m'

    BRIGHTBLACK     = '\033[90m'
    BRIGHTRED       = '\033[91m'
    BRIGHTGREEN     = '\033[92m'
    BRIGHTYELLOW    = '\033[93m'
    BRIGHTBLUE      = '\033[94m'
    BRIGHTMAGENTA   = '\033[95m'
    BRIGHTCYAN      = '\033[96m'
    BRIGHTWHITE     = '\033[97m'

    BOLD            = '\033[1m'
    UNDERLINE       = '\033[4m'
    BLINK           = '\033[5m'
    END             = '\033[0m'


def prepare_zname():

    global flag_conectado, flag_subscribed
    global TOPIC_BASE, TOPIC_GET, TOPIC_SET, TOPIC_AVAIL, TOPIC_INFO

    flag_conectado  = False
    flag_subscribed = False

    TOPIC_BASE  = f'zigbee2mqtt/{ZNAME}'
    TOPIC_SET   = f'zigbee2mqtt/{ZNAME}/set'
    TOPIC_GET   = f'zigbee2mqtt/{ZNAME}/get'
    TOPIC_AVAIL = f'zigbee2mqtt/{ZNAME}/availability'


def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def clamp(n, minn=0, maxn=100):
    return max(minn, min(n, maxn))


def get_miembros_de_grupo(gname=''):

    update_devices()

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


def consultar_estado_grupo(gname=''):
    """ Un grupo no tiene reporte de estado, hay que consultar a cada miembro
    """

    global ZNAME

    update_devices()

    miembros = get_miembros_de_grupo(gname)

    for miembro in miembros:

        ZNAME = miembro.get('friendly_name')

        prepare_zname()

        if conectar_con_broker_mqtt():
            estado = consultar_estado(timeout=2).get('state', '')
            miembro['state'] = estado
            desconectar_del_broker_mqtt()
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


def consultar_estado(timeout=5):
    """
    En Zigbee2MQTT, cuando activas availability: enabled: true, el servidor publica
    el estado en un topic específico y lo marca como "Retained" (retenido) en el broker MQTT.
    Esto significa que el broker guarda el último estado conocido y, en cuanto un script de Python
    se suscribe, el broker le envía el estado inmediatamente. No hace falta pedirlo.

    O sea, no funcinará que usemos los topics de availability
        TOPIC_REQ = "zigbee2mqtt/bridge/request/device/availability"
        TOPIC_RES = "zigbee2mqtt/bridge/response/device/availability"
    """

    global estado

    estado = {}

    if disponibilidad["state"] == 'online':

        client.publish(TOPIC_GET, json.dumps({'state': ''}))

        # Esperamos a que el driver responda por Zigbee
        start_time = time.time()
        while not estado and (time.time() - start_time) < timeout:
            time.sleep(0.1)

    else:
        if verbose:
            print(f'(consultar_estado) SIN disponibilidad')

    return estado


def enviar_comando(payload):

    if disponibilidad["state"] == 'online':
        ans = client.publish(TOPIC_SET, json.dumps(payload))
        return ans.rc == mqtt.MQTT_ERR_SUCCESS

    else:
        return False


def set_luz(modo, brillo=100, on_time=None, blink_veces=1, color_temp=80):
    """
    modo:           on | off | blink

    brillo:         0 ~ 100

    color_temp:     0 ~ 100 (fria ~ cálida)

    on_time:        Cuenta atrás en segundos para apagarse por su cuenta
                    (temporizador interno del device, no es compatible con brillo)

    blink_veces:    veces del parpadeo
    """

    def do_blink():
        for _ in range(blink_veces):
            cc = enviar_comando( {'effect': 'blink'} )
            time.sleep(3)

    modo = modo.lower()

    # brillo debe ser 0...254
    try:
        brillo = int(brillo / 100 * 254)
    except:
        brillo = 254

    # color_temp debe ser ZTCOLORMIN...ZTCOLORMAX
    try:
        color_temp = int(color_temp / 100 * (ZTCOLORMAX - ZTCOLORMIN) + ZTCOLORMIN)
    except Exception as e:
        color_temp = int((ZTCOLORMIN + ZTCOLORMAX) / 2)

    # on_time debe ser entero y lo limitamos a 24h:
    try:
        on_time = clamp( int(on_time), 1, 24*60*60)
    except:
        pass

    if modo == 'off':
        cmd = {'state': 'off'}

    elif modo == 'on':
        if on_time:
            cmd = { 'state': 'on', 'on_time': on_time }
        else:
            cmd = { 'state': 'on', 'brightness': brillo, 'color_temp': color_temp }

    elif modo == 'blink':
        do_blink()
        return True

    else:
        return False

    return enviar_comando( cmd )


def do_main():

    apagar       = False
    encender     = False
    brillo       = 100
    color_temp   = 50
    temporizador = None
    blink        = False
    veces        = 1

    for opc in sys.argv[1:]:

        if '-d=' in opc or opc == '-v':
            continue

        if opc.startswith('stat') or opc == 'estado':
            return consultar_estado()

        if 'power' in opc:
            modo = opc.split('=')[-1]
            return set_power_on_behavior(modo)


        if opc == 'demo':
            return do_demo()

        if opc == 'on':
            encender = True

        elif 'tc=' in opc or 'ct=' in opc:
            color_temp = opc.split('=')[-1]
            color_temp = clamp( int(color_temp), 0, 100 )

        elif 'temp' in opc or 'time' in opc:
            temporizador = opc.split('=')[-1]

        elif opc == 'off':
            apagar = True

        elif 'blink' in opc:
            blink = True

        elif opc.isdigit:
            try:
                if blink:
                    veces = clamp( int(opc), 1, 10)
                brillo = clamp( int(opc), 0, 100 )
            except:
                pass


    if apagar:
        return set_luz("OFF")

    elif encender:
        return set_luz("ON", brillo=brillo, color_temp=color_temp, on_time=temporizador)

    elif blink:
        return set_luz('blink', blink_veces=veces)

    else:
        return False


def do_demo():

    try:
        print(f"Probando device: {ZNAME} ...")

        set_luz("ON", 50)
        time.sleep(1)

        set_luz("ON", 10)
        time.sleep(1)

        set_luz("OFF")
        time.sleep(1)

        set_luz("blink")

        print("Prueba finalizada.")

    except KeyboardInterrupt:
        print("Script detenido por el usuario")


    return True


def set_power_on_behavior(modo):
    """ Aseguramos que después de un corte de luz 220V,
        las luces quedan apagadas o encendidas
    """
    if not modo in ('on', 'off'):
        print('modo debe ser: on | off')
        return False

    if enviar_comando( {"power_on_behavior": modo} ):
        return True
    else:
        return False


def on_connect(client, userdata, flags, rc):
    """ handler para en momento de la conexión con el broker MQTT,
        nos subscribimos a mensajes relativos a nuestro TOPIC
    """

    global flag_conectado

    if rc == 0:

        # Nos suscribimos para en adelante recibir respuestas '/get'
        # al topic principal y al de disponibilidad
        # [( "TOPIC_ESTADO", QoS ), ( "TOPIC_DISPONIBILIDAD", QoS )]
        #
        #   QoS:
        #   0 (At most once):   El mensaje se envía una vez y no se confirma.
        #                       Es el más rápido y ligero suele usarse en redes locales estables.
        #   1 (At least once):  Asegura que el mensaje llegue, aunque pueda repetirse.
        #   2 (Exactly once):   Garantiza que llegue exactamente una vez (más lento,
        #                       requiere más "papeleo" entre cliente y broker).
        client.subscribe( [ (TOPIC_BASE,  QoS_TOPIC_BASE),
                            (TOPIC_AVAIL, QoS_TOPIC_AVAIL),
                            (TOPIC_INFO,  QoS_TOPIC_INFO)
                          ]
                        )

        flag_conectado = True

        if verbose:
            print(f"✅ Conectado al broker MQTT, topic base: {Fmt.BLUE}{Fmt.BOLD}{TOPIC_BASE}{Fmt.END}")

    else:
        print(f"❌ Error de conexión con el broquer MQTT: {rc}")


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

        --> actualiza los dict <estado> y <disponibilidad>
    """
    global estado, disponibilidad, zigbbee_info

    # Si el mensaje viene del topic de disponibilidad
    if msg.topic == TOPIC_AVAIL:

        msg = msg.payload.decode().lower()

        if verbose:
            print('TOPIC_AVAIL mensaje:', msg)

        try:
            disponibilidad['state']  = json.loads(msg).get('state', 'unknown')
            disponibilidad['cuando'] = get_timestamp()

        except Exception as e:
            print(f'ERROR leyendo TOPIC_AVAIL: {e}')

    # Si el mensaje es el estado del dispositivo
    elif msg.topic == TOPIC_BASE:

        msg = msg.payload.decode().lower()

        if verbose:
            print('TOPIC_BASE mensaje:', msg)

        try:
            estado = json.loads(msg)

            if estado.get('linkquality', 0):
                disponibilidad['state']  = 'online'
                disponibilidad['cuando'] = get_timestamp()

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


def desconectar_del_broker_mqtt():

    global flag_conectado

    try:
        client.loop_stop()
        client.disconnect()
    except:
        print('ERROR desconectar_del_broquer_mqtt')

    flag_conectado = False


def conectar_con_broker_mqtt():

    # handlers para eventos asíncronos en el cliente
    client.on_connect   = on_connect
    client.on_subscribe = on_subscribe
    client.on_message   = on_message

    cc = client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    if cc == 0:

        timeout = 10
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if flag_subscribed:
                break
            time.sleep(0.1)

        # el OK lo daremos
        if flag_subscribed:
            return True

        else:
            return False

    else:
        print(f'ERROR código {cc} conectando con el server MQTT {address}')
        return False


def update_devices():

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

    prepare_zname()

    if not conectar_con_broker_mqtt():
        print(False)
        sys.exit()

    resultado = do_main()

    if type(resultado) == str:
        print( resultado )
    else:
        print( json.dumps(resultado) )

    desconectar_del_broker_mqtt()
