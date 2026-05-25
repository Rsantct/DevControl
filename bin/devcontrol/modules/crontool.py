#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'DevControl'
# a very simple Home Automation app.

""" a cron tool
"""

import  subprocess
import  re
from    crontab  import CronTab
from    croniter import croniter


class Fmt:
    RED     = '\033[31m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    GREEN   = '\033[32m'
    GRAY    = '\033[90m'
    BOLD    = '\033[1m'
    END     = '\033[0m'


def schedules_match(cron_str_1, cron_str_2):
    """ croniter avoids problems with zero padding, spaces, etc
    """
    try:
        return croniter.expand(cron_str_1) == croniter.expand(cron_str_2)
    except Exception as e:
        print(f'{Fmt.RED}(crontool.schedules_match) "{cron_str_1}" "{cron_str_1}" {str(e)}{Fmt.END}')
        return False


def write_cron_prettified(cron, simulate=False):
    """ A replacement of cron.write() in order to prettify the crontab:
         - Zeropaded figures for minute, and hour
         - Comments are moved from the job line to the line above the job

        return:  the prettified crontrab string or '' if error
    """

    final_cron_str = ''

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

    except Exception as e:
        print(f'{Fmt.RED}(crontool.write_cron_prettified) formating ERROR: {e}{Fmt.END}')


    if not simulate:

        try:
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
            process.communicate(input=final_cron_str.encode())
            print(f'{Fmt.BLUE}(crontool.write_cron_prettified) crontab saved (with zero padding minutes and hours){Fmt.END}')

        except Exception as e:
            print(f'{Fmt.RED}(crontool.write_cron_prettified) dump ERROR: {e}{Fmt.END}')

    return final_cron_str


def get_cron():
    """ crontab from the current user
    """
    return CronTab(user=True)


def job_exists(cron=None, cron_slice='', cmd_patterns=()):
    """
        Check if there is a job whose command contains ALL the strings in 'patterns'.

        <patterns> can be a string or a tuple/list of strings.

        NOTICE: cron.find_comment(pattern) ONLY WORKS for trailing
                comments in the same line as the job itself,
                so we discard this method of searching.
    """

    if not cron:
        cron = get_cron()

    # single string --> tuple so that the loop can work
    if isinstance(cmd_patterns, str):
        cmd_patterns = (cmd_patterns,)

    result      = False
    slice_match = False
    cmd_match   = False

    for job in cron:

        if schedules_match(cron_slice, str(job.slices)):
            slice_match = True
        else:
            slice_match = False

        if all(cmd_p in job.command for cmd_p in cmd_patterns):
            cmd_match = True
        else:
            cmd_match = False

        result = slice_match and cmd_match

        if result:
            #print('slice  ', slice_match, cron_slice, '|', str(job.slices))
            #print('command', cmd_match, cmd_patterns, '|', job.command)
            #print()
            break

    return result


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
    if job_exists(cron, cron_slice=schedule, cmd_patterns=(command,)):

        print(f'{Fmt.GRAY}(crontool.add_new_job) EXIST: {schedule} {command}{Fmt.END}')
        report = 'job command exists, NOT added.'

    else:

        try:
            job = cron.new(command=command, comment=comment)
            job.setall(schedule)
            success = True
            print(f'{Fmt.BLUE}(crontool.add_new_job) ADDED: {schedule} {command}{Fmt.END}')

        except Exception as e:
            print(f'{Fmt.RED}(crontool.add_new_job) ERROR: {schedule} {command} {e}{Fmt.END}')
            report = f'ERROR: {e}'

    return {'success': success, 'report': report}


def modify_jobs( cron, cron_slice='', cmd_patterns=(), new_command=None, new_schedule=None):
    """ Modify ALL the jobs matching by command for all the given patterns

        Returns a dictionary with result details

        The cron object (took by reference) will result modified in place
    """

    # schedule string must be cleaned of extra spaces:
    new_schedule = " ".join(new_schedule.split())

    success = True
    report  = []

    found = False

    for job in cron:

        if all(cmd_pattern in job.command for cmd_pattern in cmd_patterns):

            if schedules_match(cron_slice, str(job.slices)):

                found   = True

                if new_command:
                    try:
                        job.set_command(new_command)
                    except Exception as e:
                        print(f'{Fmt.RED}(crontool.modify_jobs) ERROR: {e}{Fmt.END}')
                        report.append( f'[{new_command}] ERROR with new_command: {e}' )
                        success = False

                if new_schedule:

                    try:
                        job.setall(new_schedule)
                    except Exception as e:
                        print(f'{Fmt.RED}(crontool.modify_jobs) ERROR: {e}{Fmt.END}')
                        report.append( f'[{new_schedule}] error with new schedule: {e}' )
                        success = False

                if success:
                    report.append( f"job modified: {job.slices} {job.command}" )

    return {'jobs_found': found, 'success': success, 'report': report}


def remove_jobs(cron=None, patterns=(), matching_mode='all', verbose=False):
    """ Remove all jobs matching the given patterns.

        Returns the number of removed jobs
    """
    removed = 0

    if not patterns:
        return removed

    if not cron:
        cron = CronTab(user=True)

    if isinstance(patterns, str):
        patterns = (patterns,)

    initial_count = len(cron)

    # list(cron) makes a copy so that the list does not change
    # while iteration can remove a job
    for job in list(cron):

        if matching_mode == 'all':
            if all(p in job.command for p in patterns):
                cron.remove(job)
                removed += 1
                if verbose:
                    print(f'{Fmt.BLUE}Removing: {job.command}{Fmt.END}')

        elif matching_mode == 'any':
            if any(p in job.command for p in patterns):
                cron.remove(job)
                removed += 1
                if verbose:
                    print(f'{Fmt.BLUE}Removing: {job.command}{Fmt.END}')

    if verbose:
        if len(cron) < initial_count:
            print(f'{Fmt.BLUE}Removed {initial_count - len(cron)} jobs{Fmt.END}')
        else:
            print(f'{Fmt.BLUE}Not matching jobs{Fmt.END}')

    return removed


def list_all_jobs():

    def list_job(job):
        schedule = str(job.slices)
        comment = job.comment if job.comment else "w/o comment"
        command = job.command
        print(f"{schedule:<20} | {comment:<20} | {command}")


    for job in get_cron():
        list_job(job)

