#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to manage plugs
"""

import os
import sys
UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/bin')
sys.path.append(f'{UHOME}/bin/devcontrol/modules')
sys.path.append(f'{UHOME}/bin/devcontrol/modules/devices_mod')

import shelly

import common as cm


def manage_plug(args):
    """ wrapper to manage plugs depending on its protocol
    """

    plug_id = args["target"]

    plugs = cm.CONFIG["devices"]["plugs"]


    if plug_id not in plugs:
        return 'not configured'

    else:
        plug = plugs[plug_id]


    if 'protocol' in plug and plug["protocol"].lower() == 'shelly':
        result = shelly.manage_plug(args)

    else:
        result = 'unknown plug protocol'

    return result

