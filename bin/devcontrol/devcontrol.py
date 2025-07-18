#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

"""
    A program to:

        - Wake On Lan PCs
        - Switching Smart Plugs
        - Run user cripts

    This module is loaded by '../devcontrol_srv.py'
"""

import  os
import  json
import  threading
from    time import sleep

from    modules import wol
from    modules import plugs
from    modules import scripts
from    modules import miscel as mc
from    modules.fmt import Fmt


def init():

    if os.path.exists(mc.LOGPATH) and os.path.getsize(mc.LOGPATH) > 10e6:
        print ( f"(devcontrol) log file exceeds ~ 10 MB '{mc.LOGPATH}'" )
    print ( f"(devcontrol) logging commands in '{mc.LOGPATH}'" )

    # void info file
    with open(mc.STATUSPATH, 'w') as f:
        f.write( json.dumps( mc._STATUS_VOID ) )

    # Loading the configured plug schedules (currently only Shelly)
    plugs.shelly.set_configured_schedules()

    # Backend status update
    interval = mc.CONFIG["refresh"]["backend_update_interval"]
    if interval:
        refresh_job = threading.Thread(target=do_refresh_loop, args=(interval,))
        refresh_job.start()


def do_refresh_loop(interval):

    # LOOP
    while True:
        mc.dump_status()
        sleep(interval)


# Interface function to plug this on server.py
def do( cmd_phrase ):
    """
        It is expected to receive a command folowed by a json arguments block

            command {'target': xxxx, ... }
    """

    result = 'NACK'

    if cmd_phrase == 'hello':
        return 'hi!'

    try:

        cmd  = cmd_phrase.strip().split()[0]

        tail = cmd_phrase[ len(cmd): ].strip()

        if tail:
            args = json.loads( tail )
        else:
            args = {}

    except Exception as e:
        print(f'ERROR READING COMMAND: {str(e)}')
        return 'Error'


    if 'section' in args and cmd == 'get_config':
        result = mc.get_config(args)

    elif cmd == 'get_status':
        result = mc.read_status()

    elif 'target' in args:

        if   cmd == 'wol':
            result = wol.manage_wol(args)

        elif cmd == 'plug':
            result = plugs.manage_plug(args)

        elif cmd == 'script':
            result = scripts.manage_script(args)


    if type(result) != str:
        result = json.dumps(result)


    # Select what to log
    if cmd == 'get_config':
        pass

    elif 'mode' in args and args["mode"] in ('state', 'status', 'ping'):
        pass

    else:
        mc.do_log(cmd_phrase, result)

    return result


# Things to do first
init()
