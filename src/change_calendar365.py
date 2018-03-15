#!/usr/bin/env python
# Change the calendar in a UM ancillary file from 360 day to Gregorian
# Assuming monthly data, change to appropriate middle of month dates.

from um_fileheaders import *
import umfile, sys

print sys.argv[1]
f = umfile.UMFile(sys.argv[1], 'r+')

if f.fixhd[FH_CalendarType] == 2:
    f.fixhd[FH_CalendarType] = 1
    print "Changing from 360 day to Gregorian"
else:
    print "Already Gregorian"
    sys.exit(0)

# Day no for 15th of month relative to 01-01
# dayno = [0, 14, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
#     print "Validity time", ilookup[LBYR], ilookup[LBMON], ilookup[LBDAT], \
#         ilookup[LBHR], ilookup[LBMIN], ilookup[LBDAY]
#     print "Data time", ilookup[LBYRD], ilookup[LBMOND], ilookup[LBDATD], \
#         ilookup[LBHRD], ilookup[LBMIND], ilookup[LBDAYD]
#     print "LBTIM", ilookup[LBTIM]
#     ilookup[LBDAT] = ilookup[LBDATD] = 15
#     ilookup[LBHR] = ilookup[LBHRD] = 0
#     ilookup[LBMIN] = ilookup[LBMIND] = 0
#     ilookup[LBDAY] =  ilookup[LBDAYD] = dayno[ilookup[LBMON]]
    if ilookup[LBTIM]%10 == 2:
        # Used by CDMS, though doesn't seem to be used by the model
        ilookup[LBTIM] -= 1

f.close()
