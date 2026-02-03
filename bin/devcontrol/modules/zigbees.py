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
sys.path.append(f'{UHOME}/bin/devcontrol/modules')

import json
import miscel as mc
from   fmt import Fmt
import zigbee as z


ZTCOLORMIN = 250
ZTCOLORMAX = 454


def clamp(n, minn=0, maxn=10):
    return max(minn, min(n, maxn))


def is_group(zid):
    for grupo in z.GRUPOS:
        if zid == grupo.get('friendly_name'):
            return True
    return False


def get_group_scenes(group):

    scenes = []

    group_found = next((g for g in z.GRUPOS if g['friendly_name'] == group), None)

    if group_found:
        scenes = group_found.get('scenes', [])

    return scenes


def do_command_device(device, command='state', brightness=100):
    """ toggle not used from the web interface
    """

    result = ''

    if 'sta' in command:
        result = z.consultar_status_device(device).get('state', 'unknown')

    elif command == 'on':
        pyl = {'brightness': brightness}
        z.enviar_mensaje(device, pyl)
        result = 'on'

    elif command == 'off':
        pyl = {'state': 'off'}
        z.enviar_mensaje(device, pyl)
        result = 'off'

    elif command == 'toggle':

        curr = z.consultar_status_device(device).get('state')

        if curr == 'on':
            pyl = {'state': 'off'}
            z.enviar_mensaje(device, pyl)
            result = 'off'

        elif curr == 'off':
            pyl = {'brightness': brightness}
            z.enviar_mensaje(device, pyl)
            result = 'on'

    return result


def do_command_group(group, command='state', brightness=100):
    """ toggle not here, it falls under the web interface
    """

    scenes = get_group_scenes(group)

    result = ''

    if 'sta' in command:
        result = z.consultar_estado_grupo(group)

    else:

        if command == 'on':

            if  any( [s for s in scenes if s.get('id')==1] ):

                z.enviar_mensaje(group, {'scene_recall': 1})
                result = 'on'
                print(f'{Fmt.BLUE}recall scene 1 for: {group}{Fmt.END}')

            else:
                z.enviar_mensaje(group, {'brightness': brightness})
                result = 'on'

        elif command == 'off':

            if  any( [s for s in scenes if s.get('id')==0] ):

                z.enviar_mensaje(group, {'scene_recall': 0})
                result = 'off'
                print(f'{Fmt.BLUE}recall scene 0 for: {group}{Fmt.END}')

            elif command == 'off':
                z.enviar_mensaje(group, {'state': 'off'})
                result = 'off'

    return result


def manage_zigbee(args):
    """
        {'target': element_name, 'command': a command phrase }

        element_name as per entries under config["zigbees"]

        result: an string (on, off, ... etc)
    """

    if 'target' not in args:
        return result

    config = mc.read_config()

    elem_name = args['target']
    zname     = config.get('zigbees', {}).get(elem_name, '')
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



    # Group
    if is_group(zname):
        result = do_command_group(zname, command, brightness)

    # Individual device
    else:
        result = do_command_device(zname, command, brightness)

    return result


z.actualizar_devices_y_grupos()
