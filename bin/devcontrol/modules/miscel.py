#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" miscellaneous
"""

import  os
import  yaml
import  json
from    time import  strftime, sleep, time
from    fmt import Fmt

import  wol
import  plugs
import  scripts
import  zigbees

_MY_DIR      = os.path.dirname(__file__)

LOGPATH     = f'{_MY_DIR}/../devcontrol.log'
CFGPATH     = f'{_MY_DIR}/../devcontrol.yml'
STATUSPATH  = f'{_MY_DIR}/../.devcontrol'
CONFIG      = {}

def init():
    global CONFIG
    CONFIG = read_config()


def read_config():

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

    # Backend update interval 3...30 seconds, default 5.
    tmp = config["refresh"].get("backend_update_interval", 5)
    if tmp < 3:
        print(f'{Fmt.RED}(devcontrol) `backend_update_interval` forced to minimum 3 seconds.{Fmt.END}')
    elif tmp > 30:
        print(f'{Fmt.RED}(devcontrol) `backend_update_interval` forced to maximun 10 seconds.{Fmt.END}')
    config["refresh"]["backend_update_interval"] = min(max(3, tmp), 30)

    # Web client polling interval 3...30 seconds, default 5.
    tmp = config["refresh"].get("web_polling_interval", 5)
    if tmp < 3:
        print(f'{Fmt.RED}(devcontrol) `web_polling_interval` forced to minimum 3 seconds.{Fmt.END}')
    elif tmp > 30:
        print(f'{Fmt.RED}(devcontrol) `web_polling_interval` forced to maximun 10 seconds.{Fmt.END}')
    config["refresh"]["web_polling_interval"] = min(max(3, tmp), 30)


    return config


def get_config(jsonarg):
    """
        Available jsonarg values:

            { "section":  devices | scripts | zegbees | refresh }
    """

    res = {}

    if 'section' in jsonarg:

        target = jsonarg["section"]

        if target in ['devices', 'scripts', 'zigbees', 'refresh']:
            res = read_config().get(target, {})

    return res


def do_log(cmd, res):

    with open(LOGPATH, 'a') as f:
        f.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {res}\n')


def read_status():

    st = {}

    tries = 3
    while tries:

        try:
            with open(STATUSPATH, 'r') as f:
                st = json.loads( f.read() )
            break
        except:
            tries -= 1
            sleep(.1)

    if not tries:
        print(f'{Fmt.BOLD}(miscel.read_status) ERROR{Fmt.END}')

    return st


def dump_status():

    wol_keys     = CONFIG["devices"]["wol"].keys()
    plug_keys    = CONFIG["devices"]["plugs"].keys()
    scripts_keys = CONFIG["scripts"].keys()
    zigbees_keys = CONFIG["zigbees"].keys()

    st = { 'wol': {}, 'plugs': {}, 'scripts': {}, 'zigbees': {} }

    for wol_id in wol_keys:
        ans = wol.manage_wol( {"target": wol_id, "command": "ping"} )
        st["wol"][wol_id] = ans

    for plug_id in plug_keys:
        ans = plugs.manage_plug( {"target": plug_id, "command": "status"} )
        st["plugs"][plug_id] = ans

    for script_id in scripts_keys:
        ans = scripts.manage_script( {"target": script_id, "command": "status"} )
        st["scripts"][script_id] = ans

    for z_id in zigbees_keys:
        ans = zigbees.manage_zigbee( {"target": z_id, "command": "status"} )
        st["zigbees"][z_id] = ans

    tries = 3
    while tries:

        try:
            with open(STATUSPATH, 'w') as f:
                f.write( json.dumps(st) )
            break
        except:
            tries -= 1
            sleep(.2)

    if not tries:
        print(f'{Fmt.BOLD}(miscel.dump_status) ERROR{Fmt.END}')

init()
