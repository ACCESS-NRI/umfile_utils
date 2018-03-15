#!/usr/bin/env python
# Change the calendar in a UM ancillary file from Gregorian to 360 day
# Assuming monthly data, change to appropriate middle of month dates.

from um_fileheaders import *
import umfile, sys

f = umfile.UMFile(sys.argv[1], 'r')

if f.fixhd[FH_CalendarType] == 1:
    print "Gregorian"
elif f.fixhd[FH_CalendarType] == 2:
    print "360 day"
elif f.fixhd[FH_CalendarType] == f.missval_i:
    print "Not set"
else:
    print "Unexpected calendar value", f.fixhd[FH_CalendarType]
