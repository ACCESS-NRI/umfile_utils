#!/usr/bin/env python

# Apply a perturbation to initial condition.
# Note that this works in place.

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

amplitude = 0.01
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'a:')
    for opt in optlist:
        if opt[0] == '-a':
            amplitude = float(opt[1])
except getopt.error:
    print "Usage: perturbIC [-a amplitude] file"
    sys.exit(2)

ifile = args[0]

f = umfile.UMFile(ifile, 'r+')

# Set up theta perturbation.
nlon = f.inthead[IC_XLen]
nlat = f.inthead[IC_YLen]
# Same at each level so as not to upset vertical stability
# Should really set the seed.
perturb = amplitude * (2.*np.random.random(nlon*nlat).reshape((nlat,nlon)) - 1.)
# Set poles to zero
perturb[0] = 0.
perturb[-1] = 0.

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] == 4:
        a = f.readfld(k)
        # Note that using += ensures the datatype of a doesn't change
        # (in case it's float32)
        a += perturb
        f.writefld(a,k)

f.close()
