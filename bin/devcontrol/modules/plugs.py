#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to manage plugs
"""

from . import miscel as mc
from . import shelly


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
        return shelly.manage_plug(args)

    else:
        return 'unknown plug protocol'
