#!/usr/bin/env python
# Change the calendar in a UM ancillary file from Gregorian to 360 day
# Assuming monthly data, change to appropriate middle of month dates.

from um_fileheaders import *
import umfile, sys

print sys.argv[1]
f = umfile.UMFile(sys.argv[1], 'r+')

if f.fixhd[FH_CalendarType] == 1:
    f.fixhd[FH_CalendarType] = 2
    print "Changing from Gregorian to 360 day"
else:
    print "Already 360 day"
    sys.exit(0)

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
#     print "Validity time", ilookup[LBYR], ilookup[LBMON], ilookup[LBDAT], \
#         ilookup[LBHR], ilookup[LBMIN], ilookup[LBDAY]
#     print "Data time", ilookup[LBYRD], ilookup[LBMOND], ilookup[LBDATD], \
#         ilookup[LBHRD], ilookup[LBMIND], ilookup[LBDAYD]
#     print "LBTIM", ilookup[LBTIM]
    ilookup[LBDAT] = ilookup[LBDATD] = 16
    ilookup[LBHR] = ilookup[LBHRD] = 0
    ilookup[LBMIN] = ilookup[LBMIND] = 0
    ilookup[LBDAY] =  ilookup[LBDAYD] = 16 + (ilookup[LBMON]-1)*30
    if ilookup[LBTIM]%10==1:
        # Reset units part of value from 1 to 2.
        ilookup[LBTIM] += 1  # Crucial for CDMS.

f.close()
