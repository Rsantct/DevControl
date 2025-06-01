#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to Wake On Lan PCs and switching Smart Plugs.
    This module is loaded by '../devcontrol_srv.py'
"""

import  os
import  subprocess as sp
from    time            import  strftime
import  yaml
import  json
import  requests
from    requests.auth   import HTTPDigestAuth

MY_DIR      = os.path.dirname(__file__)


def cmd_to_plug(ip, plug_cmd):

    u = 'admin'
    p = get_config()['plugs_pass']

    url = f'http://{ip}/{plug_cmd}'
    ans = ''

    try:
        response = requests.get(url, auth=HTTPDigestAuth(u, p))

        # Lanza una excepción para códigos de estado HTTP erróneos (4xx o 5xx)
        response.raise_for_status()

        ans = response.text

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la petición GET: {e}")

    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e}")

    return ans


def init():

    global LOGPATH

    # Command log file
    LOGPATH = f'{MY_DIR}/devcontrol.log'
    if os.path.exists(LOGPATH) and os.path.getsize(LOGPATH) > 10e6:
        print ( f"(devcontrol) log file exceeds ~ 10 MB '{LOGPATH}'" )
    print ( f"(devcontrol) logging commands in '{LOGPATH}'" )


def get_config():
    config = {}
    try:
        with open(f'{MY_DIR}/devcontrol.cfg', 'r') as f:
            config = yaml.safe_load(f)
    except:
        print(f'(devcontrol) UNABLE to read devcontrol.cfg')
    return config


def wol(wol_id):
    """ wol_id: as per the cfg file
    """

    config = get_config()

    if not wol_id in config["devices"]["wol"]:
        return f'\'{wol_id}\' not configured'

    mac  = config["devices"]["wol"][ wol_id ]

    try:
        result = sp.check_output(f'wakeonlan {mac}', shell=True) \
                .decode().strip()
    except:
        result = 'Error with WOL'

    return result


def manage_plug(plug_id, mode):
    """
        plug_id:    as per the cfg file
        mode:       on | off | toggle | status
    """

    if not mode:
        mode = 'status'

    res = 'NACK'

    config = get_config()

    if not plug_id in config["devices"]["plugs"]:
        return f'\'{plug_id}\' not configured'

    ip  = config["devices"]["plugs"][ plug_id ]

    if mode == 'toggle':
        plug_cmd = 'rpc/Switch.Toggle?id=0'

    elif mode == 'on':
        plug_cmd = 'rpc/Switch.Set?id=0&on=true'

    elif mode == 'off':
        plug_cmd = 'rpc/Switch.Set?id=0&on=false'

    if mode != 'status':
        cmd_to_plug(ip, plug_cmd)

    ans = cmd_to_plug(ip, 'rpc/Switch.GetStatus?id=0')

    if json.loads(ans)["output"]:
        res = 'on'
    else:
        res = 'off'

    return res


def script(script_id):

    config = get_config()

    if not script_id in config["devices"]["scripts"]:
        return f'\'{script_id}\' not configured'

    cmd  = config["devices"]["scripts"][ script_id ]

    try:
        result = sp.check_output(cmd, shell=True) \
                .decode().strip()
    except:
        result = 'Error with script'

    return result


def get_devices():
    return json.dumps( get_config()["devices"] )


def process_cmd( cmd_phrase ):
    """
        It is expected to receive a string of 1 to 3 words, like:

            command [arg [mode] ]
    """

    cmd = arg = mode = ''
    result = 'NACK'

    try:
        chunks = cmd_phrase.split()

        cmd = chunks[0]

        if chunks[1:]:
            arg = chunks[1]

        if chunks[2:]:
            mode = chunks[2]

    except:
        return 'Error'


    if cmd == 'wol':
        result = wol(arg)

    elif cmd == 'plug':
        result = manage_plug(arg, mode)

    elif cmd == 'get_devices':
        result = get_devices()

    elif cmd == 'script':
        result = script(arg)


    return result


# Interface function to plug this on server.py
def do( cmd_phrase ):

    result = 'NAK'
    cmd_phrase = cmd_phrase.strip()

    if cmd_phrase:

        # cmd_phrase log
        with open(LOGPATH, 'a') as FLOG:
            FLOG.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd_phrase}; ')

        result = process_cmd(cmd_phrase)

        if type(result) != str:
            result = json.dumps(result)

        # result log
        with open(LOGPATH, 'a') as FLOG:
            FLOG.write(f'{result}\n')

    return result


# Things to do first
init()
