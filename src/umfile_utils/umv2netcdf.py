#!/usr/bin/env python
# Convert UM fieldsfiles to netcdf
# This version works with rotated and/or variable grids
# Converts all fields in the file.

# This is really designed for masks and orography. It doesn't handle
# vertical or time dimensions yet.

# Martin Dix
# martin.dix@csiro.au

import sys, getopt, datetime
import netCDF4
import numpy as np
import umfile, stashvar
from um_fileheaders import *
from eqtoll import eqtoll

if len(sys.argv)==3:
    ifile = sys.argv[1]
    ofile = sys.argv[2]
else:
    print "Error - filename arguments expected"
    print "Usage: umv2netcdf.py input_file output_file"
    sys.exit(1)

f = umfile.UMFile(ifile)
if not f.fieldsfile:
    print "Input %s is not a UM fieldsfile" % ifile
    sys.exit(1)

# print "REAL HEADER", f.realhead
phi_pole = f.realhead[RC_PoleLat]
lambda_pole = f.realhead[RC_PoleLong]
dlon = f.realhead[RC_LongSpacing]
dlat = f.realhead[RC_LatSpacing]
lon0 = f.realhead[RC_FirstLong]
lat0 = f.realhead[RC_FirstLat]

vargrid = False
if hasattr(f,"rowdep") and hasattr(f,"coldep"):
    # Also need to check for missing values in real header?
    print "Variable resolution grid"
    vargrid = True

nc_out =  netCDF4.Dataset(ofile, "w", format="NETCDF3_CLASSIC")

if vargrid:
    nlon = f.coldep.shape[1]
    nlat = f.rowdep.shape[1]
else:
    nlon = f.inthead[IC_XLen]
    nlat = f.inthead[IC_YLen]

nc_out.createDimension('ix',nlon)
nc_out.createDimension('iy',nlat)

lon = nc_out.createVariable('lon',np.float32,['iy', 'ix'])
lon.standard_name = 'longitude'
lon.units = 'degrees_east'

lat = nc_out.createVariable('lat',np.float32,['iy', 'ix'])
lat.standard_name = 'latitude'
lat.units = 'degrees_north'

# Mask file passed CF Checker 2.0.3 2012-03-29
nc_out.Conventions = "CF-1.5"
nc_out.history = "%s: Created from %s using umv2netcdf.py" % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M'), ifile)

if not vargrid:
    lonarray = lon0 + np.arange(nlon)*dlon
    
# Should add a lon/lat bounds calculation here.
for j in range(nlat):
    if vargrid:
        phi, lam = eqtoll(f.rowdep[0,j],f.coldep[0],phi_pole,lambda_pole)
    else:
        phi, lam = eqtoll(lat0+j*dlat,lonarray,phi_pole,lambda_pole)
    lon[j,:] = lam
    lat[j,:] = phi

# eqotll returns longitudes in range (0, 360)
# Some plotting packages many have problems with regions crossing zero meridian
# so shift these back to -180 to 180 range
if lon[0,0] > lon[0,-1]:
    # region contains a 360 to 0 wrap around
    lon[:] = np.where(lon[:] > 180., lon[:] - 360., lon[:])

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN]
    if lbegin == -99:
        break

    data = f.readfld(k)
    
    var = stashvar.StashVar(ilookup[ITEM_CODE],ilookup[MODEL_CODE])
    newvar = nc_out.createVariable(var.name,np.float32,['iy','ix'])
    if var.standard_name:
        newvar.standard_name = var.standard_name
    newvar.long_name = var.long_name
    if var.units:
        newvar.units = var.units
    newvar.missing_value = -2.**30
    newvar[:] = data[:]

nc_out.close()
