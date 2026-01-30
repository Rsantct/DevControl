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

import miscel as mc
import shelly


def manage_plug(args):
    """ wrapper to manage plugs depending on its protocol
    """

    plug_id = args["target"]

    plugs = mc.read_config()["devices"]["plugs"]


    if plug_id not in plugs:
        return 'not configured'

    else:
        plug = plugs[plug_id]


    if 'protocol' in plug and plug["protocol"].lower() == 'shelly':
        result = shelly.manage_plug(args)

    else:
        result = 'unknown plug protocol'

    return result
