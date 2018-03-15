#!/usr/bin/env python
# Change the initial and valid date of a UM dump file

# Change both the file header and the date header of each record.
# The latter may not be strictly necessary but it makes looking at file with
# xconv less confusing.

import getopt, sys
import umfile
from um_fileheaders import *

ifile = sys.argv[1]

f = umfile.UMFile(ifile, "r+")

print "Initial Time", f.fixhd[FH_DTYear], f.fixhd[FH_DTMonth], f.fixhd[FH_DTDay], \
      f.fixhd[FH_DTHour], f.fixhd[FH_DTMinute], f.fixhd[FH_DTSecond]

print "Valid Time", f.fixhd[FH_VTYear], f.fixhd[FH_VTMonth], f.fixhd[FH_VTDay], \
      f.fixhd[FH_VTHour], f.fixhd[FH_VTMinute], f.fixhd[FH_VTSecond]

s = raw_input('Enter year month day\n')
s = s.split()
year = int(s[0])
month = int(s[1])
day = int(s[2])

print "Using", year, month, day

f.fixhd[FH_DTYear] = f.fixhd[FH_VTYear] = year
f.fixhd[FH_DTMonth] = f.fixhd[FH_VTMonth] = month
f.fixhd[FH_DTDay] = f.fixhd[FH_VTDay] = day

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        # Ignore missing fields.
        break
    ilookup[LBYR] = year
    ilookup[LBMON] = month
    ilookup[LBDAT] = day
    ilookup[LBFT] = 0

f.close()
