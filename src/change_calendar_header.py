#!/usr/bin/env python
# Change the calendar header field in a UM ancillary file.

from __future__ import print_function
from um_fileheaders import *
import umfile, sys, argparse

parser = argparse.ArgumentParser(description="Change calendar header in an ancillary file. If no calendar argument given it just prints the current value")
parser.add_argument('-c', dest='calendar',
                    help='Calendar to be set',
                    choices = ('gregorian', '360day', 'undefined'))

parser.add_argument('target', help='Ancillary file to change')
args = parser.parse_args()

f = umfile.UMFile(args.target, 'r+')

flag = {'gregorian':1, '360day':2, 'undefined':f.missval_i}
# Reverse dictionary
calendar = { i:c for c, i in flag.items()}

print("Original calendar value:", calendar[f.fixhd[FH_CalendarType]])

if args.calendar:
    f.fixhd[FH_CalendarType] = flag[args.calendar]
    print("New calendar value:", calendar[f.fixhd[FH_CalendarType]])

f.close()
