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


ZTCOLORMIN = 250
ZTCOLORMAX = 454


def clamp(n, minn=0, maxn=10):
    return max(minn, min(n, maxn))


def do_command(zname, command='state', brightness=100):
    """ toggle not here, it falls under the web interface
    """

    def get_zlabel(zname):
        for k, v in mc.CONFIG.get('devices', {}).get('zigbees', {}).items():
            if v.get('friendly_name', '') == zname:
                return k
        return ''

    zlabel = get_zlabel(zname)

    scenes = mc.CONFIG.get('devices', {}).get('zigbees', {})[zlabel].get("scenes", [])

    scenes_off = any( [s for s in scenes if s.get('name')=='off'] )
    scenes_on  = any( [s for s in scenes if s.get('name')=='on' ] )

    # We use the 1st one if any
    if scenes_off:
        scene_off = scenes_off[0]
    else:
        scene_off = {}
    if scenes_on:
        scene_on = scenes_on[0]
    else:
        scene_on = {}

    result = ''

    if 'sta' in command:

        if z.is_group(zname):
            result = z.consultar_estado_grupo(zname)
        else:
            result = z.consultar_status_device(zname).get('state', 'unknown')

    else:

        if command == 'on':

            if  scene_on:

                z.enviar_mensaje(zname, {'scene_recall': scene_on['id']})
                print(f'{Fmt.BLUE}recall scene `on` for: {zname}{Fmt.END}')

            else:
                z.enviar_mensaje(zname, {'brightness': brightness})

            result = 'on'

        elif command == 'off':

            if scene_off:

                z.enviar_mensaje(zname, {'scene_recall': scene_off['id']})
                print(f'{Fmt.BLUE}recall scene `off` for: {zname}{Fmt.END}')

            elif command == 'off':
                z.enviar_mensaje(zname, {'state': 'off'})

            result = 'off'

    return result


def manage_zigbee(args):
    """
        {'target': element_name, 'command': a command phrase }

        element_name as per entries under config devives zigbees

        result: an string (on, off, ... or whatever descriptor)
    """

    result = ''

    if 'target' not in args:
        return result

    target    = args['target']

    tmp       = mc.CONFIG.get('devices', {}).get('zigbees', {}).get(target, {})
    zname     = tmp.get('friendly_name')

    tmp       = args.get('command', '').split(' ')
    command   = tmp[0] if tmp[0] else 'state'
    args      = tmp[1:]

    if not zname:
        return 'target not found'

    try:
        brightness = clamp( int(args[0]), 1, 10)
    except:
        brightness = 10

    # brightness mut be in 0...254
    try:
        brightness = int(brightness / 10 * 254)
    except:
        brightness = 254

    # color_temp must be in ZTCOLORMIN...ZTCOLORMAX
    try:
        color_temp = int(color_temp / 100 * (ZTCOLORMAX - ZTCOLORMIN) + ZTCOLORMIN)
    except Exception as e:
        color_temp = int((ZTCOLORMIN + ZTCOLORMAX) / 2)


    result = do_command(zname, command, brightness)


    return result
