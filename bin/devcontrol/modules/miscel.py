#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" miscellaneous
"""

import  os
import  yaml
import  json
from    time import  strftime

_MY_DIR      = os.path.dirname(__file__)

LOGPATH = f'{_MY_DIR}/../devcontrol.log'
CFGPATH = f'{_MY_DIR}/../devcontrol.yml'


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


    return config


def get_config(jsonarg):
    """
        Available jsonarg values:

            { "section":  "devices" OR "scripts" OR "web_config" }
    """

    res = 'NACK'

    if 'section' in jsonarg:

        if jsonarg["section"] in ['devices', 'scripts', 'web_config']:

            res = read_config()[ jsonarg["section"] ]

            # Min web refresh is 3 seconds
            if 'refresh_seconds' in res:
                if res["refresh_seconds"] < 3:
                    res["refresh_seconds"] = 3
                    print('(devcontrol) web refresh min value is 3 seconds')

    return json.dumps( res )


def do_log(cmd, res):
    with open(LOGPATH, 'a') as FLOG:
        FLOG.write(f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {res}\n')
