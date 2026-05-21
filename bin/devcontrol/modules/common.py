#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" common functions
"""

import  os
import  sys
import  yaml
import  json
from    time        import strftime, sleep, time
from    datetime    import datetime, timezone

from    fmt         import Fmt
import  wol
import  plugs
import  scripts
import  zigbees
import  status_daemons
import  crontool

_MY_DIR      = os.path.dirname(__file__)

LOGDIR      = f'{_MY_DIR}/../log'
LOGPATH     = f'{LOGDIR}/devcontrol.log'
CFGPATH     = f'{_MY_DIR}/../devcontrol.yml'
STATUSPATH  = f'{_MY_DIR}/../.devcontrol'
CONFIG      = {}


def init():
    """ You must call this from the main program after import common,
        BUT DO NOT call this inside this module.

        This way you avoid circular imports issues if other modules
        imported here also import this module.

        If you execute this  module from command line,
        then __main__ will do it for you, se below.
    """

    global CONFIG, STATUS

    if not os.path.isdir(LOGDIR):
        os.mkdir(LOGDIR)

    CONFIG = read_config()

    STATUS = { 'wol': {}, 'plugs': {}, 'scripts': {}, 'zigbees': {}, 'status_daemons': {} }


def is_integer(string):
    try:
        int(string)
        return True
    except:
        return False


def get_now_iso():
    """ ISO with (Z)ulu for Javascript: 2026-03-10T13:14:15Z
    """
    now = datetime.now(timezone.utc)
    return now.strftime('%Y-%m-%dT%H:%M:%SZ')


def clamp(n, minn=0, maxn=10):
    return max(minn, min(n, maxn))


def do_log(txt):
    with open(LOGPATH, 'a') as f:
        f.write(f'{get_now_iso()}; {txt}\n')


def get_section(section):
    """ This is for web clients. We only allow to get config data
        for devices, scripts or the refresh.web_polling_interval
    """

    res = {}

    if section in ['devices', 'scripts', 'status_daemons']:
        res = CONFIG.get(section, {})

    elif section == 'refresh':
        # web frontend resfres intervel
        res['polling_interval'] = CONFIG.get('refresh').get('web_polling_interval', 3)

    return res


def get_zname_scenes(zname):
    """ get_zname_scenes('salon_libreria')
        Out[3]: [{'id': 0, 'name': 'off'}, {'id': 1, 'name': 'on'}]
    """

    def group_scenes(group):
        return group.get('scenes', [])


    def device_scenes(device):
        """ this is more complex than group scenes
        """
        scenes = []

        try:
            for k, v in device.get('endpoints', {}).items():
                tmp = v.get('scenes')
                if tmp:
                    scenes = tmp
                    break

        except Exception as e:
            print(f'{Fmt.RED}(common.get_zname_scenes) ERROR: {e}{Fmt.BOLD}')

        return scenes


    scenes = []

    if zigbees.z.is_group(zname):
        z_found = next((x for x in zigbees.z.GROUPS  if x['friendly_name'] == zname), None)
        if z_found:
            scenes = group_scenes(z_found)

    else:
        z_found = next((x for x in zigbees.z.DEVICES if x['friendly_name'] == zname), None)
        if z_found:
            scenes = device_scenes(z_found)

    return scenes


def read_config():

    def refactor_zegbee_items():

        # replace 'zigbee_name' with 'friendly_name'
        for k, v in config["devices"]["zigbees"].items():
            config["devices"]["zigbees"][k]['friendly_name'] = v['zigbee_name']
            del  config["devices"]["zigbees"][k]['zigbee_name']

        # append 'scenes' for each item
        for k, v in config["devices"]["zigbees"].items():
            zname = v['friendly_name']
            config["devices"]["zigbees"][k]["scenes"] = get_zname_scenes(zname)

        # append zigbee propierty 'is_group'
        for k, v in config["devices"]["zigbees"].items():
            zname = v['friendly_name']
            if zigbees.z.is_group(zname):
                config["devices"]["zigbees"][k]["is_group"] = True
            else:
                config["devices"]["zigbees"][k]["is_group"] = False


    config = {  'devices':  { 'plugs':{}, 'wol':{} },
                'scripts':  {},
                'status_daemons': {}
             }

    try:
        with open(CFGPATH, 'r') as f:
            config = yaml.safe_load(f)

        if 'wol' not in config["devices"]:
            config["devices"]["wol"] = {}

        if 'plugs' not in config["devices"]:
            config["devices"]["plugs"] = {}

        if 'zigbees' not in config["devices"]:
            config["devices"]["zigbees"] = {}

        if 'scripts' not in config:
            config["scripts"] = {}

        if 'status_daemons' not in config:
            config["status_daemons"] = {}


    except Exception as e:
        print(f'(devcontrol) ERROR reading devcontrol.yml: {str(e)}')

    # Refactor the Zegbbe items
    refactor_zegbee_items()

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

    # Backend update interval 3...10 seconds, default 5.
    tmp = config["refresh"].get("backend_update_interval", 5)
    if tmp < 3:
        print(f'{Fmt.RED}(common) `backend_update_interval` forced to minimum 3 seconds.{Fmt.END}')
    elif tmp > 30:
        print(f'{Fmt.RED}(common) `backend_update_interval` forced to maximun 10 seconds.{Fmt.END}')
    config["refresh"]["backend_update_interval"] = min(max(3, tmp), 10)

    # Web client polling interval 2...10 seconds, default 3.
    tmp = config["refresh"].get("web_polling_interval", 3)
    if tmp < 3:
        print(f'{Fmt.RED}(common) `web_polling_interval` forced to minimum 2 seconds.{Fmt.END}')
    elif tmp > 30:
        print(f'{Fmt.RED}(common) `web_polling_interval` forced to maximun 10 seconds.{Fmt.END}')
    config["refresh"]["web_polling_interval"] = min(max(2, tmp), 10)

    return config


def read_status_from_disk():

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
        print(f'{Fmt.BOLD}(common.read_status) ERROR{Fmt.END}')

    return st


def dump_status_to_disk():

    tries = 3
    while tries:

        try:
            with open(STATUSPATH, 'w') as f:
                f.write( json.dumps(STATUS, indent=2) )
            break
        except:
            tries -= 1
            sleep(.2)

    if not tries:
        print(f'{Fmt.RED}(common.dump_status_to_disk) ERROR{Fmt.END}')
        return False

    else:
        print(f'{Fmt.GRAY}(common) dumping status to disk{Fmt.END}')
        return True


def refresh_all_status():
    """ This takes a while
    """

    global STATUS

    wol_keys            = CONFIG.get("devices", {}).get("wol",   {}).keys()
    plug_keys           = CONFIG.get("devices", {}).get("plugs", {}).keys()
    zigbees_keys        = CONFIG.get("devices", {}).get("zigbees", {}).keys()
    scripts_keys        = CONFIG.get("scripts", {}).keys()
    status_daemons_keys = CONFIG.get('status_daemons', {}).keys()

    st = { 'wol': {}, 'plugs': {}, 'scripts': {}, 'zigbees': {}, 'status_daemons':{} }

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

    for d_id in status_daemons_keys:
        ans = status_daemons.read_status_deaemon(d_id)
        st["status_daemons"][d_id] = ans

    st["timestamp"] = get_now_iso()

    STATUS = st


def dump_zigbees_schedule_to_crontab(simulate=True):
    """ Dump the configured Zigbee labels scheduling to the user crontab

        return: True if all schedules were loaded to crontab,
                else False
    """

    def make_cmd(zname, mode='off'):
        cmd = f'mosquitto_pub -h localhost -t "zigbee2mqtt/{zname}/set" -m \'{{"state": "{mode}"}}\''
        return cmd


    def make_cmt(zlabel, zname, mode):
        return f'Zigbee: {zname} ({zlabel}) --> {mode.upper()}'


    def update_cron(cron, zlabel, zname, schedules, is_group):
        """ process schedulling for a Zigbee label entry
            return: True or False
        """

        results = []

        for sch_name, sch_slice in schedules.items():

            if sch_name == 'switch_off':
                mode = 'off'
            elif sch_name == 'switch_on':
                mode = 'on'

            cmd = make_cmd(zname,  mode)
            cmt = make_cmt(zlabel, zname, mode)

            if crontool.job_exists( cron, patterns=(zname, f'"{mode}"') ):

                res = crontool.modify_jobs(
                    cron,
                    patterns=(zname, f'"{mode}"'),
                    new_command=cmd,
                    new_schedule=sch_slice,
                )

            else:

                res = crontool.add_new_job(
                    cron,
                    command=cmd,
                    schedule=sch_slice,
                    comment=cmt,
                )

            results.append( res["success"] )

        return all(results)

    CONFIG = read_config()

    my_cron = crontool.get_cron()
    print('\n(common) dump zigbee to crontab ---- ORIGINAL:')
    print(my_cron)

    results = []


    ## First off all let's remove any job for each Zigbee under config.yml
    #for zlabel, data in CONFIG['devices']['zigbees'].items():
    #    zname     = data.get('friendly_name', '')
    #    crontool.remove_jobs( cron=my_cron, patterns=(zname,) )
    #
    #print('\n(common) dump zigbee to crontab ---- CLEARED:')
    #print(my_cron)

    # Now update the configured schedules
    for zlabel, data in CONFIG['devices']['zigbees'].items():

        schedules = data.get('schedule', {})
        zname     = data.get('friendly_name', '')
        is_group  = data.get('is_group', False)


        res = False

        # Groups
        if is_group:

            zmembers = zigbees.z.get_miembros_de_grupo(zname)
            zmembers = [ x.get('friendly_name', '') for x in zmembers]

            for zmember in zmembers:
                res = update_cron(my_cron, zlabel, zmember, schedules, is_group)

        # Individual devices
        else:

            res = update_cron(my_cron, zlabel, zname, schedules, is_group)

        results.append(res)

    print('\n(common) dump zigbee to crontab ---- UPDATED:')
    print(my_cron)

    if all( results ):

        if my_cron:

            my_crontab_prettified = crontool.write_cron_prettified(my_cron, simulate=simulate)
            if my_crontab_prettified:
                print('\n---- PRETTIFIED CRONTAB:')
                print(my_crontab_prettified)
                print('----')
                do_log('write_cron_prettified; done')
                return True

            else:
                print(f'{Fmt.RED}write_cron_prettified failed{Fmt.END}')
                do_log('write_cron_prettified; failed')
                return False

        # void crontab
        else:
            print(f'{Fmt.RED}dump_zigbees_schedule_to_crontab IS EMPTY !!!{Fmt.END}')
            do_log('dump_zigbees_schedule_to_crontab; skipped because empty crontab')
            return False

    else:
        print(f'{Fmt.RED}dump_zigbees_schedule_to_crontab failed{Fmt.END}')
        do_log('dump_zigbees_schedule_to_crontab; failed')
        return False


if __name__ == "__main__":

    print('(common.py) running standalone')
    init()
