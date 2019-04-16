#!/usr/bin/env python
#
# A python script to convert the CMIP5 fields (atmospheric) from
# UM fieldsfiles to netcdf format. This script works for all the
# four types of fields (monthly, daily, 6-hourly, and 3-hourly).
# For min, max fields, also need to match on cell_methods attribute
# Assume these are "time0: min" and "time0: max".
#
# The input variable names are mapped to CMIP5 variable names before 
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
# Acknowledgement:
# Written by Martin Dix, Petteri Uotila, Harun Rashid and Peter Uhe.

from __future__ import print_function
import os, sys, argparse, datetime
import numpy as np
import cdms2, cdtime, netCDF4
from cdms2 import MV

parser = argparse.ArgumentParser(description="Convert UM fieldsfile to netCDF.")
parser.add_argument('-i', dest='ifile', required=True, help='Input UM file')
parser.add_argument('-o', dest='ofile', required=True, help='Output netCDF file')
parser.add_argument('-k', dest='nckind', required=False, type=int,
                    default=4, help='specify kind of netCDF format for output file: 1 classic, 2 64-bit offset, 3 netCDF-4, 4 netCDF-4 classic model. Default 4', choices=[1,2,3,4])
parser.add_argument('-d', dest='deflate_level', required=False, type=int,
                    default=1, help='Compression level for netCDF4 output from 0 (none) to 9 (max). Default 1')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', 
                    default=False, help='verbose output')
parser.add_argument('--nomask', dest='nomask', action='store_true', 
                    default=False, help="Don't apply Heaviside function mask to pressure level fields.\n Default is to apply masking if the Heaviside field is available in the input file.")
parser.add_argument('--cmip6', dest='cmip6', action='store_true', 
                    default=False, help="Use a CMIP6 version of the name mapping table.")
parser.add_argument('--simple', dest='simple', action='store_true', 
                    default=False, help="Use a simple names of form fld_s01i123.")

args = parser.parse_args()

mask = not args.nomask

print("Using python version: "+sys.version.split()[0])

if args.cmip6:    
    import stashvar_cmip6 as stashvar
else:
    import stashvar

    
# Rename dimension to commonly used names
renameDims = {'latitude0':'lat','longitude0':'lon','latitude1':'lat_1',\
              'longitude1':'lon_1','longitude2':'lon_2','z4_p_level':'lev','z9_p_level':'lev',\
              'z3_p_level':'lev','time0':'time','time1':'time_1',\
        'z6_hybrid_sigmap':'z0_hybrid_height','z5_hybrid_sigmap':'z0_hybrid_height'}

# Exclude the singleton dimensions from the output neCDF file
#excludeDims = ['z0_surface','z10_msl','z3_toa','z4_level','z7_height',\
#              'z1_level','z2_height','z5_msl','z8_level','z2_msl',\
#               'z4_surface','z2_level','z3_height','z4_soil','z7_msl',\
#				'z5_toa','z2_surface','z3_msl','z4_msl','z12_soil',\
#				'z13_level','z15_msl','z1_surface','z4_toa','z5_level',\
#				'z9_height','z_pseudo3']

# Not really clear what this is, but no variables depend on it.
excludeDims=['nv']

# a function to create dimensions in the netCDF file
def write_nc_dimension(dimension,fi,fo):
    dobj = fi.dimensionobject(dimension)
    dval = dobj.getData()
    # make the time dimension "unlimited"
    if dobj.id == 'time0':
        dimlen = None
    else:
        dimlen = len(dval)
    # see if we need to rename output netcdf dimension name
    try:
        dimout = renameDims[dimension] if dimension in renameDims else dimension
        if dimout not in fo.variables.keys():
#           fo.create_dimension(dimout,dimlen)
            fo.createDimension(dimout,dimlen)
            if hasattr(dobj,'standard_name') and dobj.standard_name == 'time':
                fo.createVariable(dimout,'d',(dimout,))
            else:
                fo.createVariable(dimout,dval.dtype.char,(dimout,))
            for dattr in dobj.attributes:
                setattr(fo.variables[dimout],dattr,getattr(dobj,dattr))
            fo.variables[dimout][:] = dval
        else:
            print('already written ',dimout,'...skipping')
    except:
        dimout = dimension
        if dimout not in fo.variables.keys():
           fo.createDimension(dimension,dimlen)
           if hasattr(dobj,'standard_name') and dobj.standard_name == 'time':
               fo.createVariable(dimension,'d',(dimension,))
           else:
               fo.createVariable(dimension,dval.dtype.char,(dimension,))
           for dattr in dobj.attributes:
               setattr(fo.variables[dimension],dattr,getattr(dobj,dattr))
           fo.variables[dimension][:] = dval
    # update dimension mapping
    if dimension in renameDims:
        renameDims[dimension] = dimout
    print("Wrote dimension %s as %s, dimlen: %s" % (dimension,dimout,dimlen))

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
        print(vorder,'!= heavyside',horder)
        raise Exception('Unable to apply pressure level mask because of dimension order mismatch')
    if var.shape == heavyside.shape:
        var = MV.where(np.greater(heavyside[:],hcrit),var/heavyside[:],fVal)
        var.fill_value = var.missing_value = fVal
        return var
    else:
        # Do they just differ in number of levels with variable
        # levels being a subset
        zdim = vorder.find('z')
        vshape = list(var.shape)
        hshape = list(heavyside.shape)
        # Compare shapes without the z dimension
        vshape[zdim] = hshape[zdim] = 0
        if vshape == hshape:
            # Convert to list so that index works later
            vlevs = var.getLevel()[:].tolist()
            hlevs = heavyside.getLevel()[:].tolist()
            assert zdim==1
            # Need to make a copy first
            newvar = var[:]
            if set(vlevs).issubset(set(hlevs)):
                # Then we can do the match
                for k in range(len(vlevs)):
                    kh = hlevs.index(vlevs[k])
                    print("Matching levels", k, kh)
                    newvar[:,k] = MV.where(np.greater(heavyside[:,kh],hcrit),newvar[:,k]/heavyside[:,kh],fVal)
                newvar.fill_value = newvar.missing_value = fVal
                return newvar
            
        print("Problem applying pressure level mask for variable %d" %(item_code))
        print(var.shape,'!= heavyside',heavyside.shape)
        raise Exception('Unable to apply pressure level mask because of shape mismatch')
    return var

def heavyside_mask(var,item_code):
    global heavyside_uv, heavyside_t
    # Variable range here is correct at vn11.3
    if 30201 <= item_code <= 30288  or 30302 <= item_code <= 30303:
        if not heavyside_uv:
            # Set heavyside variable if doesn't exist
            try:
                heavyside_uv = findvar(fi.variables,30,301)
            except KeyError:
                raise Exception("Heavyside variable on UV grid required for pressure level masking of %d not found" % item_code)
        return apply_mask(var,heavyside_uv)
    elif 30293 <= item_code <= 30298:
        if not heavyside_t:
            # set heavyside variable if doesn't exist
            try:
                heavyside_t = findvar(fi.variables,30,304)
            except KeyError:
                raise Exception("Heavyside variable on T grid required for pressure level masking of %d not found" % item_code)
        return apply_mask(var,heavyside_t)
    else:
        raise Exception("Unexpected item code %d in heavyside_mask function" % item_code)

# Main program begins here. 
# First, open the input UM file (fieldsfile)  

try:
    fi = cdms2.open(args.ifile,'r')
except:
    print("Error opening file", args.ifile)
    sys.exit(1)

if os.path.exists(args.ofile):
    os.unlink(args.ofile)

# Create an output netCDF file
ncformats = {1:'NETCDF3_CLASSIC', 2:'NETCDF3_64BIT', 
             3:'NETCDF4', 4:'NETCDF4_CLASSIC'}
fo = netCDF4.Dataset(args.ofile,'w',format=ncformats[args.nckind])

history = "Converted to netCDF by %s on %s." % (os.getenv('USER'),datetime.datetime.now().strftime("%Y-%m-%d"))

# global attributes
for attribute in fi.attributes:
    if attribute in ['history']:
        setattr(fo,attribute,"%s. %s" % (getattr(fi,attribute),history))
    else:
        setattr(fo,attribute,getattr(fi,attribute))

# variables to write
varnames = fi.listvariables()

# collect list of dimensions associated with these variables
dims = set(fi.listdimension())             # set of all dim_names in the file
for dim in dims:
	dobj = fi.dimensionobject(dim)
	if dobj.shape==(1,) and (dim.find('time')==-1 and dim.find('longitude')==-1):
		excludeDims.append(dim)
dimns = list(dims.difference(excludeDims)) # exclude those in excludeDims
dimns.sort()

# create dimensions
for dimension in dimns:
    write_nc_dimension(dimension,fi,fo)
print("Finished writing dimensions...")
sys.stdout.flush()

umvar_atts = ["name","long_name","standard_name","units"]
hcrit = 0.5               # critical value of Heavyside function for inclusion.

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
print('creating variables...')
for tmpval, varname in snames:
    vval = fi.variables[varname]
    vdims = vval.listdimnames()
	#remove excludDims:
    for vdim in vdims:
    	if vdim in excludeDims:
    		vdims.remove(vdim)
    # see if we need to rename variables netcdf dimensions
    for vdidx, vdim in enumerate(vdims):
        if vdim in renameDims:
            vdims[vdidx] = renameDims[vdim]
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
        try:
            fo.createVariable(vname, vtype, tuple(vdims),
                              zlib=True, complevel=args.deflate_level,
                              fill_value=getattr(vval,'_FillValue'))
            print(vname +"\t created... from "+ varname)
            sys.stdout.flush()
        except:
            print("Could not write %s!" % vname)
            vname = vname+'_1'
            try:
	        fo.createVariable(vname, vtype, tuple(vdims),
                                  zlib=True, complevel=args.deflate_level,
                                  fill_value=getattr(vval,'_FillValue'))
            except Exception,e:
                vname=varname
                print(e,vval.shape)
                fo.createVariable(vname, vval.dtype.char, tuple(vdims),
                                  zlib=True, complevel=args.deflate_level,
                                  fill_value=getattr(vval,'_FillValue'))
            print("Now written as %15s ..." % vname)
            sys.stdout.flush()
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
# write data
print('writing data')
# Assume same number of times for all variables
# Get number of times from first variable used
for varname, vname_out in varnames_out:
    vval = fi.variables[varname]
    stash_section = vval.stash_section[0]
    stash_item = vval.stash_item[0]
    item_code = vval.stash_section[0]*1000 + vval.stash_item[0]
    if 30201 <= item_code <= 30303 and item_code not in [30301, 30304] and mask:
        # P LEV field with missing values treated as zero needs
        # to be corrected by Heavyside fn. Exclude the Heavyside
        # fields themselves (301 and 304).
        vval = heavyside_mask(vval,item_code)       
    sp = vval.shape
    # Remove singleton dimension
    if len(sp) == 4 and sp[1] == 1:
        vval = vval[:,0,:,:]
    fo.variables[vname_out][:] = vval[:]
    print('written: ',varname, 'to',vname_out)
print('finished')

fo.close() 
