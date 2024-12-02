# STASH files from Gregorian calendar runs may end up with duplicate times
# from restarting from dumps that aren't at exact month end.

# This script looks for such duplicates and removes them
# Uses a check sum to test whether the fields are truly identical.

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *
from zlib import adler32

verbose = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i::o:v')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-o':
            ofile = opt[1]
        elif opt[0] == '-v':
            verbose = True
except getopt.error:
    print "Usage: remove_stash_duplicates.py -i ifile -o ofile [-v]"
    sys.exit(2)

f = umfile.UMFile(ifile)
g = umfile.UMFile(ofile, "w")
g.copyheader(f)
g.ilookup[:] = -99 # Used as missing value
g.rlookup[:] = np.fromstring(np.array([-99],g.int).tostring(),g.float)

# Loop over all the fields, counting the number of prognostic fields
kout = 0
lookupset = set()
checksums = {}
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    if ilookup[LBEGIN] == -99:
        break

    s = f.readfld(k,raw=True)
    check = adler32(s)

    # Take a copy
    tmplookup = np.array(ilookup)
    tmplookup[LBEGIN] = tmplookup[NADDR] = 0
    key = tuple(tmplookup)
    if key in lookupset:
        print "Duplicate", k, ilookup[ITEM_CODE], ilookup[:4]
        if check != checksums[key]:
            raise Exception("Error - data mismatch %d", k)
    else:
        lookupset.add(key)
        checksums[key] = check
        g.ilookup[kout,:] = ilookup[:]
        g.rlookup[kout,:] = f.rlookup[k,:]
        g.writefld(s, kout, raw=True)
        kout += 1

# Set the header to be just large enough
g.fixhd[FH_LookupSize2] = kout
g.close()
