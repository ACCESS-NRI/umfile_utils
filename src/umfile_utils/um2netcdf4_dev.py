#!/usr/bin/env python
#
# A python script to convert the CMIP6 fields (atmospheric) from
# UM fieldsfiles to netcdf format. This script works for all the
# four types of fields (monthly, daily, 6-hourly, and 3-hourly).
# For min, max fields, also need to match on cell_methods attribute
# Assume these are "time0: min" and "time0: max".
#
# The input variable names are mapped to CMIP6 variable names before 
# writing to netcdf files. Also, singleton dimensions are eliminated,
# coordinate names are mapped to the commonly used names, and the time
# dimension is written as 'unlimited'. This is helpful for creating 
# timeseries for one or more variables and writing them to a netcdf
# file, e.g.:
#     ncrcat -h -v tas multiple_input_files.nc single_output_file.nc
# 
# Climate diagnostics on pressure levels are normally masked;
# nomask option turns this off (special case for runs where the
# heavyside function, used for masking, were not saved).
#
# Written by Martin Dix, Petteri Uotila, Harun Rashid and Peter Uhe.

from __future__ import print_function
import os, sys, argparse, datetime, collections
import numpy as np
import cdms2, cdtime, netCDF4
from cdms2 import MV
import stashutils, stashvar_cmip6 as stashvar
    
parser = argparse.ArgumentParser(description="Convert UM fieldsfile to netCDF.")
parser.add_argument('-i', dest='ifile', required=True, help='Input UM file')
parser.add_argument('-o', dest='ofile', required=True, help='Output netCDF file')
parser.add_argument('-k', dest='nckind', required=False, type=int,
                    default=3, help='specify kind of netCDF format for output file: 1 classic, 2 64-bit offset, 3 netCDF-4, 4 netCDF-4 classic model. Default 3', choices=[1,2,3,4])
parser.add_argument('-d', dest='deflate_level', required=False, type=int,
                    default=1, help='Compression level for netCDF4 output from 0 (none) to 9 (max). Default 1')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', 
                    default=False, help='verbose output')
parser.add_argument('--nomask', dest='nomask', action='store_true', 
                    default=False, help="Don't apply Heaviside function mask to pressure level fields.\n Default is to apply masking if the Heaviside field is available in the input file.")
parser.add_argument('--simple', dest='simple', action='store_true', 
                    default=False, help="Use a simple names of form fld_s01i123.")
# Using choices=('cm2', 'esm1.5') not available in python 2.7
parser.add_argument('--model', dest='model', required=False, 
                    default='cm2', help="Which model is being processed (affects dimension naming). Choices are cm2 (default) and esm1.5")
parser.add_argument('-S', dest='STASHmaster', required=False, 
                    default=None, help="Path to alternate STASHmaster file.")

args = parser.parse_args()

if args.model not in ('cm2', 'esm1.5'):
    parser.print_help()
    raise Exception("Invalid model choice %s" % args.model)

mask = not args.nomask

if args.verbose:
    print("Using python version: "+sys.version.split()[0])

def transform_dimensions(fi):
    # First work out which dimensions to exclude
    excludeDims=['nv']
    dims = set(fi.listdimension()) # set of all dim_names in the file
    for dim in dims:
        dobj = fi.dimensionobject(dim)
        # Exclude unnecessary singleton dimensions
        # Keep time, longitude (zonal means) and single pressure levels
        # Negative level value used for 850 vorticity
        if dobj.shape==(1,) and not (dobj.isTime() or dobj.isLongitude()):
            if not dobj.isLevel() or dobj.long_name.endswith('(dummy level coordinate)') or dobj.getData()[0] <= 0.:
                excludeDims.append(dim)
    dimns = list(dims.difference(excludeDims)) # exclude those in excludeDims
    dimns.sort()

    print("Excluded dimensions", excludeDims)
    print("Remaining dimensions", dimns)

    # Before using variables to work out dimension names, need to
    # check that these are consistent.
    level_codes = stashutils.get_level_codes(args.STASHmaster)
    dimdict = collections.defaultdict(list)
    for vname in fi.listvariables():
        var = fi.variables[vname]
        if hasattr(var,'stash_item'):
            # Exclude dimension variables
            for d in var.listdimnames():
                if d in dimns:
                    dimdict[d].append(vname)
    for dname in dimdict:
        if dname.startswith('z'):
            vars = dimdict[dname]
            # Do these all have the same level codes
            for k, v in enumerate(vars):
                var = fi.variables[v]
                code = 1000*var.stash_section[0] + var.stash_item[0]
                if k == 0:
                    first = level_codes[code]
                else:
                    # Treatment of level first and last is a bit odd, so skip this
                    # as well as grid
                    if not ( level_codes[code][1] == first[1] and
                             level_codes[code][4:] == first[4:] ):
                        # ESM changes some variables from tiles to
                        # PFTs so skip check in this case
                        # Handled using dimension size below.
                        if not (args.model=='esm1.5' and first.levelt==5 and first.pseudt==9):
                            
                            print("*** Mismatch", dname, vars, level_codes[code], first)
                            raise Exception()

    renameDims = {}
    for dim in dimns:
        dobj = fi.dimensionobject(dim)
        dval = dobj.getData()
        renamed = False
        long_name = None
        if dobj.isTime():
            if dim == 'time0':
                # Most files have only a single dimension
                dimout = 'time'
                renamed = True
        # see if we need to rename output netcdf dimension name
        elif dobj.isLatitude():
            # Work out the grid. ESM uses ND
            # Assuming it's global here
            if args.model == 'cm2':
                if dval[0] == -90.:
                    dimout = 'lat_v'
                else:
                    dimout = 'lat'
            else:
                if dval[0] == -90.:
                    dimout = 'lat'
                else:
                    dimout = 'lat_v'
            if dimout == 'lat':
                long_name = 'latitudes at T grid points'
            elif dimout == 'lat_v':
                long_name = 'latitudes at V grid points'
            renamed = True
        elif dobj.isLongitude():
            # Work out the grid
            if args.model == 'cm2':
                if dval[0] == 0.:
                    dimout = 'lon_u'
                else:
                    dimout = 'lon'
            else:
                # Assuming it's global here
                if dval[0] == 0.:
                    dimout = 'lon'
                else:
                    dimout = 'lon_u'
            if dimout == 'lon':
                long_name = 'longitudes at T grid points'
            elif dimout == 'lon_u':
                long_name = 'longitudes at U grid points'
            renamed = True
        elif dim.startswith('z'):
            # Already checked that the dimensions are all used
            # consistently, so can choose appropriate names from the
            # level codes of the first variable that uses it
            vname = dimdict[dim][0]
            var = fi.variables[vname]
            code = 1000*var.stash_section[0] + var.stash_item[0]
            levelt = level_codes[code].levelt
            nlev = len(dval)
            if levelt == 1:
                dimout = 'z_hybrid_height_rho'
            elif levelt == 2:
                dimout = 'z_hybrid_height_theta'
            elif levelt == 3:
                dimout = 'z_p_level_%d' % nlev
            elif levelt == 5:
                # Surface
                pseudt = level_codes[code].pseudt
                if pseudt == 1:
                    dimout = 'z_sw_band'
                    long_name = 'SW radiation spectral band'
                elif pseudt == 2:
                    dimout = 'z_lw_band'
                    long_name = 'LW radiation spectral band'
                elif pseudt == 4:
                    dimout = 'z_aod_band'
                    long_name = 'aerosol optical depth spectral band'
                elif pseudt == 10:
                    dimout = 'z_icecat'
                    long_name = 'sea-ice category'
                elif pseudt == 9:
                    # Vegetation
                    pseudl = level_codes[code].pseudl
                    if args.model=='esm1.5':
                        # Inconsistent, so use dim size
                        if nlev==13:
                            dimout = 'z_pft'
                            long_name = 'land surface vegetated tile index'
                        elif nlev==17:
                            dimout = 'z_tile'
                            long_name = 'land surface tile index'
                        else:
                            raise Exception("Unexpected dimension size for tile pseudo dimension %s" % nlev)
                    else:
                        if pseudl == 8:
                            dimout = 'z_pft'
                            long_name = 'land surface vegetated tile index'
                        elif pseudl == 9:
                            dimout = 'z_tile'
                            long_name = 'land surface tile index'
                else:
                    raise Exception("Unexpected pseudt %d for var %d" % (pseudt, code))
            elif levelt == 6:
                dimout = 'z_soil_level'
            else:
                raise Exception('Unexpected level type %d' % levelt)
            renamed = True
        if renamed:
            renameDims[dim] = (dimout, long_name)
        else:
            renameDims[dim] = (dim, long_name)

    if args.verbose:
        print("Renamed dimensions", renameDims)
    return renameDims

# a function to create dimensions in the netCDF file
def write_nc_dimension(dimension,renameDims,fi,fo):
    dobj = fi.dimensionobject(dimension)
    dval = dobj.getData()
    dimout = renameDims[dimension][0]
    # There may be several input dimensions that map to same output
    # dimension. Check that the values match in this case
    if dimout in fo.dimensions:
        if not np.allclose(dval, fo.variables[dimout][:]):
            print("Dimension %s renamed as %s already in use" % (dimension, dimout))
            print("Coordinate mismatch")
            print(dval)
            print(fo.variables[dimout][:])
            raise Exception()
        else:
            if args.verbose:
                print("Dimension %s renamed as %s already in use" % (dimension, dimout))
            return
    
    if dobj.isTime():
        dimlen = None
    else:
        dimlen = len(dval)
    if args.verbose:
        print("Creating dimension %s as %s, dimlen: %s" % (dimension,dimout,dimlen))
    fo.createDimension(dimout,dimlen)
    if hasattr(dobj,'standard_name') and dobj.standard_name == 'time':
        fo.createVariable(dimout,'d',(dimout,))
    else:
        fo.createVariable(dimout,dval.dtype.char,(dimout,))
    for dattr in dobj.attributes:
        setattr(fo.variables[dimout],dattr,getattr(dobj,dattr))
    long_name = renameDims[dimension][1]
    if long_name:
        fo.variables[dimout].long_name = long_name
    if dimout == 'z_soil_level':
        fo.variables[dimout].units = "m"
        # CDMS gets this wrong
        fo.variables[dimout].positive = "down"
    if fo.variables[dimout].units == "Pa":
        # CDMS gives values with extra 1e-8 for some reason.
        fo.variables[dimout][:] = np.round(dval,6)
    else:
        fo.variables[dimout][:] = dval

def findvar(vars, section, item):
    for v in vars.values():
        if hasattr(v,'stash_section') and v.stash_section[0] == section and v.stash_item[0] == item:
            return v
    raise KeyError

global heavyside_uv, heavyside_t
heavyside_uv = heavyside_t = None

def apply_mask(var,heavyside):
    # Mask variable by heavyside function
    fVal = var.getMissing()
    vorder = var.getOrder()
    horder = heavyside.getOrder()
    if vorder != horder:
        print(vorder,'!= heavyside',horder,file=sys.stderr)
        raise Exception('Unable to apply pressure level mask because of dimension order mismatch')
    # Slice to match var
    if var.shape == heavyside.shape:
        var = MV.where(np.greater(heavyside,hcrit),var/heavyside,fVal)
        var.fill_value = var.missing_value = fVal
        return var
    else:
        # Do they just differ in number of levels with the variable's
        # levels being a subset?
        zdim = vorder.find('z')
        vshape = list(var.shape)
        hshape = list(heavyside.shape)
        # Compare shapes without the z dimension
        vshape[zdim] = hshape[zdim] = 0
        if vshape == hshape:
            # Convert to list so that index works later
            vlevs = var.getLevel()[:].tolist()
            hlevs = heavyside.getLevel()[:].tolist()
            assert zdim==0  # Assume given a t slice
            # Need to make a copy first
            newvar = var[:]
            if set(vlevs).issubset(set(hlevs)):
                # Then we can do the match
                for k in range(len(vlevs)):
                    kh = hlevs.index(vlevs[k])
                    if args.verbose:
                        print("Matching levels", k, kh)
                    newvar[k] = MV.where(np.greater(heavyside[kh],hcrit),newvar[k]/heavyside[kh],fVal)
                newvar.fill_value = newvar.missing_value = fVal
                return newvar
            
        print("Problem applying pressure level mask for variable %d" %(item_code),file=sys.stderr)
        print(var.shape,'!= heavyside',heavyside.shape)
        raise Exception('Unable to apply pressure level mask because of shape mismatch')
    return var

def heavyside_mask(var,item_code, t):
    global heavyside_uv, heavyside_t
    # Variable range here is correct at vn11.3
    if 30201 <= item_code <= 30288  or 30302 <= item_code <= 30303:
        if not heavyside_uv:
            # Set heavyside variable if doesn't exist
            try:
                heavyside_uv = findvar(fi.variables,30,301)
            except KeyError:
                raise Exception("Heavyside variable on UV grid required for pressure level masking of %d not found" % item_code)
        return apply_mask(var[t],heavyside_uv[t])
    elif 30293 <= item_code <= 30298:
        if not heavyside_t:
            # set heavyside variable if doesn't exist
            try:
                heavyside_t = findvar(fi.variables,30,304)
            except KeyError:
                raise Exception("Heavyside variable on T grid required for pressure level masking of %d not found" % item_code)
        return apply_mask(var[t],heavyside_t[t])
    else:
        raise Exception("Unexpected item code %d in heavyside_mask function" % item_code)

# Main program begins here. 
# First, open the input UM file (fieldsfile)  

try:
    fi = cdms2.open(args.ifile,'r')
except:
    print("Error opening file", args.ifile, file=sys.stderr)
    sys.exit(1)

if os.path.exists(args.ofile):
    os.unlink(args.ofile)

# Create an output netCDF file
ncformats = {1:'NETCDF3_CLASSIC', 2:'NETCDF3_64BIT', 
             3:'NETCDF4', 4:'NETCDF4_CLASSIC'}
fo = netCDF4.Dataset(args.ofile,'w',format=ncformats[args.nckind])

history = "%s converted with um2netcdf4.py by %s on %s." % (os.path.abspath(args.ifile), os.getenv('USER'),datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# global attributes
for attribute in fi.attributes:
    if attribute in ('history'):
        setattr(fo,attribute,history)
    elif attribute not in ('input_file_format', 'input_uri', 'input_word_length','input_byte_ordering') :
        setattr(fo,attribute,getattr(fi,attribute))

# variables to write
varnames = fi.listvariables()

renameDims = transform_dimensions(fi)

# create dimensions
for dimension in sorted(renameDims):
    write_nc_dimension(dimension,renameDims,fi,fo)
if args.verbose:
    print("Finished writing dimensions...")

umvar_atts = ["name","long_name","standard_name","units"]
hcrit = 0.5 # Critical value of Heavyside function for inclusion.

# Create a list of variable names sorted by stash code
snames = []
for varname in varnames:
    vval = fi.variables[varname]
    if hasattr(vval,'stash_item') and hasattr(vval,'stash_section'):
        stash_section = vval.stash_section[0]
        stash_item = vval.stash_item[0]
        item_code = vval.stash_section[0]*1000 + vval.stash_item[0]
        snames.append((item_code,varname))
snames.sort()

varnames_out=[]
# loop over all variables
# create variables but don't write data yet
if args.verbose:
    print('creating variables...')
for tmpval, varname in snames:
    vval = fi.variables[varname]
    vdims = vval.listdimnames()
    # remove excluded dims:
    for vdim in vdims:
    	if vdim not in renameDims:
    	    vdims.remove(vdim)
    # see if we need to rename variables netcdf dimensions
    for vdidx, vdim in enumerate(vdims):
        if vdim in renameDims:
            vdims[vdidx] = renameDims[vdim][0]
    if hasattr(vval,'stash_item') and hasattr(vval,'stash_section'):
        stash_section = vval.stash_section[0]
        stash_item = vval.stash_item[0]
        item_code = vval.stash_section[0]*1000 + vval.stash_item[0]
        umvar = stashvar.StashVar(item_code,vval.stash_model[0])
        vname = umvar.name
        if args.simple:
            vname = 'fld_s%2.2di%3.3d' % (stash_section, stash_item)

        if hasattr(vval,"cell_methods") and vval.cell_methods == "time0: max":
            vname = vname+"_max"
        if hasattr(vval,"cell_methods") and vval.cell_methods == "time0: min":
            vname = vname+"_min"
        
        # write data
        if vval.dtype in (np.int32, np.int64):
            vtype = np.int32
        else:
            vtype = np.float32
        basename = vname
        suffix = 1
        while vname in fo.variables:
            vname = '%s_%d' %(basename, suffix)
            suffix += 1
        if args.verbose and vname != basename:
            print("Using name %s because of duplication" % vname)
        fo.createVariable(vname, vtype, tuple(vdims),
                          zlib=True, complevel=args.deflate_level,
                          fill_value=getattr(vval,'_FillValue'))
        if args.verbose:
            print(vname +"\t created from "+ varname)
        varnames_out.append((varname,vname))

        # variable attributes
        for vattr in vval.listattributes():
            if getattr(vval,vattr) is None:
                print("Could not write attribute %s for %s." % (vattr,vname))
            else:
                if vattr not in ('_FillValue', 'stash_model', 'lookup_source'):
                    attval = getattr(vval,vattr)
                    if hasattr(attval,'dtype') and attval.dtype == np.int64:
                        attval = attval.astype(np.int32)
                    setattr(fo.variables[vname],vattr,attval)

        for vattr in umvar_atts:
            if hasattr(umvar,vattr) and getattr(umvar,vattr) != '':
                fo.variables[vname].setncattr(vattr,getattr(umvar,vattr))
                
# Loop over all variables writing data
# Assume same number of times for all variables
# Get number of times from first variable used
varname, vname_out = varnames_out[0]
vval = fi.variables[varname]
nt = vval.shape[0]

if args.verbose:
    print('writing data')
for t in range(nt):
    for varname, vname_out in varnames_out:
        vval = fi.variables[varname]
        stash_section = vval.stash_section[0]
        stash_item = vval.stash_item[0]
        item_code = vval.stash_section[0]*1000 + vval.stash_item[0]
        if 30201 <= item_code <= 30303 and item_code not in [30301, 30304] and mask:
            # P LEV field with missing values treated as zero needs
            # to be corrected by Heavyside fn. Exclude the Heavyside
            # fields themselves (301 and 304).
            vval = heavyside_mask(vval,item_code,t)
            fo.variables[vname_out][t] = vval.getValue()
        else:
            sp = vval.shape
            if len(sp) == 4 and sp[1] == 1 and len(fo.variables[vname_out].shape) == 3:
                # A singleton level dimension was removed, so use
                # explicit index so shapes match
                fo.variables[vname_out][t] = vval[t,0].getValue()
            else:
                fo.variables[vname_out][t] = vval[t].getValue()
        if args.verbose and t==0:
            print('writing', varname, 'to',vname_out)

if args.verbose:
    print('finished')

fo.close() 
