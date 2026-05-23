#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" A module to retrieve user status log files
"""

import os
import sys
import subprocess as sp
import json

UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/bin')
sys.path.append(f'{UHOME}/bin/devcontrol/modules')

import common as cm


def read_status_deaemon(item):

    def read_last_status():
        """ the status file has one line for each status snapshot
        """

        res = {}

        try:
            with open(st_path, 'r') as f:
                lines = f.read()
                lines = [l for l in lines.split('\n') if l]
                last_line = lines[-1] if lines else ''

            if last_line:
                try:
                    res = json.loads(last_line)
                except Exception as e:
                    print(f'{cm.Fmt.RED}last_line: {last_line}{cm.Fmt.END}')
                    print(f'{cm.Fmt.RED}cannot read json: {str(e)}{cm.Fmt.END}')

            else:
                    print(f'{cm.Fmt.RED}void {st_path}{cm.Fmt.END}')

        except Exception as e:
            print(f'{cm.Fmt.RED}cannot read {st_path}: {str(e)}{cm.Fmt.END}')

        return res


    st_path = cm.CONFIG["status_daemons"].get(item, {}).get('state_path', '')

    return read_last_status()

