#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to manage Shelly devices
"""

from    time import sleep
import  json
import  urllib.parse
import  requests
from    requests.auth   import HTTPDigestAuth
import  threading

from    . import miscel as mc


def cmd_to_plug(host, plug_cmd, delay=0, verbose=False):
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

        if SHELLY_CFG["timeout"]:
            timeout = SHELLY_CFG["timeout"]
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

        # Logging no status commands
        if 'status' not in http_command.lower():
            mc.do_log(http_command, ans)

        if verbose:
            print()
            print('--- url:')
            print(http_command)
            print()
            print('--- response:')
            print(ans)
            print()

        return ans


    SHELLY_CFG = mc.read_config()["plugs"]["shelly"]

    u = 'admin'
    p = SHELLY_CFG["pass"]

    http_command = f'http://{host}/{plug_cmd}'


    if not delay:
        ans = send_http_get(http_command)

    else:
        job = threading.Thread(target=send_http_get, args=(http_command, delay))
        job.start()
        ans = 'ordered'

    return ans


def set_configured_schedules():
    """ Set PLUGs schedules as per configurated under the YAML file
    """

    def prepare_plug_schedule_cmd(plug_id, mode):
        """ mode:   switch_off | switch_on
        """

        # The `timespec` part
        timespec = plugs[ plug_id ]["schedule"][mode]

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
        calls = json.dumps(calls)   # , separators=(",", ":"))

        # This is a MUST:
        timespec = urllib.parse.quote(timespec)
        calls    = urllib.parse.quote(calls)

        # All together
        url_cmd = f'rpc/Schedule.Create?timespec="{timespec}"&calls={calls}'

        return url_cmd


    plugs = mc.read_config()["devices"]["plugs"]


    for plug_id, props in plugs.items():


        if 'protocol' not in props or not props["protocol"].lower() == 'shelly':
            continue

        host = props["address"]


        if 'schedule' in props and props["schedule"]:

            if 'schedule_mode' in props and props["schedule_mode"] == 'override':

                plug_cmd = 'rpc/Schedule.DeleteAll'
                cmd_to_plug( host, plug_cmd )


            for mode in ('switch_off', 'switch_on'):

                if mode in props["schedule"] and props["schedule"][mode]:

                    plug_cmd = prepare_plug_schedule_cmd(plug_id, mode)
                    cmd_to_plug( host, plug_cmd )


def manage_plug(args):
    """
        {   'target':   xxxx
            'mode':     on | off | toggle | status
            'delay':    N  (seconds)
        }
    """

    def get_plug_status():

        ans = cmd_to_plug(host, 'rpc/Switch.GetStatus?id=0')

        try:
            if json.loads(ans)["output"]:
                return 'on'
            else:
                return 'off'

        except:
            return ans


    def get_plug_schedules():
        """
            example of Shedule.List:

            {"jobs":    [
                            {   "id":       1,
                                "enable":   true,
                                "timespec": "0 10 2 * * *",
                                "calls":    [
                                                {"method": "Switch.Set", "params": {"id": 0, "on": false}}
                                            ]
                            }
                        ],
            "rev":103}


            Will return a list of tuples representing all jobs calls

            [ [ HH:MM:SS, ON | OFF ], ... ]
        """

        resu = []

        tmp = cmd_to_plug(host, 'rpc/Schedule.List')

        try:
            tmp = json.loads( tmp )
            jobs_list = tmp["jobs"]

        except:
            # if plug was not reachable (`tmp` == 'timed out')
            return resu

        for job in jobs_list:

            timespec = job["timespec"].split()

            hh, mm, ss = [x.zfill(2) for x in timespec[0:3][::-1]]

            # lets discard the seconds
            hhmm = ':'.join( (hh, mm) )

            dom, mon, dow = timespec[3:]

            nice_timespec = f'{hhmm} {dom} {mon} {dow}'

            for job_call in job["calls"]:

                if job_call["method"] == 'Switch.Set':

                    if job_call["params"]["on"]:
                        resu.append( (nice_timespec, 'ON') )

                    else:
                        resu.append( (nice_timespec, 'OFF') )

        return resu


    res = 'NACK'

    if 'target' not in args:
        return res

    if 'mode' not in args:
        args["mode"] = 'status'

    if 'delay' not in args:
        args['delay'] = 0

    plug_id = args["target"]
    mode    = args["mode"]
    delay   = args["delay"]

    if type(delay) != int:
        return 'delay (seconds) must be integer'

    config = mc.read_config()

    if plug_id not in config["devices"]["plugs"]:
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
            return cmd_to_plug(host, plug_cmd)

        elif args['schedule'] == 'nice_list':
            return get_plug_schedules()

        elif args['schedule'] == 'delete':
            plug_cmd = f'rpc/Schedule.Delete?id={args["schedule_id"]}'
            return cmd_to_plug(host, plug_cmd)

        elif args['schedule'] == 'deleteall':
            plug_cmd = 'rpc/Schedule.DeleteAll'
            return cmd_to_plug(host, plug_cmd)

        elif args['schedule'] == 'create_configured':
            set_configured_schedules()
            plug_cmd = 'rpc/Schedule.List'
            return cmd_to_plug(host, plug_cmd)

        else:
            return 'NACK'

    else:
        return res


    # No changes
    if 'stat' in mode:
        return get_plug_status()

    # Change the plug output
    else:

        plug_ans = cmd_to_plug(host, plug_cmd, delay)

        # Delayed
        if plug_ans == 'ordered':

            res = 'ordered'

        # Not delayed, want to know the new state
        else:
            res = get_plug_status()

    return res
