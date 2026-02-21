#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to manage user scripts
"""

import os
import sys
UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/bin')
sys.path.append(f'{UHOME}/bin/devcontrol/modules')

import subprocess as sp

import common as cm


def manage_script(args):
    """
        this simply runs an user script silently then returns the
        script response if any

        {'target': script_name, 'command': run | status }
    """

    result = ''

    if 'target' not in args:
        return result

    script_id = args["target"]

    if script_id not in cm.CONFIG["scripts"]:
        return f'\'{script_id}\' not configured'

    if 'command' not in args:
        return 'needs command: run | status'


    if args["command"] in ('run', 'send'):

        cmd = cm.CONFIG["scripts"][ script_id ]["button_cmd"]

        try:
            result = sp.check_output(cmd, shell=True).decode().strip()
        except:
            result = 'Error running the script'


    elif 'sta' in args["command"]:

        try:

            cmd = cm.CONFIG["scripts"][ script_id ]["status_cmd"]

            try:
                result = sp.check_output(cmd, shell=True).decode().strip()
            except:
                result = 'Error getting the script status'

        except:

            result = 'not available'

    return result
