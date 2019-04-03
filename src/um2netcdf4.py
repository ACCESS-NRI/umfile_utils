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
#   This script is designed taking ideas from previous python scripts
# written by Martin Dix and Petteri Uotila.
#
# Harun Rashid (harun.rashid@csiro.au)
# 20-JUL-2011
#
# Peter Uhe (Peter.Uhe@csiro.au)
# 29-May 2013 modified to use netcdf4 libraries with zlib compression. 
#
# 3-Dec 2013 set up for raijin
# To use on raijin set up the environment by the following commands:
#
# module load python/2.7.5
# module use /projects/access/modules
# module load pythonlib/cdat-lite/6.0rc2-fixed
# module load pythonlib/netCDF4/1.0.4

#TODO possibly append libraries to the end of the path, 
# rather than requiring the environment to be set

from __future__ import print_function
import os, sys, argparse
import numpy as np
import re
from datetime import datetime
import traceback
import stashvar

heavyside = None

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

args = parser.parse_args()

mask = not args.nomask

print("Using python version: "+sys.version.split()[0])

try:
    import cdms2, cdtime
    from cdms2 import MV
    from netCDF4 import Dataset
except:
    print("""ERROR: modules not loaded
    Please run:
        module use ~access/modules
        module load pythonlib/netCDF4
        module load pythonlib/cdat-lite
        """)
    exit()

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
excludeDims=[]

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
fo=Dataset(args.ofile,'w',format=ncformats[args.nckind])

history = "Converted to netCDF by %s on %s." % (os.getenv('USER'),datetime.now().strftime("%Y-%m-%d"))

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


varnames_out={}
# loop over all variables
# create variables but dont write data
print('creating variables...')
for varname in varnames:
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

        if hasattr(vval,"cell_methods") and vval.cell_methods == "time0: max":
            vname = vname+"max"
        if hasattr(vval,"cell_methods") and vval.cell_methods == "time0: min":
            vname = vname+"min"
        
        # write data
        try:
            fo.createVariable(vname, vval.dtype.char, tuple(vdims),
                              zlib=True, complevel=args.deflate_level,
                              fill_value=getattr(vval,'_FillValue'))
            print(vname +"\t created... from "+ varname)
            sys.stdout.flush()
        except:
            print("Could not write %s!" % vname)
            vname = vname+'_1'
            try:
	        fo.createVariable(vname, vval.dtype.char, tuple(vdims),
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
        varnames_out[varname]=vname

        # variable attributes
        for vattr in vval.listattributes():
            if getattr(vval,vattr) is None:
                print("Could not write attribute %s for %s." % (vattr,vname))
            else:
                if vattr!='_FillValue':
                    setattr(fo.variables[vname],vattr,getattr(vval,vattr))
        for vattr in umvar_atts:
            if hasattr(umvar,vattr) and getattr(umvar,vattr) != '':
                fo.variables[vname].setncattr(vattr,getattr(umvar,vattr)) 
# loop over all variables
# write data
print('writing data')
try:
    # Assume same number of times for all variables
    # Get number of times from first variable used
    for varname,vname_out in varnames_out.items():
        vval = fi.variables[varname]
        sp = vval.shape
        #remove singleton dim
        if len(sp) == 4 and sp[1] == 1:
            vval = vval[:,0,:,:]
        # P LEV/UV GRID with missing values treated as zero;
        # needs to be corrected by Heavyside fn
        stash_section = vval.stash_section[0]
        stash_item = vval.stash_item[0]
        item_code = vval.stash_section[0]*1000 + vval.stash_item[0]
        if (30201 <= item_code <= 30303) and mask and item_code!=30301:
            if not heavyside:
                # set heavyside variable if doesn't exist
                try:
                    heavyside = fi.variables['psag']
                    # check variable code as well as the name.
                    if (heavyside.stash_item[0] != 301 or
                        heavyside.stash_section[0] != 30) :
                        raise error, "Heavyside variable code mismatch"
                except Exception: #heaviside function not available
                    #use temperature zeros as mask (only works for instantaneous values)
                    try:
                        heavyside=fi.variables['temp_1'] #second temp field is on pressure levels
                    except:
                        heavyside=fi.variables['temp'] #take temp if there is no temp_1
                    heavyside=np.array(heavyside[:]!=0,dtype=np.float32)
                    # print(np.shape(heavyside))
            # Mask variable by heavyside function
            fVal = vval.getMissing()         	
            if vval.shape == heavyside.shape:
                vval = MV.where(np.greater(heavyside[:],hcrit),vval/heavyside[:],fVal)
                vval.fill_value = vval.missing_value = fVal
            else:
                print(vname,vval.shape,'!= heavyside',heavyside.shape)
                print(vname+' not masked')
        fo.variables[vname_out][:] = vval[:]
        print('written: ',varname, 'to',vname_out)
    print('finished')
except Exception, e:
    print('Error :(' ,e)
    traceback.print_exc()
    raise e

sys.stdout.flush()
fo.close() 
