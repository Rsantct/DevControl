#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" a cron tool
"""

import subprocess
import re
from   crontab import CronTab


def write_cron_prettified(cron, simulate=False):
    """ a replacement of cron.write() in order to prettify the crontab:
         - Zeropaded figures for minute, and hour
         - Comments are moved from the job line to the line above the job
    """

    result = False

    lines = cron.render().splitlines()

    try:
        padded_lines = []
        for line in lines:

            # Pad minute if it is a digit
            new_line = re.sub(r'^(\d)\s', r'0\1 ', line)

            # Pad hour if it is a digit
            new_line = re.sub(r'^(\S+)\s(\d)\s', r'\1 0\2 ', new_line)

            # Move comment
            if '#' in new_line and not new_line.strip().startswith('#'):
                i = new_line.index('#')
                job = new_line[:i].strip()
                cmt = new_line[i:].strip()
                padded_lines.append(cmt)
                padded_lines.append(job)

            else:
                padded_lines.append(new_line)

        final_cron_str = "\n".join(padded_lines) + "\n"

        result = True

    except Exception as e:
        print(f'(write_cron_prettified) ERROR: {e}')


    if simulate:
        print('\n---- SIMULATION ----')
        print(final_cron_str)
        print()

    else:
        try:
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
            process.communicate(input=final_cron_str.encode())
            result = True
            #print("✅ (crontool) Crontab saved (with zero padding minute and hour)")

        except Exception as e:
            print(f'(write_cron_prettified) ERROR: {e}')

    return result


def get_cron():
    """ crontab from the current user
    """
    return CronTab(user=True)


def job_exists(patterns=()):
    """
        Check if there is a job whose command contains ALL the strings in 'patterns'.

        <patterns> can be a string or a tuple/list of strings.

        NOTICE: cron.find_comment(pattern) ONLY WORKS for trailing
                comments in the same line as the job itself,
                so we discard this method of searching.
    """

    cron = get_cron()

    # single string --> tuple so that the loop works the same
    if isinstance(patterns, str):
        patterns = (patterns,)

    for job in cron:
        if all(p in job.command for p in patterns):
            return True

    return False


def add_new_job(cron, command, comment=None, schedule="0 0 * * *"):
    """ Schedule must in standard format 'min hour day month dow'

        Returns a dictionary with the modified cron object and result details

        The cron object (took by reference) will result modified in place
    """
    report = ''
    success = False

    # schedule string must be cleaned of extra spaces:
    schedule = " ".join(schedule.split())

    # Avoid duplicates
    if job_exists(command):
        print("❌ (crontool.add_new_job) job command exists, NOT added")
        report = f'ERROR: job command exists, NOT added.'

    else:

        try:
            job = cron.new(command=command, comment=comment)
            job.setall(schedule)
            success = True

        except Exception as e:
            print(f"❌ (crontool.add_new_job) ERROR: {e}")
            report = f'ERROR: {e}'

    return {'success': success, 'report': report}


def modify_jobs( cron, patterns=(), new_command=None, new_schedule=None):
    """ Modify ALL jobs matching by command all the pattern in the given tuple

        Returns a dictionary with result details

        The cron object (took by reference) will result modified in place
    """

    # schedule string must be cleaned of extra spaces:
    new_schedule = " ".join(new_schedule.split())

    success = True
    report  = []

    found = False
    for job in cron:

        if all(pattern in job.command for pattern in patterns):

            found   = True

            if new_command:
                try:
                    job.set_command(new_command)
                except Exception as e:
                    print(f"(crontool.modify_jobs) ERROR: {e}")
                    report.append( f'[{new_command}] ERROR with new_command: {e}' )
                    success = False

            if new_schedule:

                try:
                    job.setall(new_schedule)
                except Exception as e:
                    print(f"(crontool.modify_jobs) ERROR: {e}")
                    report.append( f'[{new_schedule}] error with new schedule: {e}' )
                    success = False

            if success:
                report.append( f"job modified: {job.slices} {job.command}" )

    return {'jobs_found': found, 'success': success, 'report': report}


def list_all_jobs():

    def list_job(job):
        schedule = str(job.slices)
        comment = job.comment if job.comment else "w/o comment"
        command = job.command
        print(f"{schedule:<20} | {comment:<20} | {command}")


    for job in get_cron():
        list_job(job)

