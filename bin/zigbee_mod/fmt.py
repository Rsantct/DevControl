#!/usr/bin/env python3

class Fmt:
    """
    # Some nice ANSI formats for printouts formatting
    # CREDITS: https://github.com/adoxa/ansicon/blob/master/sequences.txt
    """

    BLACK           = '\033[30m'
    RED             = '\033[31m'
    GREEN           = '\033[32m'
    YELLOW          = '\033[33m'
    BLUE            = '\033[34m'
    MAGENTA         = '\033[35m'
    CYAN            = '\033[36m'
    WHITE           = '\033[37m'
    GRAY            = '\033[90m'

    BRIGHTBLACK     = '\033[90m'
    BRIGHTRED       = '\033[91m'
    BRIGHTGREEN     = '\033[92m'
    BRIGHTYELLOW    = '\033[93m'
    BRIGHTBLUE      = '\033[94m'
    BRIGHTMAGENTA   = '\033[95m'
    BRIGHTCYAN      = '\033[96m'
    BRIGHTWHITE     = '\033[97m'

    BOLD            = '\033[1m'
    UNDERLINE       = '\033[4m'
    BLINK           = '\033[5m'
    END             = '\033[0m'
