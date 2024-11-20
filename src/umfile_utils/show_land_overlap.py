#!/usr/bin/env python

# Reconfiguration can give incorrect results if there are land points in the
# target grid but none have an adjacent land point on the global grid

# This script takes the full region regional mask and marks land points
# that don't have such neighbours by setting mask values to -1.

# Create a copy of the mask with disallowed corner points 

# Usage is show_land_overlap.py global_mask regional_mask disallowed

# Note that this isn't going to work for rotated grids.

# Martin Dix martin.dix@csiro.au

import numpy as np
import sys
import umfile
from um_fileheaders import *

file1 = sys.argv[1]
file2 = sys.argv[2]
file3 = sys.argv[3]

f = umfile.UMFile(file1)
g = umfile.UMFile(file2, 'r+')
h = umfile.UMFile(file3, 'w')

h.copyheader(g)
h.ilookup[:] = -99 # Used as missing value
h.rlookup[:] = np.fromstring(np.array([-99],h.int).tostring(),h.float)

def getfld(f):
    # Expecting only a single field
    ilookup = f.ilookup[0]

    # Check field name and data type.
    # Expecting stash code 1 0 30 LAND MASK
    if ilookup[ITEM_CODE] != 30:
        print "Variable is not land mask, stashcode is", ilookup[ITEM_CODE]
        sys.exit(1)
    if ilookup[DATA_TYPE] != 3:
        print "Variable is not expected logical type, code is", ilookup[DATA_TYPE]
        sys.exit(1)

    data = f.readfld(0)
    return data, ilookup, f.rlookup[0]

gmask, ilook1, rlook1 = getfld(f)
# Check that this file is global with starting point at -90,0
if ( not (rlook1[BDY] + rlook1[BZY] == -90. and 
        rlook1[BDX] + rlook1[BZX] == 0.) or 
     not (rlook1[BDY]*ilook1[LBROW] + rlook1[BZY] == 90. and 
        rlook1[BDX]*(ilook1[LBNPT]+1) + rlook1[BZX] == 360.)):
    raise Exception("First file is not global")

rmask, ilook2, rlook2 = getfld(g)

# Mask may be +-1 depending on compiler used in ancillary program.
# Coordinates of box centres
glat = rlook1[BZY] + rlook1[BDY]*np.arange(1,ilook1[LBROW]+1)
glon = rlook1[BZX] + rlook1[BDX]*np.arange(1,ilook1[LBNPT]+1)
rlat = rlook2[BZY] + rlook2[BDY]*np.arange(1,ilook2[LBROW]+1)
rlon = rlook2[BZX] + rlook2[BDX]*np.arange(1,ilook2[LBNPT]+1)

# Find the indices of the global box to the lower left of the regional grid box
ix = np.zeros(ilook2[LBNPT],np.int)
jy = np.zeros(ilook2[LBROW],np.int)

iarray = np.arange(len(glon))
for i in range(ilook2[LBNPT]):
    # Want index of the largest global lon that's <= rlon[i]
    # Don't need to check bounds because we know the TX region is inside
    ix[i] = iarray[glon - rlon[i] <= 0][-1]

jarray = np.arange(len(glat))
for j in range(ilook2[LBROW]):
    jy[j] = jarray[glat - rlat[j] <= 0][-1]

for j in range(ilook2[LBROW]):
    jj = jy[j]
    print j
    for i in range(ilook2[LBNPT]):
        if rmask[j,i]:
            ii = ix[i]
            if gmask[jj:jj+2,ii:ii+2].sum() == 0:
                rmask[j,i] = -1

# Now set up array of bad starting points, assuming 300x300
bad = np.zeros((ilook2[LBROW], ilook2[LBNPT]), np.int)
rmaskp = (rmask == 1)
rmaskm = (rmask == -1)
for j in range(ilook2[LBROW]-300):
    print j
    mp = rmaskp[j:j+300].sum(axis=0)
    mm = rmaskm[j:j+300].sum(axis=0)
    for i in range(ilook2[LBNPT]-300):
        # If no correct land points and some problem points it's a bad start
        if not np.any(mp[i:i+300]) and np.any(mm[i:i+300]):
            bad[j,i] = 1

g.writefld(rmask,0)
g.close()

h.ilookup[0,:] = ilook2[:]
h.rlookup[0,:] = rlook2[:]
h.writefld(bad, 0)
h.close()
