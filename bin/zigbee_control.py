#!/usr/bin/env python3
"""
    Gestión de dispositivo Zigbee

    Uso:    control_zigbee.py  [-v] -d=ZIGBEE_ID  ..opciones..

        -v                  respuesta verbose

        estado
        demo

        power_on=on|off     configural el comportamiento al recibir alimentación


        blink [NN]          parpadea NN veces (1 por defecto)

        on  [N]             brillo 0..100
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

verbose         = False
estado          = {}
DEVICE          = ''
client          = mqtt.Client()
flag_conectado  = False
flag_subscribed = False

# OjO necesita configuration.yaml en Zigbee2MQTT
#
#   availability: true
#   advanced:
#       # Opcional el driver se marcará 'offline' si no responde en 60 seg.
#       availability_timeout: 60
#
# posibles valores "online", "offline" o "unknown"
disponibilidad = {'state': 'unknown', 'cuando': ''}


def init_topics():
    global TOPIC, TOPIC_GET, TOPIC_SET, TOPIC_AVAIL, TOPIC_INFO
    TOPIC       = f'zigbee2mqtt/{DEVICE}'
    TOPIC_SET   = f'zigbee2mqtt/{DEVICE}/set'
    TOPIC_GET   = f'zigbee2mqtt/{DEVICE}/get'
    TOPIC_AVAIL = f'zigbee2mqtt/{DEVICE}/availability'
    # Este topic proporciona todo el diccionario de configuración
    # del bridge ZIGBEE2MQTT (es muy extenso)
    TOPIC_INFO  = "zigbee2mqtt/bridge/info"


def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def clamp(n, minn=0, maxn=100):
    return max(minn, min(n, maxn))


def consultar_estado():
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
        timeout = 5
        start_time = time.time()
        while not estado and (time.time() - start_time) < timeout:
            time.sleep(0.1)

    if estado:
        estado['observaciones'] = 'linkquality <20 puede fallar, 50~100 correcto, >100 excelente'

    return estado


def enviar_comando(payload):

    if disponibilidad["state"] == 'online':
        ans = client.publish(TOPIC_SET, json.dumps(payload))
        return ans.rc == mqtt.MQTT_ERR_SUCCESS

    else:
        return False


def set_luz(modo, brillo=100, on_time=None, veces=1):
    """
    modo:       on | off | blink

    brillo:     0 a 100

    on_time:    Cuenta atrás en segundos para apagarse por su cuenta (temporizador interno del device)
                (no es compatible con brillo)

    veces:      para blink
    """

    def do_blink():
        for _ in range(veces):
            cc = enviar_comando( {'effect': 'blink'} )
            time.sleep(3)

    modo = modo.lower()

    # brillo debe ser 0...254
    brillo = int(brillo / 100 * 254)

    # on_time debe ser entero y lo limitamos a 24h:
    try:
        on_time = clamp( int(on_time), 1, 24*60*60)
    except:
        pass

    if modo == 'off':
        cmd = {'state': 'off'}

    elif modo == 'on':
        if on_time:
            cmd = {'state': 'on', 'on_time': on_time}
        else:
            cmd = {'state': 'on', 'brightness': brillo}

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
    temporizador = None
    blink        = False
    veces        = 1

    for opc in sys.argv[1:]:

        if '-d=' in opc or opc == '-v':
            continue

        if 'sta' in opc:
            return consultar_estado()

        if 'power' in opc:
            modo = opc.split('=')[-1]
            return set_power_on_behavior(modo)


        if opc == 'demo':
            return do_demo()

        if opc == 'on':
            encender = True

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
                brillo = clamp( int(opc) )
            except:
                pass


    if apagar:
        return set_luz("OFF")

    elif encender:
        return set_luz("ON", brillo=brillo, on_time=temporizador)

    elif blink:
        return set_luz('blink', veces=veces)

    else:
        return False


def do_demo():

    try:
        print(f"Probando device: {DEVICE} ...")

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
        client.subscribe( [ (TOPIC,       0),
                            (TOPIC_AVAIL, 0),
                            (TOPIC_INFO,  0)
                          ]
                        )

        flag_conectado = True

        if verbose:
            print("✅ Conectado al broker MQTT")

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
    elif msg.topic == TOPIC:

        msg = msg.payload.decode().lower()

        if verbose:
            print('TOPIC mensaje:', msg)

        try:
            estado = json.loads(msg)

            if estado.get('linkquality', 0):
                disponibilidad['state']  = 'online'
                disponibilidad['cuando'] = get_timestamp()

        except Exception as e:
            print(f"Error leyendo TOPIC: {e}")

    # Si el mensaje es la información de Zigbee2MQTT
    elif msg.topic == TOPIC_INFO:

        msg = msg.payload.decode().lower()

        try:
            zigbbee_info = json.loads(msg)
            if verbose:
                print('TOPIC_INFO mensaje:', zigbbee_info.keys())

        except Exception as e:
            print(f"Error leyendo TOPIC: {e}")

    else:
        print(f'RECIBIDO msg: {msg}')


def conectar_con_broker_mqtt(address='localhost'):

    # handlers para eventos asíncronos en el cliente
    client.on_connect   = on_connect
    client.on_subscribe = on_subscribe
    client.on_message   = on_message

    cc = client.connect(address, 1883, 60)
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


if __name__ == "__main__":

    # Lee desde command line <DEVICE> y <verbose>,
    # el resto de opciones se analizan en main()
    for opc in sys.argv[1:]:

        if '-d=' in opc:
            DEVICE = opc.split('=')[-1]
            if DEVICE.startswith('"') and DEVICE.endswith('"'):
                DEVICE = DEVICE[1:-1]
            elif DEVICE.startswith("'") and DEVICE.endswith("'"):
                DEVICE = DEVICE[1:-1]

        elif opc == '-v':
            verbose = True

        elif opc == '-h' or opc == '--help':
            print(__doc__)
            sys.exit()

    init_topics()

    if not conectar_con_broker_mqtt():
        print(False)
        sys.exit()

    resultado = do_main()

    if type(resultado) == str:
        print( resultado )
    else:
        print( json.dumps(resultado) )

    client.loop_stop()
    client.disconnect()
