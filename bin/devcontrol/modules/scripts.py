#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to manage user scripts
"""


import subprocess as sp
from . import miscel as mc


def manage_script(args):
    """
        this simply runs an user script silently then returns the
        script response if any

        {'target': script_name, 'mode': run | status }
    """

    result = ''

    if 'target' not in args:
        return result

    config = mc.read_config()

    script_id = args["target"]

    if script_id not in config["scripts"]:
        return f'\'{script_id}\' not configured'

    if 'mode' not in args:
        return 'needs mode: run | status'


    if args["mode"] in ('run', 'send'):

        cmd = config["scripts"][ script_id ]["button_cmd"]

        try:
            result = sp.check_output(cmd, shell=True).decode().strip()
        except:
            result = 'Error running the script'


    elif 'stat' in args["mode"]:

        try:

            cmd = config["scripts"][ script_id ]["status_cmd"]

            try:
                result = sp.check_output(cmd, shell=True).decode().strip()
            except:
                result = 'Error getting the script status'

        except:

            result = 'not available'


    # status file
    mc.dump_element_status("scripts", {script_id: result})

    return result
