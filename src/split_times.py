#!/usr/bin/env python

# Split a UM fieldsfiles into separate files for each valid time

# Usage is -i input -o output
# where output is used as a file prefix

import numpy as np
import getopt, sys
import umfile, collections, datetime
from um_fileheaders import *

def usage():
    print "Usage: split_times.py -i ifile -o output_prefix"
    sys.exit(2)

ifile = None
oprefix = None
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:o:')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-o':
            oprefix = opt[1]
except getopt.error:
    usage()

if not ifile or not oprefix:
    usage()

f = umfile.UMFile(ifile)

# First pass through to get the number of valid times
times=collections.defaultdict(int)
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    if ilookup[LBEGIN] == -99:
        break
    t = datetime.datetime(ilookup[LBYR], ilookup[LBMON], 
                          ilookup[LBDAT], ilookup[LBHR], 
                          ilookup[LBMIN], ilookup[LBDAY])
    times[t] += 1


for tout in sorted(times.keys()):
    ofile = oprefix + "." + tout.strftime('%Y%m%d%H%M')

    g = umfile.UMFile(ofile, "w")
    g.copyheader(f)
    g.ilookup[:] = -99 # Used as missing value
    g.rlookup[:] = np.fromstring(np.array([-99],g.int).tostring(),g.float)

    # Loop over all the fields, selecting those at time tout
    kout = 0
    for k in range(f.fixhd[FH_LookupSize2]):
        ilookup = f.ilookup[k]
        if ilookup[LBEGIN] == -99:
            break
        t = datetime.datetime(ilookup[LBYR], ilookup[LBMON], 
                              ilookup[LBDAT], ilookup[LBHR], 
                              ilookup[LBMIN], ilookup[LBDAY])
        if t == tout:
            g.ilookup[kout,:] = ilookup[:]
            g.rlookup[kout,:] = f.rlookup[k,:]
            s = f.readfld(k,raw=True)
            g.writefld(s, kout, raw=True)
            kout += 1

    # Set the header to be just large enough
    g.fixhd[FH_LookupSize2] = kout
    print "%d fields written to %s" % (kout, ofile)
    g.close()
