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
import miscel   as mc
import zigbee   as z


BRIGHTNESSMAX = 254
ZTCOLORMIN    = 250
ZTCOLORMAX    = 454


def clamp(n, minn=0, maxn=10):
    return max(minn, min(n, maxn))


def get_scene_on_off(zlabel):

    scenes      = mc.CONFIG.get('devices', {}).get('zigbees', {})[zlabel].get("scenes", [])
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


def do_command(zlabel, zname, command='state', brightness=0):
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
                z.enviar_mensaje(zname, {'brightness': brightness})
                print(f'{Fmt.BLUE}{zname}: brightness {brightness}/{BRIGHTNESSMAX}{Fmt.END}')

            else:

                if  scene_on:
                    z.enviar_mensaje(zname, {'scene_recall': scene_on['id']})
                    print(f'{Fmt.BLUE}{zname}: recall scene <on>{Fmt.END}')

                else:
                    z.enviar_mensaje(zname, {'brightness': int(BRIGHTNESSMAX / 2)})
                    print(f'{Fmt.BLUE}{zname}: brightness medium because no specied and scene <on> not found{Fmt.END}')

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

    if 'target' not in args:
        return result

    zlabel    = args['target']

    # zname is the actual name under zigbee2mqtt
    tmp       = mc.CONFIG.get('devices', {}).get('zigbees', {}).get(zlabel, {})
    zname     = tmp.get('friendly_name')
    if not zname:
        return 'target not found in Zigbee2MQTT'

    tmp       = args.get('command', '').split(' ')
    command   = tmp[0] if tmp[0] else 'state'
    args      = tmp[1:]

    if args:
        # Currently only brigthness as arg values
        brightness = args[0]
        # brightness must come in 1...10
        try:
            brightness = clamp( int(args[0]), 1, 10)
        except:
            brightness = 0

    # zigbee2mqtt brightness must be in 0...254
    try:
        brightness = int(brightness / 10 * 254)
    except:
        brightness = 0

    # STILL NOT IN USE
    # color_temp comes in (1...10) and must be in ZTCOLORMIN...ZTCOLORMAX
    try:
        color_temp = int(color_temp / 10 * (ZTCOLORMAX - ZTCOLORMIN) + ZTCOLORMIN)
    except Exception as e:
        color_temp = int((ZTCOLORMIN + ZTCOLORMAX) / 2)

    # Do process
    result = do_command(zlabel, zname, command, brightness)

    return result
