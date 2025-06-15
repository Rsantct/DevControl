#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to:
        - Wake On Lan PCs
        - Switching Smart Plugs
        - Run user cripts

    This module is loaded by '../devcontrol_srv.py'
"""

import  os
import  subprocess as sp
import  platform
from    time            import  strftime, sleep
import  yaml
import  json
import  urllib.parse
import  requests
from    requests.auth   import HTTPDigestAuth
import  threading

MY_DIR      = os.path.dirname(__file__)


def init():


    # Command log file
    global LOGPATH

    LOGPATH = f'{MY_DIR}/devcontrol.log'
    if os.path.exists(LOGPATH) and os.path.getsize(LOGPATH) > 10e6:
        print ( f"(devcontrol) log file exceeds ~ 10 MB '{LOGPATH}'" )
    print ( f"(devcontrol) logging commands in '{LOGPATH}'" )

    create_configured_schedules()


def create_configured_schedules():
    """
        PLUGs schedule as per configurated under the YAML file
    """

    config = read_config()

    for plug_id, content in config["devices"]["plugs"].items():

        host = content["address"]

        if 'schedule' in content and content["schedule"]:

            plug_cmd = 'rpc/Schedule.DeleteAll'
            _cmd_to_plug( host, plug_cmd )

            for mode in ('switch_off', 'switch_on'):

                if mode in content["schedule"] and content["schedule"][mode]:

                    plug_cmd = prepare_plug_schedule(plug_id, mode)
                    _cmd_to_plug( host, plug_cmd )


def prepare_plug_schedule(plug_id, mode):
    """ mode:   switch_off | switch_on
    """

    config = read_config()

    # The `timespec` part
    timespec = config["devices"]["plugs"][ plug_id ]["schedule"][mode]

    # Remove leading zeroes if any
    timespec = timespec.split()
    timespec_cleaned = []
    for x in timespec:
        if x.isdigit():
            timespec_cleaned.append( str(int(x)) )
        else:
            timespec_cleaned.append( x )

    # Back to string with SINGLE spaces
    timespec = ' '.join( timespec_cleaned )


    # The `calls` part
    calls = [   {   "method":   "Switch.Set",
                    "params":   {   "id": 0,
                                    "on": True if 'on' in mode else False
                                }
                }
            ]

    # Separators will remove unnecessary spaces (but it is not necessary)
    calls = json.dumps(calls) #, separators=(",", ":"))

    # This is a MUST:
    timespec = urllib.parse.quote(timespec)
    calls    = urllib.parse.quote(calls)

    # All together
    url_cmd = f'rpc/Schedule.Create?timespec="{timespec}"&calls={calls}'

    return url_cmd


def _cmd_to_plug(host, plug_cmd, delay=0, verbose=False):
    """
        sends an http command to a plug with optional delay

        returns:
            'some json string' from the http plug API
            OR
            'ordered' when delayed
            OR
            'no answer' if plug is not available
    """


    def send_http_get(http_command, delay=0):
        """
            This is the actual http request with optional delay,
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
            ans = 'timed out'

        except requests.exceptions.RequestException as e:
            ans = f'GET error: {str(e)}'

        except requests.exceptions.HTTPError as e:
            ans = f'HTTP error: {str(e)}'

        except Exception as e:
            ans = f'request error: {str(e)}'

        print(f'send_http_get Rx: {ans}')

        # Logging no status commands
        if not 'status' in http_command.lower():
            do_log(http_command, ans)

        if verbose:
            print()
            print('--- url:')
            print(http_command)
            print()
            print('--- response:')
            print(ans)
            print()

        return ans


    u = 'admin'
    p = read_config()['plug_pass']

    http_command = f'http://{host}/{plug_cmd}'


    if not delay:
        ans = send_http_get(http_command)

    else:
        job = threading.Thread(target=send_http_get, args=(http_command, delay))
        job.start()
        ans = 'ordered'

    return ans


def read_config():

    config = {  'devices':  { 'plugs':{}, 'wol':{} },
                'scripts':  {}
             }

    try:
        with open(f'{MY_DIR}/devcontrol.yml', 'r') as f:
            config = yaml.safe_load(f)

        if not 'wol' in config["devices"]:
            config["devices"]["wol"] = {}

        if not 'plugs' in config["devices"]:
            config["devices"]["plugs"] = {}

        if not 'scripts' in config:
            config["scripts"] = {}

    except Exception as e:
        print(f'(devcontrol) ERROR reading devcontrol.yml: {str(e)}')


    # Script status responses allow space or comma separated values
    for script, values in config["scripts"].items():

        if 'responses' in values and values["responses"]:

            tmp = values["responses"]

            if type(tmp) == str:
                if ',' in tmp:
                    tmp = [ x.strip() for x in tmp.split(',') ]
                else:
                    tmp = tmp.split()

            elif type(tmp) != list:
                raise Exception(f'Bad responses values in {script}')

            config["scripts"][script]["responses"] = tmp


    return config


def manage_wol(args):
    """
        {   'target':   xxxxx,
            'mode':     send | ping
        }
    """

    def get_ip(mac):
        """ Search an IP from the O.S. ARP MAC/IP table
        """

        ip = ''

        try:
            tmp = sp.check_output(['arp']).decode().strip()

        except Exception as e:
            print(f'(devcontrol) ERROR getting IP from MAC: {str(e)}')
            return ip

        arp_lines = tmp.split('\n')
        arp_table = [ line.split() for line in arp_lines ]

        for row in arp_table:
            if row[2].lower() == mac.lower():
                ip = row[0]
                break

        return ip


    def ping_host(host):

        param = '-n' if 'windows' in platform.system().lower() else '-c'

        ping_command = ['ping', param, '1', host]

        try:
            output = sp.run(ping_command, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
            if output.returncode == 0:
                return 'up'
            else:
                return 'not reachable'

        except Exception as e:
            print(f"Error: {e}")
            return 'error with ping'


    result = 'NACK'

    if not 'target' in args:
        return result

    config = read_config()

    if not 'target' in args or not 'mode' in args:
        return result

    wol_id = args["target"]

    if not wol_id in config["devices"]["wol"]:
        return f'\'{wol_id}\' not configured'

    mac  = config["devices"]["wol"][ wol_id ]

    if args["mode"] == 'send':

        try:
            result = sp.check_output(f'wakeonlan {mac}', shell=True) \
                    .decode().strip()
        except:
            result = 'Error with WOL'

    elif args["mode"] == 'ping':
        ip = get_ip(mac)
        result = ping_host(ip)


    return result


def manage_plug(args):
    """
        {   'target':   xxxx
            'mode':     on | off | toggle | status
            'delay':    N  (seconds)
        }
    """

    def get_plug_status():

        ans = _cmd_to_plug(host, 'rpc/Switch.GetStatus?id=0')

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

    host  = config["devices"]["plugs"][ plug_id ]["address"]

    if mode == 'toggle':
        plug_cmd = 'rpc/Switch.Toggle?id=0'

    elif mode == 'on':
        plug_cmd = 'rpc/Switch.Set?id=0&on=true'

    elif mode == 'off':
        plug_cmd = 'rpc/Switch.Set?id=0&on=false'

    elif 'stat' in mode:
        pass

    elif mode == 'schedule':

        if args['schedule'] == 'list':
            plug_cmd = 'rpc/Schedule.List'
            return _cmd_to_plug(host, plug_cmd)

        elif args['schedule'] == 'delete':
            plug_cmd = f'rpc/Schedule.Delete?id={args["schedule_id"]}'
            return _cmd_to_plug(host, plug_cmd)

        elif args['schedule'] == 'deleteall':
            plug_cmd = 'rpc/Schedule.DeleteAll'
            return _cmd_to_plug(host, plug_cmd)

        elif args['schedule'] == 'create_configured':
            create_configured_schedules()
            plug_cmd = 'rpc/Schedule.List'
            return _cmd_to_plug(host, plug_cmd)

        else:
            return 'NACK'

    else:
        return res


    # No changes
    if 'stat' in mode:
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


def manage_script(args):
    """
        this simply runs an user script silently then returns the
        script response if any

        {'target': script_name, 'mode': run | status }
    """

    result = ''

    if not 'target' in args:
        return result

    config = read_config()

    script_id = args["target"]

    if not script_id in config["scripts"]:
        return f'\'{script_id}\' not configured'

    if not 'mode' in args:
        return 'needs mode: run | status'


    if args["mode"] in ('run', 'send'):

        cmd  = config["scripts"][ script_id ]["button_cmd"]

        try:
            result = sp.check_output(cmd, shell=True) \
                    .decode().strip()
        except:
            result = 'Error running the script'


    elif 'stat' in args["mode"]:

        try:

            cmd  = config["scripts"][ script_id ]["status_cmd"]

            try:
                result = sp.check_output(cmd, shell=True) \
                        .decode().strip()
            except:
                result = 'Error getting the script status'

        except:

            result = 'not available'


    return result


def get_config(jsonarg):
    """
        Available jsonarg values:

            {"section":  "devices" | "scripts" | "web_config"}
    """

    res = 'NACK'

    if 'section' in jsonarg:

        if jsonarg["section"] in ['devices', 'scripts', 'web_config']:

            res = read_config()[ jsonarg["section"] ]

            # Min web refresh is 3 seconds
            if 'refresh_seconds' in res:
                if res["refresh_seconds"] < 3:
                    res["refresh_seconds"] = 3
                    print(f'(devcontrol) web refresh min value is 3 seconds')

    return json.dumps( res )


def do_log(cmd, res):
        with open(LOGPATH, 'a') as FLOG:
            FLOG.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {res}\n')


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
        result = manage_wol(args)

    elif cmd == 'plug':
        result = manage_plug(args)

    elif cmd == 'script':
        result = manage_script(args)

    if type(result) != str:
        result = json.dumps(result)

    if cmd == 'get_config':
        pass

    elif 'mode' in args and args["mode"] in ('state', 'status', 'ping'):
        pass

    else:
        do_log(cmd_phrase, result)

    return result


# Things to do first
init()
