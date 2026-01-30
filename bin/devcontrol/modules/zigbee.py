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
    zc.init_topics()
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
        this simply toggles or queries the status of a device
        then returns the response if any

        {'target': element_name, 'mode': toggle | state }
    """

    result = 'none'

    if 'target' not in args:
        return result

    config = mc.read_config()

    elem_name = args['target']
    device    = config.get('zigbees', {}).get(elem_name, '')
    todo      = args.get('mode', '')

    if not init_zc(device):
        return 'error initializing device'

    if todo == 'toggle':
        result = do_toggle(device)

    elif todo == 'on':
        if zc.set_luz('on'):
            result = 'on'

    elif todo == 'off':
        if zc.set_luz('off'):
            result = 'off'

    elif todo == 'state':
        return zc.consultar_estado()

    # status file
    mc.dump_element_status("zigbees", {elem_name: result})

    return result
