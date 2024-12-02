# Replace the Australian part of the GLOBE30 data with data from 
# aus_dem_9s (averaged to same 30 sec resolution)
# Note that this modifies the file in place

# This file just has a single variable with code 0

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *
import cdms2
from cdms2 import MV2

ifile = "GLOBE30_aus.orog"
ncfile = "aus_dem_30s.nc"
ncvarname = "height"

d = cdms2.open(ncfile)
ncvar = d.variables[ncvarname]

f = umfile.UMFile(ifile, "r+")

# Start of data
dstart = f.fixhd[FH_DataStart]

# Orography uses zero over oceans rather than missing value
arr = MV2.array(ncvar[:])
MV2.set_fill_value(arr,0)
arr = MV2.filled(arr)

# GLOBE30 goes starts at 0E, 90N, resolution 1/120th
# aus_dem also N to S
lat = ncvar.getLatitude()
lon = ncvar.getLongitude()
lat0 = lat[0]
lon0 = lon[0]
ioff = int(round(lon[0]*120))
joff = int(round((90-lat0)*120))
j12s = int(round((90+12)*120))
i128e = 128*120
nlat = len(lat)
nlon = len(lon)

print "JOFF", joff, j12s

# Loop over all the fields
kout = 0
kount = dstart-1 # dstart is index rather than offset
k = 0  # Single field
a = f.readfld(k)
print "SHAPES", a.shape,  a[joff:joff+nlat,ioff:ioff+nlon].shape, arr.shape
# For first part of array, to 12 S, include only a region
# from 128 to 144E so only Australia gets changed
nregion = j12s - joff
lonstart = i128e - ioff
print "SHAPES", a[joff:j12s,i128e:i128e+1920].shape, arr[:nregion,lonstart:lonstart+1920].shape
a[joff:j12s,i128e:i128e+1920] = arr[:nregion,lonstart:lonstart+1920]
print "SHAPES", a[j12s:joff+nlat,ioff:ioff+nlon].shape, arr[nregion:].shape
a[j12s:joff+nlat,ioff:ioff+nlon] = arr[nregion:]

f.writefld(a,k)

f.close()
