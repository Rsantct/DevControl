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


def manage_zigbee(args):
    """
        this simply toggles or queries the status of a device
        then returns the response if any

        {'target': z_name, 'mode': toggle | state }
    """

    result = ''

    if 'target' not in args:
        return result

    config = mc.read_config()

    # this is the Zigbee2Mqtt device
    device = config.get('zigbees', {}).get(args['target'], '')



    # status file
    #mc.dump_element_status("zigbees", {device_id: result})

    return device
