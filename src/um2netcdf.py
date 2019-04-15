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
import cdms2, cdtime, sys, getopt, datetime, argparse
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
parser.add_argument('-3', dest='usenc3', action='store_true', 
                    default=False, help="netCDF3 output (default netCDF4)")

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
 
# print "LEN(TIME)", len(time)

#  If output file exists then append to it, otherwise create a new file
try:
    file = cdms2.openDataset(args.ofile, 'r+')
    newv = file.variables[vname]
    newtime = newv.getTime()
except cdms2.error.CDMSError:
    if args.usenc3:
        # Force netCDF3 output
        cdms2.setNetcdfShuffleFlag(0)
        cdms2.setNetcdfDeflateFlag(0)
        cdms2.setNetcdfDeflateLevelFlag(0)
    file = cdms2.createDataset(args.ofile)
    file.history = "Created by um2netcdf.py."
    # Stop it creating the bounds_latitude, bounds_longitude variables
    cdms2.setAutoBounds("off")

    # By default get names like latitude0, longitude1
    # Need this awkwardness to get the variable/dimension name set correctly
    # Is there a way to change the name cdms uses after 
    # newlat = newgrid.getLatitude() ????
    newlat = file.createAxis('lat', grid.getLatitude()[:])
    newlat.standard_name = "latitude"
    newlat.axis = "Y"
    newlat.units = 'degrees_north'
    newlon = file.createAxis('lon', grid.getLongitude()[:])
    newlon.standard_name = "longitude"
    newlon.axis = "X"
    newlon.units = 'degrees_east'

    lev = var.getLevel()
    if len(lev) > 1:
        newlev = file.createAxis('lev', lev[:])
        for attr in ('standard_name', 'units', 'positive', 'axis'):
            if hasattr(lev,attr):
                setattr(newlev, attr, getattr(lev,attr))
    else:
        newlev = None
                                  
    newtime = file.createAxis('time', None, cdms2.Unlimited)
    newtime.standard_name = "time"
    newtime.units = time.units # "days since " + `baseyear` + "-01-01 00:00"
    newtime.setCalendar(time.getCalendar())
    newtime.axis = "T"
    
    if var.dtype == np.dtype('int32'):
        vtype = cdms2.CdInt
        missval = -2147483647
    else:
        vtype = cdms2.CdFloat
        missval = 1.e20
      
    if newlev:
        newv = file.createVariable(vname, vtype, (newtime, newlev, newlat, newlon))
    else:
        newv = file.createVariable(vname, vtype, (newtime, newlat, newlon))
    for attr in ("standard_name", "long_name", "units"):
        if hasattr(umvar, attr):
            newv.setattribute(attr, getattr(umvar,attr))
    if hasattr(var,'cell_methods'):
        # Change the time0 to time
        newv.cell_methods = 'time: '  + v.cell_methods.split()[1]
    newv.stash_section = var.stash_section[0]
    newv.stash_item = var.stash_item[0]
    newv.missing_value = missval
    newv._FillValue = missval

    try:
        newv.units = var.units
    except AttributeError:
        pass

file.history += "\n%s: Processed %s" % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M'), args.ifile)

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
        if var.shape[1] > 1:
            # Multi-level
            if (30201 <= item_code <= 30303) and mask:
                newv[k+i] = np.where( np.greater(heavyside[i], hcrit), var[i]/heavyside[0], newv.getMissing())
            else:
                newv[k+i] = var[i]
        else:
            newv[k+i] = var[i,0]

        newtime[k+i] = timevals[i]

file.close()
