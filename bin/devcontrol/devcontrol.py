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


def _cmd_to_plug(ip, plug_cmd, delay=0):
    """
        sends an http command to a plug with optional delay

        returns:
            'some json string' from the http plug API
            OR
            'ordered' when delayed
            OR
            'no answer' if plug is not available
    """


    def send_http(http_command, delay=0):
        """
            the actual http request with optional delay,
            if so you may want to thread this function call.
        """

        sleep(delay)

        ans = 'no answer'

        if 'plug_timeout':
            timeout = read_config()['plug_timeout']
        else:
            timeout = 1

        try:
            response = requests.get(http_command, auth=HTTPDigestAuth(u, p), timeout=timeout)

            # Lanza una excepción para códigos de estado HTTP erróneos (4xx o 5xx)
            response.raise_for_status()

            ans = response.text

        except requests.exceptions.Timeout:
            print("The request timed out")

        except requests.exceptions.RequestException as e:
            print(f"GET request error: {e}")

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")

        except Exception as e:
            print(f"Request error: {e}")

        print(f'send_http Rx: {ans}')

        return ans


    u = 'admin'
    p = read_config()['plug_pass']

    http_command = f'http://{ip}/{plug_cmd}'


    if not delay:
        ans = send_http(http_command)

    else:
        job = threading.Thread(target=send_http, args=(http_command, delay))
        job.start()
        ans = 'ordered'

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
        with open(f'{MY_DIR}/devcontrol.yml', 'r') as f:
            config = yaml.safe_load(f)
    except:
        print(f'(devcontrol) UNABLE to read devcontrol.yml')
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

    def get_plug_status():

        ans = _cmd_to_plug(ip, 'rpc/Switch.GetStatus?id=0')

        try:
            if json.loads(ans)["output"]:
                return 'on'
            else:
                return 'off'

        except:
            return ans


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

    if type(delay) != int:
        return 'delay (seconds) must be integer'

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


    # No changes
    if mode == 'status':
        return get_plug_status()

    # Change the plug output
    else:

        plug_ans = _cmd_to_plug(ip, plug_cmd, delay)

        # Delayed
        if plug_ans == 'ordered':

            res = 'ordered'

        # Not delayed, want to know the new state
        else:
            res = get_plug_status()

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

    if cmd_phrase == 'hello':
        return 'hi!'

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
