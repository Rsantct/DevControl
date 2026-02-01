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
import json
import miscel as mc
from   fmt import Fmt

import zigbee_control as zc


def es_grupo(zid):

    for grupo in zc.GRUPOS:
        if zid == grupo.get('friendly_name'):
            return True

    return False


def init_zc(device, verbose=False):
    zc.verbose  = verbose
    zc.ZNAME = device
    zc.prepare_zname()
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
        {'target': element_name, 'command': a command phrase }
    """

    #### set verbose to True to DEBUG here
    verbose = False
    ####

    result = ''

    if 'target' not in args:
        return result

    config = mc.read_config()

    elem_name = args['target']
    zname     = config.get('zigbees', {}).get(elem_name, '')
    tmp       = args.get('command', '').split(' ')
    command   = tmp[0]
    args      = tmp[1:]

    if not init_zc(zname, verbose=verbose):
        print(f'(manage_zigbee) ERROR with {zname}')
        return f'error with zigbee_id: {zname}'

    if zc.verbose:
        print('---- DEBUG manage_zigbee()')


    if command == 'toggle':

        result = do_toggle(zname)

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

        if es_grupo(zname):
            result = zc.consultar_estado_grupo(zname)

        else:
            status = zc.consultar_estado()
            result = status.get('state', 'unknown')

    zc.desconectar_del_broker_mqtt()

    if zc.verbose:
        print('----')

    return result


zc.update_devices()
