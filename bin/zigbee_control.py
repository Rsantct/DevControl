#!/usr/bin/env python3
"""
    Gestión de dispositivo Zigbee **EXPERIMETAL**

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
import  os
sys.path.append(f'{os.path.expanduser("~")}/bin/zigbee_mod')

import  json
import  time
from    datetime import datetime
import  zigbee as z
from    fmt import Fmt


def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def clamp(n, minn=0, maxn=100):
    return max(minn, min(n, maxn))


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
            publicar( 'set', {'effect': 'blink'} )
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
        pyl = {'state': 'off'}

    elif modo == 'on':
        if on_time:
            pyl = { 'state': 'on', 'on_time': on_time }
        else:
            pyl = { 'state': 'on', 'brightness': brillo, 'color_temp': color_temp }

    elif modo == 'blink':
        do_blink()
        return True

    else:
        return False

    return publicar( 'set', pyl )


def do_command_line():

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
            return z.consultar_status_device()

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

    if publicar( 'set', {"power_on_behavior": modo} ):
        return True
    else:
        return False


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

