#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" miscellaneous
"""

import  os
import  yaml
import  json
from    time import  strftime, sleep
from    .fmt import Fmt

from    . import wol
from    . import plugs
from    . import scripts

_MY_DIR      = os.path.dirname(__file__)

LOGPATH     = f'{_MY_DIR}/../devcontrol.log'
CFGPATH     = f'{_MY_DIR}/../devcontrol.yml'
STATUSPATH  = f'{_MY_DIR}/../.devcontrol'

_STATUS_VOID = { "wol": {}, "plugs": {}, "scripts": {} }

CONFIG = {}


def init():
    global CONFIG
    CONFIG = read_config(check_refresh=True)


def read_config(check_refresh=False):

    config = {  'devices':  { 'plugs':{}, 'wol':{} },
                'scripts':  {}
             }

    try:
        with open(CFGPATH, 'r') as f:
            config = yaml.safe_load(f)

        if 'wol' not in config["devices"]:
            config["devices"]["wol"] = {}

        if 'plugs' not in config["devices"]:
            config["devices"]["plugs"] = {}

        if 'scripts' not in config:
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


    # Early return
    if not check_refresh:
        return config


    # Backend update interval min 3 seconds, disabled if set to 0

    bui = config["refresh"]["backend_update_interval"]

    if bui <= 0:
        pass

    elif bui < 3:
        print(f'{Fmt.RED}(devcontrol) `backend_update_interval` forced to minimum 3 seconds.{Fmt.END}')
        config["refresh"]["backend_update_interval"] = 3

    # Web client refresh interval

    wri = config["refresh"]["web_refresh_interval"]

    if wri < 3:
        print(f'{Fmt.RED}(devcontrol) `web_refresh_interval` forced to minimum 3 seconds.{Fmt.END}')
        config["refresh"]["web_refresh_interval"] = 3


    return config


def get_config(jsonarg):
    """
        Available jsonarg values:

            { "section":  "devices" OR "scripts" OR "web_config" }
    """

    res = {}

    if 'section' in jsonarg:

        if jsonarg["section"] in ['devices', 'scripts', 'refresh']:

            res = read_config()[ jsonarg["section"] ]

    return res


def do_log(cmd, res):

    with open(LOGPATH, 'a') as f:
        f.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {res}\n')


def dump_status():

    wol_keys     = CONFIG["devices"]["wol"].keys()
    plug_keys    = CONFIG["devices"]["plugs"].keys()
    scripts_keys = CONFIG["scripts"].keys()

    st = _STATUS_VOID

    for wol_id in wol_keys:
        ans = wol.manage_wol( {"target": wol_id, "mode": "ping"} )
        st["wol"][wol_id] = ans


    for plug_id in plug_keys:
        ans = plugs.manage_plug( {"target": plug_id, "mode": "status"} )
        st["plugs"][plug_id] = ans


    for script_id in scripts_keys:
        ans = scripts.manage_script( {"target": script_id, "mode": "status"} )
        st["scripts"][script_id] = ans


    tries = 3

    while tries:

        try:
            with open(STATUSPATH, 'w') as f:
                f.write( json.dumps(st) )
            break

        except Exception as e:
            print(f'(miscel.dump_status) ERROR: {str(e)}')
            tries -= 1
            sleep(.2)


def dump_element_status(what, element_status):
    """ arguments:

            what:               wol | plugs | scripts   (string)

            element_status:     {elem_id: elem_status}  (dict)

        example:
                    "wol", {"Salon": "waiting for ping response"}
    """

    st = {}

    try:
        with open(STATUSPATH, 'r') as f:
            st = json.loads( f.read() )

    except Exception as e:
        print(f'Error reading `.devcontrol` status file')
        st = _STATUS_VOID

    # getting the only received key (see in wol module)
    elemet_id = next(iter( element_status ))

    st[what][elemet_id] = element_status[elemet_id]

    with open(STATUSPATH, 'w') as f:
        f.write( json.dumps(st) )


def read_status():
    """
        return the STATUS dict to a client

        if necessary, will query all elements by calling dump_status()

    """

    if not CONFIG["refresh"]["backend_update_interval"]:
        dump_status()

    resu = {}

    tries = 5

    while tries:

        try:
            with open(STATUSPATH, 'r') as f:
                resu = json.loads( f.read() )
                break

        except Exception as e:
            print(f'(miscel.read_status) ERROR: {str(e)}')
            tries -= 1
            sleep(.2)

    return resu


init()
