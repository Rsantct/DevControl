#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to manage zigbee devices
"""

import os
import sys
UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/bin/zigbee_mod')
sys.path.append(f'{UHOME}/bin/devcontrol/modules/devices_mod')

import json
from   fmt      import Fmt
import common   as cm
import zigbee   as z


BRIGHTNESSMAX = 254
ZTCOLORMIN    = 250
ZTCOLORMAX    = 454


def color_temp_conversion(uvalue):
    """ color_temp user values comes in (1...10)
        it mus converted to the range ZTCOLORMIN...ZTCOLORMAX
    """
    try:
        return int(uvalue / 10 * (ZTCOLORMAX - ZTCOLORMIN) + ZTCOLORMIN)
    except Exception as e:
        return int((ZTCOLORMIN + ZTCOLORMAX) / 2)


def arg_to_brightness(arg):

    # User brightness values must come in 1...10
    try:
        brightness = cm.clamp( int(arg), 1, 10)
    except:
        brightness = 0

    # zigbee2mqtt brightness must be in 0...254
    try:
        brightness = int(brightness / 10 * 254)
    except:
        brightness = 0

    return brightness


def arg_to_timer(arg):
    """ User timer values comes as a negative integer or float string format,
        in minutes by default.

        arg         timer
        ---         -----
        -25s        25 sec
        -10         10 min
        -1.5m       90 sec
        -0.5h       30 min
    """

    M = 60

    if arg[-1].lower() == 's':
        M = 1

    elif arg[-1].isdigit() or arg[-1].lower() == 'm':
        M = 60

    elif arg[-1].lower() == 'h':
        M = 3600

    try:
        # keep only numeric chars and decimal dot
        arg = "".join(filter(lambda x: x.isdigit() or x == ".", arg))
        return int( abs(round(float(arg), 1) * M) )

    except Exception as e:
        print(f'{Fmt.RED}(zigbees.arg_to_timer) ERROR: {e}{Fmt.END}')
        return 0


def get_scene_on_off(zlabel):

    scenes      = cm.CONFIG.get('devices', {}).get('zigbees', {})[zlabel].get("scenes", [])
    scenes_off = [s for s in scenes if s.get('name')=='off']
    scenes_on  = [s for s in scenes if s.get('name')=='on' ]

    # We use the 1st one if any
    if scenes_off:
        scene_off = scenes_off[0]
    else:
        scene_off = {}

    if scenes_on:
        scene_on = scenes_on[0]
    else:
        scene_on = {}

    return scene_on, scene_off


def do_command(zlabel, zname, command='state', brightness=0, timer=0):
    """ toggle not here, it falls under the web interface
    """

    result = ''

    # status
    if 'sta' in command:

        if z.is_group(zname):
            result = z.consultar_estado_grupo(zname)
        else:
            result = z.consultar_status_device(zname).get('state', 'unknown')

    # on / off
    else:

        scene_on, scene_off = get_scene_on_off(zlabel)

        if command == 'on':

            if brightness:
                print(f'{Fmt.BLUE}{zname}: brightness {brightness}/{BRIGHTNESSMAX}{Fmt.END}')
                z.enviar_mensaje(zname, {'brightness': brightness})

            else:

                if  scene_on:
                    z.enviar_mensaje(zname, {'scene_recall': scene_on['id']})
                    print(f'{Fmt.BLUE}{zname}: recall scene <on>{Fmt.END}')

                else:
                    z.enviar_mensaje(zname, {'brightness': int(BRIGHTNESSMAX / 2)})
                    print(f'{Fmt.BLUE}{zname}: brightness medium because no specied and scene <on> not found{Fmt.END}')

            if timer:
                cm.sleep(.5)
                print(f'{Fmt.BLUE}{zname}: timer {timer} seconds.{Fmt.END}')
                z.enviar_mensaje(zname, {'state': 'on', 'on_time': timer})

            result = 'on'

        elif command == 'off':

            if scene_off:

                z.enviar_mensaje(zname, {'scene_recall': scene_off['id']})
                print(f'{Fmt.BLUE}{zname}: recall scene <off>{Fmt.END}')

            elif command == 'off':
                z.enviar_mensaje(zname, {'state': 'off'})

            result = 'off'

    return result


def manage_zigbee(args):
    """
        {'target': zlabel, 'command': a command phrase }

        zlabel must match a label entrie under config/devives/zigbees

        result: an string (on, off, '', ... or whatever descriptor)
    """

    result = ''

    # The target
    if 'target' not in args:
        return result

    zlabel    = args['target']

    # zname is the actual name under zigbee2mqtt
    tmp       = cm.CONFIG.get('devices', {}).get('zigbees', {}).get(zlabel, {})
    zname     = tmp.get('friendly_name')
    if not zname:
        return 'target not found in Zigbee2MQTT'

    # Reading the command and args
    tmp       = args.get('command', '').split()
    command   = tmp[0] if tmp[0] else 'state'
    args      = tmp[1:]

    brightness  = 0
    timer       = 0

    for arg in args:

        if cm.is_integer(arg):

            if int(arg) > 0:
                brightness = arg_to_brightness(arg)

            elif int(arg) < 0:
                timer = arg_to_timer(arg)

        elif arg[0] == '-':
            timer = arg_to_timer(arg)

    # Do process
    result = do_command(zlabel, zname, command, brightness, timer)

    return result
