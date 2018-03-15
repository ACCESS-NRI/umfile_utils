#!/usr/bin/env python

# Extract the regular grid part from a variable grid UM file

# The regular region on the U and V grids is one point smaller than
# the P grid.

# In a variable resolution dump file there's no information to tell
# whether a field is on the U, V or P grid.
# This can only come from reading the STASHmaster file, so must give suitable
# one as an argument.

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *
import read_stashmaster

def usage():
    print "Usage: umv2reg [-v] -i ifile -o ofile -s STASHmaster"
    sys.exit(2)

verbose = False
ifile = None
ofile = None
stashmaster = None
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:o:s:v')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-o':
            ofile = opt[1]
        elif opt[0] == '-s':
            stashmaster = opt[1]
        elif opt[0] == '-v':
            verbose = True
except getopt.error:
    usage()

if not (ifile and ofile and stashmaster):
    print "Missing arguments"
    usage()
    
stashd = read_stashmaster.read_stash(stashmaster)

f = umfile.UMFile(ifile)

phi_pole = f.realhead[RC_PoleLat]
lambda_pole = f.realhead[RC_PoleLong]
dlon = f.realhead[RC_LongSpacing]
dlat = f.realhead[RC_LatSpacing]
lon0 = f.realhead[RC_FirstLong]
lat0 = f.realhead[RC_FirstLat]

# Variable grid file has dlon, dlat = missing value
if not dlon == dlat == lon0 == lat0 == f.missval_r:
    raise Exception("Input file does not use variable grid")

if not (hasattr(f,"rowdep") and hasattr(f,"coldep")):
    raise Exception("Input file missing variable grid lat/lon")

nlon = f.coldep.shape[1]
nlat = f.rowdep.shape[1]

# Find the regular grid spacing
# Ancillary file may only have P grid values
# If U and V values are present they're half a grid point to N and E.
deltalon = f.coldep[0,1:] - f.coldep[0,:-1]
deltalat = f.rowdep[0,1:] - f.rowdep[0,:-1]

dlon = deltalon.min()
dlat = deltalat.min()
# Find first and last grid indices with this spacing
indices = np.arange(nlon)[abs(deltalon-dlon) < 2e-5]
lon1 = indices[0]  # Start of grid, first point s.t. lon(i+1) - lon(i) = dlon
lon2 = indices[-1] + 1
nx = lon2 - lon1 + 1

indices = np.arange(nlat)[abs(deltalat-dlat) < 2e-5]
lat1 = indices[0]  # Start of grid, first point s.t. lat(i+1) - lat(i) = dlat
lat2 = indices[-1] + 1
ny = lat2 - lat1 + 1

# Recalculate the regular grid spacing using the full range for more accuracy
# (necessary for 32 bit files).
dlon =  (f.coldep[0,lon2]-f.coldep[0,lon1]) / (lon2-lon1)
dlat =  (f.rowdep[0,lat2]-f.rowdep[0,lat1]) / (lat2-lat1)
# Get sensibly rounded values
dlon = round(dlon.min(),6)
dlat = round(dlat.min(),6)
print "Grid spacing", dlon, dlat
print "Regular region", f.coldep[0,lon1], f.coldep[0,lon2], f.rowdep[0,lat1], f.rowdep[0,lat2]
print "Regular grid size", nx, ny
# If this is done correctly it should be symmetrical
if not (nlon-1-lon2 == lon1 and nlat-1-lat2 == lat1):
    raise Exception("Regular resolution region is not symmetrical")

g = umfile.UMFile(ofile, "w")
g.copyheader(f)

# No row and column depedent constants in the regular grid file
g.fixhd[FH_RowDepCStart:FH_ColDepCSize2+1] = g.missval_i
# Change the grid values in the output header to match the chosen origin and
# size
g.inthead[IC_XLen] = nx
g.inthead[IC_YLen] = ny
g.realhead[RC_FirstLat] = f.rowdep[0,lat1] - dlat  # This is "zeroth" point
g.realhead[RC_FirstLong] = f.coldep[0,lon1] - dlon
g.realhead[RC_LongSpacing] = dlon
g.realhead[RC_LatSpacing] = dlat

# Start by trying to read the land-sea mask, field 30
try:
    f.getmask()
    # Mask on the regular region
    g.mask = f.mask[lat1:lat1+ny,lon1:lon1+ny]
except umfile.packerr:
    pass

# Loop over all the fields
kout = 0
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        # End of data
        break
    if ilookup[LBCODE] == f.missval_i:
        # There are some files with variables code in headers but much
        # of the rest of the data missing
        print "Header data missing", ilookup[ITEM_CODE]
        continue
    if verbose:
        print k, ilookup[ITEM_CODE]
    npts = ilookup[LBNPT]
    nrows = ilookup[LBROW]
    # Look at the STASHmaster grid value for this item code to check which
    # grid it's on. There's no way to tell purely from the variable grid
    # fieldsfile.
    gridcode = stashd[ilookup[ITEM_CODE]]['grid']
    if gridcode in (1,2,3,21,22):
        # theta points, including packed to land or ocean
        # ozone grid also (same as theta?)
        lon0 = g.realhead[RC_FirstLong]
        lat0 = g.realhead[RC_FirstLat]
        nxv = nx
        nyv = ny
    elif gridcode == 18:
        # U
        lon0 = f.coldep[1,lon1] - dlon
        lat0 = g.realhead[RC_FirstLat]
        nxv = nx-1
        nyv = ny
    elif gridcode == 19:
        # U
        lon0 = g.realhead[RC_FirstLong]
        lat0 = f.rowdep[1,lat1] - dlat
        nxv = nx
        nyv = ny-1
    else:
        print "Skipping variable %d with grid %d" % (ilookup[ITEM_CODE], gridcode)
        continue

    # Currently have a copy of the input header
    # Set modified output grid for this field
    g.ilookup[kout,LBCODE] = 101  # Standard rotated grid
    
    # Could set this in the writing routing from the array size?
    g.ilookup[kout,LBROW] = nyv
    g.ilookup[kout,LBNPT] = nxv
    g.ilookup[kout,LBLREC] = nxv*nyv
    g.rlookup[kout,BZY] = lat0
    g.rlookup[kout,BZX] = lon0
    g.rlookup[kout,BDY] = dlat
    g.rlookup[kout,BDX] = dlon

    data = f.readfld(k)
    newdata = data[lat1:lat1+nyv,lon1:lon1+nxv]
    g.writefld(newdata,kout)
    kout += 1

g.close()
