#!/usr/bin/env python

# List of valid data times in a file

from um_fileheaders import *
import umfile, sys, collections, datetime

f = umfile.UMFile(sys.argv[1])

times=collections.defaultdict(int)

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    if ilookup[LBEGIN] == -99:
        break
    if ilookup[LBREL] >= 3:
        # Second field introduced from vn 8.1
        t = datetime.datetime(ilookup[LBYR], ilookup[LBMON], 
                              ilookup[LBDAT], ilookup[LBHR], 
                              ilookup[LBMIN], ilookup[LBSEC])
    else:
        t = datetime.datetime(ilookup[LBYR], ilookup[LBMON], 
                              ilookup[LBDAT], ilookup[LBHR], 
                              ilookup[LBMIN], 0)
    times[t] += 1

print "Valid_times",
for t in sorted(times.keys()):
    print t.strftime('%Y%m%d%H%M'),
print

if len(set(times.values())) > 1:
    print "Warning - not all times have same number of fields"
