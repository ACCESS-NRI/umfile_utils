#!/usr/bin/env python
# Reconfiguration can give incorrect results if there are land points in the
# target grid but none in the matching region on the parent grid
# (even if there is land elsewhere).
# Here check for this 
# Usage is check_land_overlap.py global_mask  regional_mask

# Note that this isn't going to work for rotated grids.

# Martin Dix martin.dix@csiro.au

import numpy as np
import sys
import umfile
from um_fileheaders import *

file1 = sys.argv[1]
file2 = sys.argv[2]

f = umfile.UMFile(file1)
g = umfile.UMFile(file2)

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

data1, ilook1, rlook1 = getfld(f)
# Check that this file is global with starting point at -90,0
gridtype = None
if ( np.isclose(rlook1[BDY] + rlook1[BZY], -90.) and 
     np.isclose(rlook1[BDX] + rlook1[BZX], 0.) and 
     np.isclose(rlook1[BDY]*ilook1[LBROW] + rlook1[BZY], 90.) and 
     np.isclose(rlook1[BDX]*(ilook1[LBNPT]+1) + rlook1[BZX],360.) ):
    gridtype = 'ND'
elif ( np.isclose(rlook1[BDY]*0.5 + rlook1[BZY], -90.) and 
       np.isclose(rlook1[BDX]*0.5 + rlook1[BZX], 0.) and
       np.isclose(rlook1[BDY]*(ilook1[LBROW]+0.5) + rlook1[BZY], 90.) and 
       np.isclose(rlook1[BDX]*(ilook1[LBNPT]+0.5) + rlook1[BZX], 360.) ):
    gridtype = 'EG'
else:
    raise Exception("First file is not global")

data2, ilook2, rlook2 = getfld(g)

# Mask may be +-1 depending on compiler used in ancillary program.
nland2 = (data2 != 0).sum()
if nland2 == 0:
    # No problem
    print "No land in LAM mask so OK"
else:
    # Coordinates of box centres
    lat1 = rlook2[BDY] + rlook2[BZY]
    lon1 = rlook2[BDX] + rlook2[BZX]
    lat2 = rlook2[BDY]*ilook2[LBROW] + rlook2[BZY]
    lon2 = rlook2[BDX]*ilook2[LBNPT] + rlook2[BZX]

    # Find the global coordinates that fit inside this box
    i1 = int(np.ceil(lon1 / rlook1[BDX]))
    i2 = int(np.ceil(lon2 / rlook1[BDX]))
    j1 = int(np.ceil((lat1+90.) / rlook1[BDY]))
    j2 = int(np.ceil((lat2+90.) / rlook1[BDY]))

    nland1 = (data1[j1:j2,i1:i2]!=0).sum()

    if nland1 != 0:
        print "OK - land points exist in global subset"
    else:
        print "Error - no overlapping land points"
        # Now search for land in each direction
        # Set defaults in case land isn't found in that direction
        i1off = -9999
        j1off = -9999
        i2off = 9999
        j2off = 9999
        for i in range(i1-1,-1,-1):
            if (data1[j1:j2,i]!=0).sum() != 0:
                i1off = i
                break
        for i in range(i2,ilook1[LBNPT]):
            if (data1[j1:j2,i]!=0).sum() != 0:
                i2off = i
                break
        for j in range(j1-1,-1,-1):
            if (data1[j,i1:i2]!=0).sum() != 0:
                j1off = j
                break
        for j in range(j2,ilook1[LBROW]):
            if (data1[j,i1:i2]!=0).sum() != 0:
                j2off = j
                break

        print "Possible fixes"
        # These corrections are on global grid, so need to convert
        # to LAM
        shift_E = int(np.ceil((i2off + 1 - i2)*rlook1[BDX]/rlook2[BDX]))
        shift_W = int(np.ceil((i1 - i1off)*rlook1[BDX]/rlook2[BDX]))
        shift_N = int(np.ceil((j2off + 1 - j2)*rlook1[BDY]/rlook2[BDY]))
        shift_S = int(np.ceil((j1 - j1off)*rlook1[BDY]/rlook2[BDY]))
        print "  Shift grid %d points E" % shift_E
        print "  Shift grid %d points W" % shift_W
        print "  Shift grid %d points N" % shift_N
        print "  Shift grid %d points S" % shift_S

        # Find the minimum
        shifts = [shift_E, shift_W, shift_N, shift_S]
        i = np.argmin(shifts)
        direction = ['E', 'W', 'N', 'S'][i]
        print "Recommended shift is %d points %s" % (shifts[i], direction)

        # Full region ancillary files are start at 60 E, 45 s
        # 1426 x 916 points
        # ~yix/share/umlam2/ACCESS/ANCIL/TXLAPS0.11/qrparm.mask 
        # 4km 4320 x 2800, starting at 60E, 45 S. Spacing 0.036
        # Current coordinates
        # Existing offsets
        ioff = int(round((lon1-60)/rlook2[BDX],0))
        joff = int(round((lat1+45)/rlook2[BDY],0))

        # print "Offsets in current file", ioff, joff
        if direction == 'E':
            ioff += shift_E
        elif direction == 'W':
            ioff -= shift_W
        elif direction == 'N':
            joff += shift_N
        elif direction == 'S':
            joff -= shift_S

        print "Rerun subset_ancillary with offsets", ioff, joff
