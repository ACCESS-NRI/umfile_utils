#!/usr/bin/env python
# Convert UM monthly PP files to netcdf and concatenate
# Also works with daily files and optionally calculates the monthly average
# For min, max temperature, also need to match on cell_methods attribute
# Assume this starts with time0:

# Climate diagnostics on pressure levels are normally masked and need to be 
# corrected using the Heaviside function.
# nomask option turns this off (special case for runs where these were
# saved differently).

# Use the -x option to optionally skip some variables.

import cdms2, cdtime, sys, getopt, collections
from cdms2 import MV
import numpy as np
import stashvar

class error(Exception):
    pass


def process_file(ifile,suffix,average=False,forcedaily=False,mask=True,xlist=[]):

    try:
        d = cdms2.open(ifile)
    except:
        print "Error opening file", ifile
        usage()
        sys.exit(1)

    hcrit = 0.5 # Critical value of Heavyside function for inclusion.
    ofilelist = []

    for vn in d.variables:
        var = d.variables[vn]
        # Need to check whether it really has a stash_item to skip coordinate variables

        # Note: need to match both item and section number
        if not hasattr(var,'stash_item'):
            continue
        item_code = var.stash_section[0]*1000 + var.stash_item[0]
        if item_code in xlist:
            print "Skipping", item_code
            continue

        grid = var.getGrid()
        time = var.getTime()
        timevals = np.array(time[:])
        if forcedaily:
            # Work around cdms error in times
            for k in range(len(time)):
                timevals[k] = round(timevals[k],1)

        umvar = stashvar.StashVar(item_code,var.stash_model[0])
        vname = umvar.name
        print vname, var[0,0,0,0]

        # Create filename from variable name and cell_methods,
        # checking for name collisions
        if suffix:
            ofile = "%s_%s.nc" % (umvar.uniquename, suffix)
        else:
            ofile = "%s.nc" % umvar.uniquename
        if ofile in ofilelist:
            raise Exception("Duplicate file name %s" % ofile)
        ofilelist.append(ofile)

    #  If output file exists then append to it, otherwise create a new file
        try:
            file = cdms2.openDataset(ofile, 'r+')
            newv = file.variables[vname]
            newtime = newv.getTime()
        except cdms2.error.CDMSError:
            file = cdms2.createDataset(ofile)
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

            order = var.getOrder()
            if order[1] == 'z':
                lev = var.getLevel()
                if len(lev) > 1:
                    newlev = file.createAxis('lev', lev[:])
                    for attr in ('standard_name', 'units', 'positive', 'axis'):
                        if hasattr(lev,attr):
                            setattr(newlev, attr, getattr(lev,attr))
                else:
                    newlev = None
            else:
                # Pseudo-dimension
                pdim = var.getAxis(1)
                if len(pdim) > 1:
                    newlev = file.createAxis('pseudo', pdim[:])
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
            newv.missing_value = missval
            newv.stash_section=var.stash_section[0] 
            newv.stash_item=var.stash_item[0] 
            newv._FillValue = missval

            try:
                newv.units = var.units
            except AttributeError:
                pass

        # Get appropriate file position
        # Uses 360 day calendar, all with same base time so must be 30 days on.
        k = len(newtime)
        # float needed here to get the later logical tests to work properly
        avetime = float(MV.average(timevals[:])) # Works in either case
        if k>0:
            if average:
                # if newtime[-1] != (avetime - 30):
                # For Gregorian calendar relax this a bit
                # Sometimes get differences slightly > 31
                if not 28 <= avetime - newtime[-1] <= 31.5:
                    raise error, "Times not consecutive %f %f %f" % (newtime[-1], avetime, timevals[0])
            else:
                if k > 1:
                    # Need a better test that works when k = 1. This is just a
                    # temporary workaround
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
                # multiple levels
                newv[k] = MV.average(var[:],axis=0).astype(np.float32)
            else:
                # single level
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

def usage():
    print "Usage: um2netcdf_all.py [-a] [-d] -i ifile -o suffix [--nomask]"

def help():
    usage()
    print " -i input_file (Met Office  fieldsfile format)"
    print " -o suffix (output file suffix, e.g. -o test means ts_test.nc) "
    print " -a (calculate time average)"
    print " -d Force daily time values (work around cdms error)"

if __name__ == '__main__':

    # vname is the name to use in the output file
    cell_methods = None
    average = False
    mask = True
    ifile = None
    suffix = None
    forcedaily = False
    xlist = []
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'adhi:o:x:',['nomask'])
        for o, a in opts:
            if o == '-a':
                average = True
            elif o == '-h':
                help()
                sys.exit(0)
            elif o == '-d':
                forcedaily = True
            elif o == '-i':
                ifile = a
            elif o == '--nomask':
                mask = False
            elif o == '-o':
                suffix = a
            elif o == '-x':
                for v in a.split(","):
                    xlist.append(int(v))
    except getopt.error:
        usage()
        sys.exit(1)

    process_file(ifile,suffix,average,forcedaily,mask,xlist)
