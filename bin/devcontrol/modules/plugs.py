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
        result = shelly.manage_plug(args)

    else:
        result = 'unknown plug protocol'


    # status file
    mc.dump_status("plugs", {plug_id: result})


    return result
