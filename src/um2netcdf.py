#!/usr/bin/env python
# Convert UM monthly PP files to netcdf and concatenate
# Also works with daily files and optionally calculates the monthly average
# For min, max temperature, also need to match on cell_methods attribute
# Assume this starts with time0:

# Climate diagnostics on pressure levels are normally masked and need to be 
# corrected using the Heavyside function.
# nomask option turns this off (special case for runs where these were
# saved differently).

import cdms2, cdtime, sys, getopt, datetime
from cdms2 import MV
import numpy as np
import stashvar

class error(Exception):
    pass

def usage():
    print "Usage: um2netcdf.py [-a] [-4] -i ifile -o ofile -s section,item [-m cell_methods] [--nomask] [-v vname]"

def help():
    usage()
    print " -i input_file (Met Office fieldsfile format)"
    print " -o output file (netcdf, appended to if it already exists)"
    print " -s section,item (Stash code for variable)"
    print " -m cell_methods (required if there are multiple instances of a variable with different cell methods, e.g. ave, min and max temp)"
    print " -a (calculate time average)"
    print " -d Force daily time values (work around cdms error)"
    print " -v vname Override default variable name in output file"
    print " -4 netCDF4 output (default netCDF3)"

def get_cell_methods(v):
    if hasattr(v,'cell_methods'):
        # Skip the time0: part
        # Are cell_methods ever used for any other property?
        return v.cell_methods.split()[1]
    else:
        return ""

# vname is the name to use in the output file
cell_methods = None
average = False
mask = True
ifile = None
ofile = None
forcedaily = False
vname = None
usenc4 = False
try:
    opts, args = getopt.getopt(sys.argv[1:], '4adhi:o:m:s:v:',['nomask'])
    for o, a in opts:
        if o == '-4':
            usenc4 = True
        elif o == '-a':
            average = True
        elif o == '-h':
            help()
            sys.exit(0)
        elif o == '-d':
            forcedaily = True
        elif o == '-i':
            ifile = a
        elif o == '-m':
            cell_methods = a
        elif o == '--nomask':
            mask = False
        elif o == '-o':
            ofile = a
        elif o == '-v':
            vname = a
        elif o == '-s':
            # STASH section, item
            stash_section = int(a.split(',')[0])
            stash_item = int(a.split(',')[1])
except getopt.error:
    usage()
    sys.exit(1)

try:
    d = cdms2.open(ifile)
except:
    print "Error opening file", ifile
    usage()
    sys.exit(1)

var = None
print "Matching variables"
for vn in d.variables:
    v = d.variables[vn]
    # Need to check whether it really has a stash_item to skip coordinate variables
    
    # Note: need to match both item and section number
    if hasattr(v,'stash_item') and v.stash_item[0] == stash_item and v.stash_section[0] == stash_section:
        print vn, get_cell_methods(v)
        # Need to cope with variables that have no cell methods so check
        # cell_methods is None 
        if cell_methods == None or (cell_methods != None and get_cell_methods(v) == cell_methods):
            # print "Cell match"
            if var:
                # Multiple match
                raise error, "Multiple variables match"
            else:
                var = v
            
if not var:
    raise error, "Variable not found %d %d" % ( stash_item, stash_section)

print var

grid = var.getGrid()
time = var.getTime()
timevals = np.array(time[:])
if forcedaily:
    # Work around cdms error in times
    for k in range(len(time)):
        timevals[k] = round(timevals[k],1)

item_code = var.stash_section[0]*1000 + var.stash_item[0]
umvar = stashvar.StashVar(item_code,var.stash_model[0])
if not vname:
    vname = umvar.name
print vname, var[0,0,0,0]

hcrit = 0.5 # Critical value of Heavyside function for inclusion.
 
# print "LEN(TIME)", len(time)

#  If output file exists then append to it, otherwise create a new file
try:
    file = cdms2.openDataset(ofile, 'r+')
    newv = file.variables[vname]
    newtime = newv.getTime()
except cdms2.error.CDMSError:
    if not usenc4:
        # Force netCDF3 output
        cdms2.setNetcdfShuffleFlag(0)
        cdms2.setNetcdfDeflateFlag(0)
        cdms2.setNetcdfDeflateLevelFlag(0)
    file = cdms2.createDataset(ofile)
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

file.history += "\n%s: Processed %s" % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M'), ifile)

# Get appropriate file position
# Uses 360 day calendar, all with same base time so must be 30 days on.
k = len(newtime)
# float needed here to get the later logical tests to work properly
avetime = float(MV.average(timevals[:])) # Works in either case
if k>0:
    if average:
        #if newtime[-1] != (avetime - 30):
        # For Gregorian calendar relax this a bit
        # Sometimes get differences slightly > 31
        if not 28 <= avetime - newtime[-1] <= 31.5:
            raise error, "Times not consecutive %f %f %f" % (newtime[-1], avetime, timevals[0])
    else:
        if k > 1:
            # Need a better test that works when k = 1. This is just a
            # temporary workaround
            # For monthly data
            if 27 < newtime[-1] - newtime[-2] < 32:
                if not 27 < timevals[0] - newtime[-1] < 32:
                    raise error, "Monthly times not consecutive %f %f " % (newtime[-1], timevals[0])
            else:
                if not np.allclose( newtime[-1] + (newtime[-1]-newtime[-2]), timevals[0] ):
                    raise error, "Times not consecutive %f %f " % (newtime[-1], timevals[0])

if (30201 <= item_code <= 30303) and mask:
    # P LEV/UV GRID with missing values treated as zero.
    # Needs to be corrected by Heavyside fn
    heavyside = d.variables['psag']
    # Check variable code as well as the name.
    if heavyside.stash_item[0] != 301 or heavyside.stash_section[0] != 30:
        raise error, "Heavyside variable code mismatch"

if average:
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
