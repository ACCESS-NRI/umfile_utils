#!/usr/bin/env python
# Convert a UM timeseries fields file to a netcdf file.
# In general a single file can contain variables on multiple usage
# domains, so should allow for this when generating the netcdf dimensions.
# Also in general could need multiple time dimensions, though these can't
# be unlimited.
# Here assume that everything is defined at the same times.
# This is checked for,

# Rachel's files have two domains, surface and atmospheric. However, the
# atmospheric domain may have different coordinates for u, v and T grids.

# Need to be sure it works for different file restarting frequencies

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys, time
import stashvar
from um_fileheaders import *
import umfile
import netCDF4
import cdtime

def usage():
    print "Usage: um_timeseries.py -i ifile -o ofile [-v]"
    sys.exit(2)

verbose = False
ifile = None
ofile = None
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:o:v')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-o':
            ofile = opt[1]
        elif opt[0] == '-v':
            verbose = True
except getopt.error:
    usage()

if not ifile or not ofile:
    usage()

f = umfile.UMFile(ifile)
d = netCDF4.Dataset(ofile,"w",format='NETCDF3_CLASSIC')

if verbose:
    f.print_fixhead()

if verbose:
    print "REAL HEADER", f.realhead

# Loop over all the loookup headers to set up the netcdf file.
# Check each variable is defined on the same times.
# Use cdtime for the calendar

if f.fixhd[FH_CalendarType] == 1:
    cdtime.DefaultCalendar = cdtime.GregorianCalendar
elif f.fixhd[FH_CalendarType] == 2:
    cdtime.DefaultCalendar = cdtime.Calendar360
else:
    raise Exception("Unsupported calendar")

vardict = {}
setgrid = False
setsurf = False
timeunits = None

# Check whether file contains any timeseries data
timeseries = False
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    if ilookup[LBCODE] in (31320, 31323):
        timeseries = True
        break

if not timeseries:
    print "File contains no timeseries data"
    sys.exit(1)

if verbose:
    print "Number of records", f.fixhd[FH_LookupSize2]
var = None
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    rlookup = f.rlookup[k]
    if ilookup[LBCODE] not in (31320, 31323):
        # Not a time series
        continue
    lblrec = ilookup[LBLREC]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    lbnrec = ilookup[LBNREC] # Actual size
    if lbegin == -99:
        break

    # if var and var.code == ilookup[ITEM_CODE]:
    # Then this is another level of the same variable

    # Perhaps should just pass the full lookup array?
    # Should this return a unique list of names ???
    npts = ilookup[LBNPT]
    nrows = ilookup[LBROW]

    if not timeunits:
        # Should be hidden as a function somewhere
        timeunits = "days since %4.4d-%2.2d-%2.2d %2.2d:%2.2d" % (ilookup[LBYR],
          ilookup[LBMON], ilookup[LBDAT], ilookup[LBHR], ilookup[LBMIN])

    # Different variables may be saved with different steps
    # Really only need to do this the first time variable is seen.
    end = cdtime.comptime(ilookup[LBYRD], ilookup[LBMOND],
                          ilookup[LBDATD], ilookup[LBHRD], ilookup[LBMIND])
    period = end.torelative(timeunits)
    step = period.value/ilookup[LBROW]
    if verbose:
        print "TIME STEP (days)", step
    # Step will probably be some integer number of minutes
    step = round(1440*step,4)
    if verbose:
        print "TIME STEP (mins)", step

    # ilookup[LBCODE] is 31320 for Gregorian timeseries, 31323 for other calendar
    # rlookup[51] is level, -1 for single or special levels
    f.wordseek(lbegin)  # Offset rather than absolute seek?
    s = f.wordread(npts*nrows)
    # Where is this format for grid point values defined?
    # Added by routine extra_ts_info
    s = f.wordread((npts+1)*6)
    x = np.fromstring(s,np.float64).byteswap().reshape(6,npts+1)
    y = np.fromstring(s,np.int64).byteswap()

    # Need to unpack the first part and then get point values from the
    # last part. This will probably only work when they're separate points
    # Regions will be different?
    startlats = x[0,1:]
    startlons = x[1,1:]
    endlats   = x[2,1:]
    endlons   = x[3,1:]
    startlevs = x[4,1:]
    endlevs   = x[5,1:]

    # Check whether the level is non-zero.
    # Might indicate tiling?

    # This might not be necessary. Levels seem to be saved as individuals even
    # when specified with a range in the UMUI.
    # Perhaps not when a box is specified?
    if not np.allclose(startlats,endlats) or not np.allclose(startlons,endlons) \
           or not np.allclose(startlevs, endlevs) :
        raise Exception("Conversion doesn't support timeseries with regions at the moment")
    # If there are multiple usage domains with different sets of points
    # this code probably won't work.
    # Should perhaps make a list of points for each variable.

    # The notation here is a bit misleading because these aren't really grids.
    # but rather collections of coordinates.

    # If it's on hybrid levels, set the real height
    # Use rlookup[BLEV] to check whether it's on rho or theta. 
    # theta levels are in f.levdep[4], rho levels in f.levdep[6]
    if ilookup[LBVC] == 65:
        if abs(f.levdep[4]-rlookup[BLEV]).min() < 1e-2:
            # Index by theta levels. Level 0 is 0 so start at 1
            startlevs =  f.levdep[4][startlevs.astype(np.int)]
        elif abs(f.levdep[6]-rlookup[BLEV]).min() < 1e-2:
            # Index by rho levels. Level 0 is first model level so start at 0
            startlevs =  f.levdep[6][startlevs.astype(np.int)-1]
        else:
            print "Warning - unexpected vertical levels", ilookup[ITEM_CODE]
            print rlookup[BLEV], f.levdep[4], f.levdep[6]
        
    # Use index to accumulate total number of times for each variable
    # This should use item_code because name might not be unique
    # Use var.code
    if not var or ilookup[ITEM_CODE] not in vardict:
        var = stashvar.StashVar(ilookup[ITEM_CODE], ilookup[MODEL_CODE])
        # Initialising with .UniqueList(startlons) doesn't work
        # because the uniqueness checking isn't added to init method.
        # Need to use a combined lat/lon list because each individual
        # list might have repeated values, e.g. points (30, 150) and (30,155).
        var.gridlist = umfile.UniqueList()
        # var.latlist = umfile.UniqueList()
        var.levlist = umfile.UniqueList()
        # Need tuple so can use set later
        var.gridlist.append([tuple(x) for x in np.column_stack((startlats,startlons)).tolist()])
        # var.latlist.append(startlats)
        if ilookup[LBPLEV] == 1: # Tiles
            var.levlist.append(np.arange(1.,10.))
        else:
            var.levlist.append(startlevs)
        var.count = ilookup[LBROW]
        var.step = step
        vardict[ilookup[ITEM_CODE]] = var
    else:
        vardict[ ilookup[ITEM_CODE]].gridlist.append([tuple(x) for x in np.column_stack((startlats,startlons)).tolist()])
        vardict[ ilookup[ITEM_CODE]].levlist.append(startlevs)
        vardict[ ilookup[ITEM_CODE]].count += ilookup[LBROW]
        # vardict[ITEM_CODE].tlist 

    if verbose:
        # print "X", x
        print "STARTLATS", startlats
        print "STARTLONS", startlons
        print "STARTLEVS", startlevs
        print "ENDLATS", endlats
        print "ENDLONS", endlons
        print "ENDLEVS", endlevs

    if verbose:
        print "-----------------------------------------------------------"
        print var.name, var.long_name
        print f.ilookup[k, :45]
        print f.rlookup[k, 45:]
        # Expect lblrec = npts*nrows + npts*9
        print "Rec size", k, lbnrec, lblrec, npts*nrows + (npts+1)*6
        print "Start time", ilookup[:5]
        print "End time", ilookup[6:11]
        print "Level type", ilookup[LBVC]
        print "Forecast period", ilookup[LBFT]
        print "Rows", ilookup[LBROW]
        print "Data type", ilookup[DATA_TYPE]
        print "Level", ilookup[LBLEV]
        print "Pseudo level", ilookup[LBPLEV]



#     # Update lists of point coordinates
#         # in a dictionary?
#         # vardict[var.code].count += ilookup[LBROW] ???
#         # Should also check that the grids match
#         vtmp = vardict[var.code]
#         vtmp.count += ilookup[LBROW]
#         vardict[var.code] = vtmp

# #         var.step = step
# #         var.lon = lon  # So we can find the correct axes later
# #         var.lat = lat
# #         var.lev = lev
#         print "Adding to dictionary", var.name #, var.lon.lev
#         var.count = ilookup[LBROW]
# #         vardict[var.code] = var

# Global attributes
d.history = "%s Created by um_timeseries.py from file %s" % (time.strftime("%Y-%m-%d %H:%M"), ifile)

# Distinct coordinates
# Convert lists to tuples so they're hashable.
ugrid = sorted(list(set([tuple(v.gridlist) for v in vardict.values()])))
# ulat = sorted(list(set([tuple(v.latlist) for v in vardict.values()])))
ulev = sorted(list(set([tuple(v.levlist) for v in vardict.values()])))
if verbose:
    print "Number of distinct coordinate sets", len(ugrid), len(ulev)
    print "Unique gridpts", ugrid


for k in range(len(ulev)):
    lev = ulev[k]
    if verbose:
        print "LEVLIST", k, lev
    if not (max(lev) == min(lev) == 1):
        dname = "lev_%d" % k
        d.createDimension(dname,len(lev))
        levsvar = d.createVariable("lev_%d"%k, "f", (dname,))
        # Need to get the appropriate level type and the proper values
        # rather than just indices.
        if abs(f.levdep[4]-lev[0]).min() < 1e-4:
            levsvar.long_name = "Model theta levels"
            levsvar.units = 'm'
        elif abs(f.levdep[6]-lev[0]).min() < 1e-4:
            levsvar.long_name = "Model rho levels"
            levsvar.units = 'm'
        else:
            levsvar.long_name = "Model levels"
        levsvar.axis='Z'
        levsvar[:] = np.array(lev).astype(np.float32)

# Length of ulon and ulat must be the same
for k in range(len(ugrid)):
    grid = ugrid[k]
    dname = "gridpts_%d" % k
    vname = "lon_%d" % k
    d.createDimension(dname,len(grid))
    lonsvar = d.createVariable(vname, "f", (dname,))
    lonsvar.long_name = "longitude"
    lonsvar.units = "degrees_east"
    lon = [p[1] for p in grid]
    lonsvar[:] = np.array(lon).astype(np.float32)
    vname = "lat_%d" % k
    latsvar = d.createVariable(vname, "f", (dname,))
    latsvar.long_name = "latitude"
    latsvar.units = "degrees_north"
    lat = [p[0] for p in grid]
    latsvar[:] = np.array(lat).astype(np.float32)

# Assume a single time index per file.
# Check that each variable has the same time axis.    
# Make a list of the times
times = [v.count for v in vardict.values()]
tset = set(times) # To get unique times
tlist = list(tset)
tlist.sort()
steps = [v.step for v in vardict.values()]
stepset = set(steps) # To get unique times
steplist = list(stepset)
steplist.sort(reverse=True)

# Check these have same lengths, otherwise there's some inconsistency
if len(steplist) != len(tlist):
    raise Exception("Inconsistency in lengths of time and step lists %d, %d" % (len(tlist), len(steplist)))

for k, nt in enumerate(tlist):
    name = "time_%d" % k
    timedim = d.createDimension(name, nt)
    timevar = d.createVariable(name, "f", (name,))
    timevar.units = timeunits
    tval = cdtime.reltime(0,timeunits)
    for t in range(nt):
        timevar[t] = tval.value
        tval = tval.add(steplist[k], cdtime.Minutes)

# Create the variables
# Use of filevars here won't handle multiple use of the same variable
# with different profiles.
filevars = {}
dims = {}
for vcode in vardict:
    var = vardict[vcode]
    vname = var.name
    # Match all the dimensions
    timedim = "time_%d" % tlist.index(var.count)
    if min(var.levlist) == max(var.levlist) == 1:
        levdim = None
    else:
        levdim = "lev_%d" % ulev.index(tuple(var.levlist))
    gridd = ugrid.index(tuple(var.gridlist))
    griddim = "gridpts_%d" % gridd
    if vname in d.variables.keys():
        # Need to generalise this properly
        vname = vname + "_2"
    if levdim:
        if verbose:
            print "Creating %s with %s, %s, %s" % (vname, timedim, levdim, griddim)
        newvar = d.createVariable(vname, "f", (timedim, levdim, griddim))
    else:
        if verbose:
            print "Creating %s (%d) with %s, %s" % (vname, vcode, timedim, griddim)
        newvar = d.createVariable(vname, "f", (timedim, griddim))
    newvar.long_name = var.long_name
    if var.units:
        newvar.units = var.units
    if var.standard_name:
        newvar.standard_name = var.standard_name
    newvar.longitude = "longitude_%d" % gridd
    newvar.latitude = "latitude_%d" % gridd
    filevars[vcode] = newvar
    # This is a transposed list because that's the order it's needed in later
    dims[vcode] = (len(var.gridlist), len(var.levlist))
        
countvar = {}
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lblrec = ilookup[LBLREC]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    lbnrec = ilookup[LBNREC] # Actual size
    if lbegin == -99:
        break
    var = stashvar.StashVar(ilookup[ITEM_CODE],ilookup[MODEL_CODE])

    npts = ilookup[LBNPT]
    nrows = ilookup[LBROW]
    f.wordseek(lbegin)
# Need to apply this everywhere, also for reading lats and lons.
##     if ilookup[LBPACK] == 0:
##         s = f.wordread(npts*nrows)
##         data = np.reshape( np.fromstring(s, np.float64).byteswap(), [nrows, npts])
##     elif ilookup[LBPACK] == 2:
##         s = f.wordread((npts*nrows)//2)
##         data = np.reshape( np.fromstring(s, np.float32).byteswap(), [nrows, npts])
##     else:
##         raise "Unsupported packing type %d" % ilookup[LBPACK]
    s = f.wordread(npts*nrows)
    data = np.reshape( np.fromstring(s, np.float64).byteswap(), [nrows, npts])

    item_code = ilookup[ITEM_CODE]
    try:
        start = countvar[item_code]
        countvar[item_code] = countvar[item_code] + ilookup[LBROW]
    except KeyError:
        start = 0
        countvar[item_code] = ilookup[LBROW]

    # Shouldn't need to keep doing this
    #var = stashvar.StashVar(ilookup[ITEM_CODE], ilookup[MODEL_CODE])
    #filevar = d.variables[var.name]
    # Data ranges over levels first, then grid points
#     print "SHAPES", data.shape, start, ilookup[LBROW]
#     print "DATA", data[0]
    for k in range(data.shape[0]):
        tmp = data[k]
        tmp.shape = dims[ilookup[ITEM_CODE]]
        tmp = tmp.transpose()
        # if k == 0:
            # print "Shapes"
            # print tmp.shape, filevars[ilookup[ITEM_CODE]][start+k].shape
            # print tmp
        if len(filevars[ilookup[ITEM_CODE]].shape) == 3:
            # Level dimension
            filevars[ilookup[ITEM_CODE]][start+k] = tmp.astype(np.float32)
        else:
            # tmp has a trivial level dimension
            filevars[ilookup[ITEM_CODE]][start+k] = tmp.astype(np.float32)[0]


d.close()
