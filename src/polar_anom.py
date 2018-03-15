#!/usr/bin/env python

# Check whether fields at poles have any spurious zonal variation
# Exclude fields on u and v grids (v grid not at poles, u values at poles
# not used?)

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
from um_fileheaders import *
import umfile, stashvar

verbose = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'v')
    for opt in optlist:
        if opt[0] == '-v':
            verbose = True
except getopt.error:
    print "Usage: polar_anom [-v] ifile "
    sys.exit(2)

if args:
    ifile = args[0]
    
f = umfile.UMFile(ifile)

if not f.fieldsfile:
    print "Not a UM fieldsfile"
    sys.exit(1)

if f.fixhd[FH_HorizGrid] != 0:
    print "Error - not a global grid"
    sys.exit(1)

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    rlookup = f.rlookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break

    # Determine the grid from the zeroth latitude and longitude
    if not ( np.allclose(rlookup[BZY] + rlookup[BDY], -90.) and
             np.allclose(rlookup[BZX] + rlookup[BDX], 0.) ):
        if verbose:
            print "Skipping grid", ilookup[ITEM_CODE]
        continue

    data = f.readfld(k)

    if len(data.shape)==1:
        print "Shape error", ilookup[ITEM_CODE], data.shape
        continue

    anom_sp = data[0,:].max() - data[0,:].min()
    anom_np = data[-1,:].max() - data[-1,:].min()
    if verbose:
        print ilookup[ITEM_CODE], anom_sp.max(), anom_np.max()
    if anom_sp > 0 or anom_np > 0:
        print "Error - polar anomaly: %d %d %d" % (ilookup[ITEM_CODE], ilookup[LBLEV], k)
        print "   Absolute values", anom_sp, anom_np
        print "   Relative values", anom_sp/data[0].mean(), anom_np/data[-1].mean()

