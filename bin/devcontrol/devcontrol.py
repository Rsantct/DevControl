#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to Wake On Lan PCs and switching Smart Plugs.
    This module is loaded by '../devcontrol_srv.py'
"""

import  os
import  subprocess as sp
from    time            import  strftime, sleep
import  yaml
import  json
import  requests
from    requests.auth   import HTTPDigestAuth
import  threading

MY_DIR      = os.path.dirname(__file__)


def cmd_to_plug(ip, plug_cmd, delay=0):

    def send(url, delay=delay):

        sleep(delay)

        response = requests.get(url, auth=HTTPDigestAuth(u, p))

        # Lanza una excepción para códigos de estado HTTP erróneos (4xx o 5xx)
        response.raise_for_status()

        return response.text


    u = 'admin'
    p = read_config()['plugs_pass']

    url_command = f'http://{ip}/{plug_cmd}'
    ans = ''

    try:

        if not delay:
            ans = send(url_command)

        else:
            job = threading.Thread(target=send, args=(url_command, delay))
            job.start()
            ans = 'ordered'

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


def read_config():
    config = {}
    try:
        with open(f'{MY_DIR}/devcontrol.cfg', 'r') as f:
            config = yaml.safe_load(f)
    except:
        print(f'(devcontrol) UNABLE to read devcontrol.cfg')
    return config


def wol(args):
    """
        {'target': xxxxx }
    """
    result = 'NACK'

    if not 'target' in args:
        return result

    config = read_config()

    wol_id = args["target"]

    if not wol_id in config["devices"]["wol"]:
        return f'\'{wol_id}\' not configured'

    mac  = config["devices"]["wol"][ wol_id ]

    try:
        result = sp.check_output(f'wakeonlan {mac}', shell=True) \
                .decode().strip()
    except:
        result = 'Error with WOL'

    return result


def manage_plug(args):
    """
        {   'target':   xxxx
            'mode':     on | off | toggle | status
            'delay':    N  (seconds)
        }
    """

    res = 'NACK'

    if not 'target' in args:
        return res

    if not 'mode' in args:
        args["mode"] = 'status'

    if not 'delay' in args:
        args['delay'] = 0

    plug_id = args["target"]
    mode    = args["mode"]
    delay   = args["delay"]

    config = read_config()

    if not plug_id in config["devices"]["plugs"]:
        return f'\'{plug_id}\' not configured'

    ip  = config["devices"]["plugs"][ plug_id ]

    if mode == 'toggle':
        plug_cmd = 'rpc/Switch.Toggle?id=0'

    elif mode == 'on':
        plug_cmd = 'rpc/Switch.Set?id=0&on=true'

    elif mode == 'off':
        plug_cmd = 'rpc/Switch.Set?id=0&on=false'

    elif mode == 'status':
        pass

    else:
        return res

    ans = ''
    if mode != 'status':
        ans = cmd_to_plug(ip, plug_cmd, delay)

    if ans != 'ordered':
        ans = cmd_to_plug(ip, 'rpc/Switch.GetStatus?id=0')

        if json.loads(ans)["output"]:
            res = 'on'
        else:
            res = 'off'
    else:
        res = ans

    return res


def script(args):
    """
        {'target': xxxxx }
    """
    result = 'NACK'

    if not 'target' in args:
        return result

    config = read_config()

    script_id = args["target"]

    if not script_id in config["scripts"]:
        return f'\'{script_id}\' not configured'

    cmd  = config["scripts"][ script_id ]

    try:
        result = sp.check_output(cmd, shell=True) \
                .decode().strip()
    except:
        result = 'Error with script'

    return result


def get_config(jsonarg):

    res = 'NACK'

    if 'section' in jsonarg:

        if jsonarg["section"] in ['devices', 'scripts']:

            res = json.dumps( read_config()[ jsonarg["section"] ] )

    return res



# Interface function to plug this on server.py
def do( cmd_phrase ):
    """
        It is expected to receive a command folowed by a json arguments block

            command {'target': xxxx, ... }
    """

    result = 'NACK'

    try:
        cmd  = cmd_phrase.strip().split()[0]
        args = json.loads( cmd_phrase[ len(cmd): ].strip() )

    except Exception as e:
        print(f'ERROR READING COMMAND: {str(e)}')
        return 'Error'


    if cmd == 'get_config':
        result = get_config(args)

    elif cmd == 'wol':
        result = wol(args)

    elif cmd == 'plug':
        result = manage_plug(args)

    elif cmd == 'script':
        result = script(args)

    if type(result) != str:
        result = json.dumps(result)

    if 'mode' in args and args["mode"] == 'status':
        pass

    else:

        # log cmd_phrase
        with open(LOGPATH, 'a') as FLOG:
            FLOG.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd_phrase}; ')

        # log the result
        with open(LOGPATH, 'a') as FLOG:
            FLOG.write(f'{result}\n')

    return result


# Things to do first
init()
