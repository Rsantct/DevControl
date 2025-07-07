#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to send Wake On LAN packets to PCs
"""


import subprocess as sp
import platform
from . import miscel as mc


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
        """ """
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


    def send_wol(mac):
        try:
            res = sp.check_output(f'wakeonlan {mac}', shell=True).decode().strip()
        except:
            res = 'Error with WOL'
        return res


    result = ''

    if 'target' not in args:
        return 'NACK'

    config = mc.read_config()

    if 'target' not in args or 'mode' not in args:
        return 'NACK'

    wol_id = args["target"]

    if wol_id not in config["devices"]["wol"]:
        return f'\'{wol_id}\' not configured'

    mac = config["devices"]["wol"][ wol_id ]

    if args["mode"] == 'send':
        result = send_wol(mac)

    elif args["mode"] == 'ping':
        ip = get_ip(mac)
        result = ping_host(ip)


    # status file
    if 'Sending' in result:
        mc.dump_element_status("wol", {wol_id: "waiting for ping response ..."})

    else:
        mc.dump_element_status("wol", {wol_id: result})


    return result
