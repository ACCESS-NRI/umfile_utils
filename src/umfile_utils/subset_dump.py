#!/usr/bin/env python

# Subset a UM dump file

# Intended to get a TC model initial dump file from a full region reconfigured
# initial dump.

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
stashmaster = None
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
    print "Usage: subset_dump -i ifile -o ofile -x x0,nx -y y0,ny"
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

# Need to start by setting up the mask field because it's required by the 
# fields packed to land points
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    if ilookup[ITEM_CODE] == 30:
        data = f.readfld(k)
        g.mask = np.array(data[y0:y0+ny,x0:x0+nx])
        g.nland = np.sum(g.mask!=0)
        g.inthead[IC_NumLandPoints] = g.nland
if g.mask is None:
    raise Exception("Land sea mask missing in input")

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    npts = ilookup[LBNPT]
    nrows = ilookup[LBROW]
    lat0 = f.rlookup[k,BZY] +  f.rlookup[k,BDY]*y0
    # For zonal mean fields BDX=360 which messes up this calculation.
    # Instead don't set it and pick up the value from the previous field
    if not f.rlookup[k,BDX]==360:
        lon0 = f.rlookup[k,BZX] +  f.rlookup[k,BDX]*x0

    if verbose:
        print k, ilookup[ITEM_CODE]
        print "GRID SIZE", ilookup[LBROW], ilookup[LBNPT]
        print "GRID origin", f.rlookup[k,BZY], f.rlookup[k,BZX]
        print "GRID first pt", f.rlookup[k,BZY] + f.rlookup[k,BDY], f.rlookup[k,BZX] + f.rlookup[k,BDX]
        print "NEWGRID origin", lat0, lon0
        print "NEWGRID first pt", lat0 + f.rlookup[k,BDY], lon0 + f.rlookup[k,BDX]
    if lbegin == -99:
        break

    # Check whether this variable is on the V grid
    # If so, f.rlookup[k,BZY] + 0.5*f.rlookup[k,BDY] = f.realhead[RC_FirstLat]
    # For U and P grids
    # f.rlookup[k,BZY] + f.rlookup[k,BDY] = f.realhead[RC_FirstLat]
    # 0.6 factor allows for roundoff
    vgrid = f.realhead[RC_FirstLat] - f.rlookup[k,BZY] < 0.6*f.rlookup[k,BDY]
    if vgrid:
        nyout = ny-1
    else:
        nyout = ny

    # Set modified output grid for this field
    # Using min(nx,npts) handles the zonal mean fields with npts=1
    g.ilookup[k,LBLREC] = min(nx,npts)*nyout
    # Land packed fields have npts = nrows = 0
    g.ilookup[k,LBROW] = min(nyout,nrows) 
    g.ilookup[k,LBNPT] = min(nx,npts)
    g.rlookup[k,BZY] = lat0
    g.rlookup[k,BZX] = lon0

    data = f.readfld(k)

    # Skip this test for fields packed as land
    packing = [0, ilookup[LBPACK]%10, ilookup[LBPACK]//10 % 10,
               ilookup[LBPACK]//100 % 10, ilookup[LBPACK]//1000 % 10,
               ilookup[LBPACK]//10000]
    if verbose:
        print "Packing", packing

    # Select the new region
    # if packing[2] != 2 and not (y0+ny <= nrows and x0+nx <= npts):
    #     print "ERROR: record %d field: %d" % (k, ilookup[ITEM_CODE])
    #     print "Input grid size", npts, nrows
    #     print "Requested extent %d:%d, %d:%d" % (x0, x0+nx, y0, y0+ny)
    #     raise Exception("Requested grid is not a subset of source grid.")

    if npts==1: # Zonal mean
        newdata = data[y0:y0+nyout]
    else:
        newdata = data[y0:y0+nyout,x0:x0+nx]

    g.writefld(newdata,k)

g.close()
