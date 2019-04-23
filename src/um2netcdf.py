#!/usr/bin/env python
# Convert UM monthly PP files to netcdf and concatenate
# Also works with daily files and optionally calculates the monthly average
# For min, max temperature, also need to match on cell_methods attribute
# Assume this starts with time0:

# Climate diagnostics on pressure levels are normally masked and need to be 
# corrected using the Heavyside function.
# nomask option turns this off (special case for runs where these were
# saved differently).

from __future__ import print_function
import cdms2, cdtime, sys, getopt, datetime, argparse, netCDF4, os
from cdms2 import MV
import numpy as np
import stashvar

def get_cell_methods(v):
    if hasattr(v,'cell_methods'):
        # Skip the time0: part
        # Are cell_methods ever used for any other property?
        return v.cell_methods.split()[1]
    else:
        return ""

def findvar(vars, section, item):
    for v in vars.values():
        if hasattr(v,'stash_section') and v.stash_section[0] == section and v.stash_item[0] == item:
            return v
    raise KeyError

parser = argparse.ArgumentParser(description="Convert selected variables from UM fieldsfile to netCDF.")
parser.add_argument('-i', dest='ifile', required=True, help='Input UM file')
parser.add_argument('-o', dest='ofile', required=True, help='Output netCDF file (appended to if it already exists)"')
parser.add_argument('-s', dest='stashcode', required=True, help=' section,item (Stash code for variable)')
parser.add_argument('-v', dest='vname', help='Override default variable name in output file')
parser.add_argument('-m', dest='cell_methods', help='cell_methods (required if there are multiple instances of a variable with different cell methods, e.g. ave, min and max temp)')
parser.add_argument('-a', dest='average', action='store_true', 
                    default=False, help="Calculate time average.")
parser.add_argument('-d', dest='forcedaily', action='store_true', 
                    default=False, help="Force daily time values (work around cdms error)")
parser.add_argument('--nomask', dest='nomask', action='store_true', 
                    default=False, help="Don't apply Heavyside function mask to pressure level fields.")
parser.add_argument('-k', dest='nckind', required=False, type=int,
                    default=4, help='specify kind of netCDF format for output file: 1 classic, 2 64-bit offset, 3 netCDF-4, 4 netCDF-4 classic model. Default 4', choices=[1,2,3,4])
parser.add_argument('--deflate', dest='deflate_level', required=False, type=int,
                    default=1, help='Compression level for netCDF4 output from 0 (none) to 9 (max). Default 1')
args = parser.parse_args()

mask = not args.nomask
stash_section = int(args.stashcode.split(',')[0])
stash_item = int(args.stashcode.split(',')[1])

try:
    d = cdms2.open(args.ifile)
except:
    print("Error opening file", args.ifile)
    usage()
    sys.exit(1)

var = None
print("Matching variables")
for vn in d.variables:
    v = d.variables[vn]
    # Need to check whether it really has a stash_item to skip coordinate variables
    
    # Note: need to match both item and section number
    if hasattr(v,'stash_item') and v.stash_item[0] == stash_item and v.stash_section[0] == stash_section:
        print(vn, get_cell_methods(v))
        # Need to cope with variables that have no cell methods so check
        # cell_methods is None 
        if args.cell_methods == None or (args.cell_methods != None and get_cell_methods(v) == args.cell_methods):
            # print "Cell match"
            if var:
                # Multiple match
                raise Exception("Multiple variables match")
            else:
                var = v
            
if not var:
    raise Exception("Variable not found %d %d" % ( stash_item, stash_section))

print(var)

grid = var.getGrid()
time = var.getTime()
timevals = np.array(time[:])
if args.forcedaily:
    # Work around cdms error in times
    for k in range(len(time)):
        timevals[k] = round(timevals[k],1)

item_code = var.stash_section[0]*1000 + var.stash_item[0]
umvar = stashvar.StashVar(item_code,var.stash_model[0])
if not args.vname:
    vname = umvar.name
print(vname, var[0,0,0,0])

hcrit = 0.5 # Critical value of Heavyside function for inclusion.
 
#  If output file exists then append to it, otherwise create a new file
# Different versions of netCDF4 module give different exceptions, so
# test for existence explicitly
exists = os.path.exists(args.ofile)
if exists:
    f = netCDF4.Dataset(args.ofile, 'r+')
    newv = f.variables[vname]
    newtime = f.variables['time']
else:
    ncformats = {1:'NETCDF3_CLASSIC', 2:'NETCDF3_64BIT', 
                 3:'NETCDF4', 4:'NETCDF4_CLASSIC'}
    f = netCDF4.Dataset(args.ofile,'w', format=ncformats[args.nckind])
    f.history = "Created by um2netcdf.py."

    f.createDimension('lat', len(grid.getLatitude()[:]))
    newlat = f.createVariable('lat',np.float32,('lat',))
    newlat.standard_name = "latitude"
    newlat.axis = "Y"
    newlat.units = 'degrees_north'
    newlat[:]= grid.getLatitude()[:]
    f.createDimension('lon', len(grid.getLongitude()[:]))
    newlon = f.createVariable('lon',np.float32,('lon',))
    newlon.standard_name = "longitude"
    newlon.axis = "X"
    newlon.units = 'degrees_east'
    newlon[:]= grid.getLongitude()[:]

    lev = var.getLevel()
    if len(lev) > 1:
        f.createDimension('lev', len(lev))
        newlev = f.createVariable('lev', np.float32, ('lev'))
        for attr in ('standard_name', 'units', 'positive', 'axis'):
            if hasattr(lev,attr):
                setattr(newlev, attr, getattr(lev,attr))
        newlev[:] = lev[:]
    else:
        newlev = None
                                  
    f.createDimension('time', None)
    newtime = f.createVariable('time', np.float64, ('time',))
    newtime.standard_name = "time"
    newtime.units = time.units # "days since " + `baseyear` + "-01-01 00:00"
    newtime.calendar = time.calendar
    newtime.axis = "T"
    
    if var.dtype == np.dtype('int32'):
        vtype = np.int32
        missval = -2147483647
    else:
        vtype = np.float32
        # UM missing value
        missval = -2.**30
      
    if newlev:
        newv = f.createVariable(vname, vtype, ('time', 'lev', 'lat', 'lon'), fill_value=missval, zlib=True, complevel=args.deflate_level)
    else:
        newv = f.createVariable(vname, vtype, ('time', 'lat', 'lon'), fill_value=missval, zlib=True, complevel=args.deflate_level)
    for attr in ("standard_name", "long_name", "units"):
        if hasattr(umvar, attr):
            setattr(newv,attr, getattr(umvar,attr))
    if hasattr(var,'cell_methods'):
        # Change the time0 to time
        newv.cell_methods = 'time: '  + v.cell_methods.split()[1]
    newv.stash_section = var.stash_section[0]
    newv.stash_item = var.stash_item[0]
    newv.missing_value = missval

    try:
        newv.units = var.units
    except AttributeError:
        pass

f.history += "\n%s: Processed %s" % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M'), args.ifile)

# Get appropriate file position
# Uses 360 day calendar, all with same base time so must be 30 days on.
k = len(newtime)
# float needed here to get the later logical tests to work properly
avetime = float(MV.average(timevals[:])) # Works in either case
if k>0:
    if args.average:
        #if newtime[-1] != (avetime - 30):
        # For Gregorian calendar relax this a bit
        # Sometimes get differences slightly > 31
        if not 28 <= avetime - newtime[-1] <= 31.5:
            raise Exception("Times not consecutive %f %f %f" % (newtime[-1], avetime, timevals[0]))
    else:
        if k > 1:
            # Need a better test that works when k = 1. This is just a
            # temporary workaround
            # For monthly data
            if 27 < newtime[-1] - newtime[-2] < 32:
                if not 27 < timevals[0] - newtime[-1] < 32:
                    raise Exception("Monthly times not consecutive %f %f " % (newtime[-1], timevals[0]))
            else:
                if not np.allclose( newtime[-1] + (newtime[-1]-newtime[-2]), timevals[0] ):
                    raise Exception("Times not consecutive %f %f " % (newtime[-1], timevals[0]))

if ( 30201 <= item_code <= 30288  or 30302 <= item_code <= 30303 ) and mask:
    # P LEV/UV GRID with missing values treated as zero.
    # Needs to be corrected by Heavyside fn
    try:
        heavyside = findvar(d.variables,30,301)
    except KeyError:
        raise Exception("Heavyside variable on UV grid required for pressure level masking of %d not found" % item_code)
if ( 30293 <= item_code <= 30298 ) and mask:
    # P LEV/T GRID
    try:
        heavyside = findvar(d.variables,30,304)
    except KeyError:
        raise Exception("Heavyside variable on T grid required for pressure level masking of %d not found" % item_code)

if args.average:
    newtime[k] = avetime
    if var.shape[1] > 1:
        newv[k] = MV.average(var[:],axis=0).astype(np.float32)
    else:
        newv[k] = MV.average(var[:],axis=0)[0].astype(np.float32)
else:
    for i in range(len(timevals)):
        newtime[k+i] = timevals[i]
        if var.shape[1] > 1:
            # Multi-level
            if (30201 <= item_code <= 30303) and mask:
                newv[k+i] = np.where( np.greater(heavyside[i], hcrit), var[i]/heavyside[0], var.getMissing())
            else:
                newv[k+i] = var[i]
        else:
            newv[k+i] = var[i]


f.close()
