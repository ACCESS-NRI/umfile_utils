#!/usr/bin/env python
# Subset an ancillary file

# New region is specified by the indices of the lower left corner (x0,y0)
# and the extents nx, ny. 
# These are specified as arguments -x x0,nx -y y0,ny
# Note that (x0,y0) are 0 based indices

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

verbose = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:o:x:y:v')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-o':
            ofile = opt[1]
        elif opt[0] == '-v':
            verbose = True
        elif opt[0] == '-x':
            x0 = int(opt[1].split(',')[0])
            nx = int(opt[1].split(',')[1])
        elif opt[0] == '-y':
            y0 = int(opt[1].split(',')[0])
            ny = int(opt[1].split(',')[1])
except getopt.error:
    print "Usage: subset_ancillary -i ifile -o ofile -x x0,nx -y y0,ny"
    sys.exit(2)

# Section to take
if verbose:
    print "Section", x0, y0, nx, ny

f = umfile.UMFile(ifile)

g = umfile.UMFile(ofile, "w")
g.copyheader(f)

# Change the grid values in the output header to match the chosen origin and
# size
g.inthead[IC_XLen] = nx
g.inthead[IC_YLen] = ny
lat0 = f.realhead[RC_FirstLat] +  f.realhead[RC_LatSpacing]*y0
lon0 = f.realhead[RC_FirstLong] +  f.realhead[RC_LongSpacing]*x0
g.realhead[RC_FirstLat] = lat0
g.realhead[RC_FirstLong] = lon0
g.realhead[RC_PoleLong] = 180. # For SH regions - perhaps should be an option?

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    npts = ilookup[LBNPT]
    nrows = ilookup[LBROW]
    lat0 = f.rlookup[k,BZY] +  f.rlookup[k,BDY]*y0
    lon0 = f.rlookup[k,BZX] +  f.rlookup[k,BDX]*x0

    if verbose:
        print "Field", k, ilookup[ITEM_CODE]
        print "GRID SIZE", ilookup[LBROW], ilookup[LBNPT]
        print "GRID origin", f.rlookup[k,BZY], f.rlookup[k,BZX]
        print "GRID first pt", f.rlookup[k,BZY] + f.rlookup[k,BDY], f.rlookup[k,BZX] + f.rlookup[k,BDX]
        print "NEWGRID origin", lat0, lon0
        print "NEWGRID first pt", lat0 + f.rlookup[k,BDY], lon0 + f.rlookup[k,BDX]
    if lbegin == -99:
        break

    # Set modified output grid for this field
    g.ilookup[k,LBLREC] = nx*ny
    g.ilookup[k,LBROW] = ny
    g.ilookup[k,LBNPT] = nx
    # Set polar lon to 180 for SH grid.
    g.rlookup[k,BPLON] = 180.
    g.rlookup[k,BZY] = lat0
    g.rlookup[k,BZX] = lon0

    data = f.readfld(k)

    # Select the new region
    if not (y0+ny <= nrows and x0+nx <= npts):
        print "ERROR"
        print "Input grid size", npts, nrows
        print "Requested extent %d:%d, %d:%d" % (x0, x0+nx, y0, y0+ny)
        raise Exception("Requested grid is not a subset of source grid.")

    newdata = data[y0:y0+ny,x0:x0+nx]

    g.writefld(newdata,k)

g.close()
