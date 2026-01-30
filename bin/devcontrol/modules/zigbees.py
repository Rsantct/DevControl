#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to manage zigbee devices
"""

import os
import sys
UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/bin')
sys.path.append(f'{UHOME}/bin/devcontrol/modules')

import subprocess as sp
import miscel as mc

import zigbee_control as zc


def init_zc(device):
    zc.DEVICE = device
    zc.init()
    return zc.conectar_con_broker_mqtt()


def do_toggle(device):

    result = 'none'

    curr_status = zc.consultar_estado()
    curr_state = curr_status.get('state')

    if curr_state == 'on':
        if zc.set_luz('off'):
            result = 'off'

    elif curr_state == 'off':
        if zc.set_luz('on'):
            result = 'on'

    return result


def manage_zigbee(args):
    """
        {'target': 'element_name', 'command': 'a command phrase' }
    """

    result = ''

    if 'target' not in args:
        return result

    config = mc.read_config()

    elem_name = args['target']
    device    = config.get('zigbees', {}).get(elem_name, '')
    tmp       = args.get('command', '').split(' ')
    command   = tmp[0]
    args      = tmp[1:]

    if not init_zc(device):
        return f'error with {device}'

    if command == 'toggle':
        result = do_toggle(device)

    elif command == 'on':

        try:
            brillo = int(args[0])
        except:
            brillo = None

        if zc.set_luz('on', brillo):
            result = 'on'

    elif command == 'off':
        if zc.set_luz('off'):
            result = 'off'

    elif 'sta' in command:
        return zc.consultar_estado().get('state', 'unknown')

    zc.desconectar_del_broker_mqtt()

    return result
