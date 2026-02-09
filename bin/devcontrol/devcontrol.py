#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

"""
    A program to:

        - Wake On Lan PCs
        - Switching Smart Plugs
        - Run user cripts
        - Manage Zigbee devices

    This module is loaded by '../devcontrol_srv.py'
"""

import  os
import  sys
UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/bin')
sys.path.append(f'{UHOME}/bin/devcontrol/modules')

import  json
from    time    import sleep, time
import  threading

from    fmt     import Fmt
import  common  as cm
import  wol
import  plugs
import  scripts
import  zigbees


def init():

    def loop_refresh_and_dump_all_status():
        pause = cm.CONFIG["refresh"]["backend_update_interval"]
        while True:
            cm.refresh_all_status()
            cm.dump_status_to_disk()
            sleep(pause)

    # Common needs to prepare CONFIG and other tasks
    cm.init()

    # Notice about logging
    if os.path.exists(cm.LOGPATH) and os.path.getsize(cm.LOGPATH) > 10e6:
        print ( f"(devcontrol.py) log file exceeds ~ 10 MB '{cm.LOGPATH}'" )
    print ( f"(devcontrol.py) logging commands in '{cm.LOGPATH}'" )

    # Loading the configured plug schedules (currently only Shelly)
    plugs.shelly.set_configured_schedules()

    # Loop status auto-update
    j1 = threading.Thread( target=loop_refresh_and_dump_all_status )
    j1.start()
    print ( f"(devcontrol.py) threading loop for refreshing the status in background ...'" )


# Interface function to plug this on server.py
def do( cmd_phrase ):
    """
        It is expected to receive a prefix name folowed by a json arguments block,
        example:

            plugs {'target': xxxx, 'command': command }

            prefix:             command:
            -------             ---------

            plug
                    shelly      on off toggle status

            script              run/send   status

            wol                 send ping

            zigbee              on off toggle status

        OR
            get_config          { 'section': section_name }

        OR
            hello
    """

    # Ping response
    if cmd_phrase in ('hello', 'ping'):
        return 'hi!'

    # Reading the command phrase
    try:

        prefix  = cmd_phrase.strip().split()[0]

        tail    = cmd_phrase.strip()[ len(prefix): ].strip()

        if tail:
            args = json.loads( tail )
        else:
            args = {}

    except Exception as e:
        print(f'(devcontrol.py) ERROR reading command: {str(e)}')
        return 'Error'

    # Processing the command phrase and saving common.STATUS
    result = 'NACK'

    do_save_status = False
    try:

        if prefix == 'get_config' and 'section' in args:
            result = cm.get_section( args["section"] )

        elif prefix == 'get_status':
            result = cm.STATUS

        elif 'target' in args.keys():

            if   prefix == 'wol':
                result = wol.manage_wol(args)

            elif prefix == 'plug':
                result = plugs.manage_plug(args)

            elif prefix == 'script':
                result = scripts.manage_script(args)

            elif prefix == 'zigbee':
                result = zigbees.manage_zigbee(args)

            # Save the status flag:
            if 'command' in args.keys() and \
                not ('sta' in args["command"] or 'sched' in args["command"]):
                    do_save_status = True

    except Exception as e:
        print(f'{Fmt.RED}(devcontrol.py) ERROR processing command phrase: {e}{Fmt.END}')

    # Save the status if the flag is set
    if do_save_status:
        section = {
            'wol':      'wol',
            'plug':     'plugs',
            'script':   'scripts',
            'zigbee':   'zigbees'
        }.get(prefix)

        cm.STATUS[section][args['target']] = result

        if cm.dump_status_to_disk():
            print(f'{Fmt.BLUE}(devcontrol.py) dumping status to disk{Fmt.END}')

    # Select what to log
    if prefix == 'get_config':
        pass
    elif 'command' in args and args["command"] in ('state', 'status', 'ping'):
        pass
    else:
        cm.do_log(cmd_phrase, result)

    return json.dumps(result)


# Things to do first
init()
