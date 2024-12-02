#!/usr/bin/env python

# Replace a field in a UM fieldsfile with values from a netcdf file
# Note that this modifies the file in place
# Works with single or multi-level (include pseudo-level) fields

# Martin Dix martin.dix@csiro.au

from __future__ import print_function
import numpy as np
import argparse, sys, iris, umfile
from um_fileheaders import *

parser = argparse.ArgumentParser(description="Replace field in UM file with a field from a netCDF file.")
parser.add_argument('-v', dest='varcode', type=int, required=True,
      help='Variable to be replaced (specified by STASH index = section_number * 1000 + item_number')
parser.add_argument('-n', dest='ncfile', required=True, help='Input netCDF file')
parser.add_argument('-V', dest='ncvarname', required=True, help='netCDF variable name')
parser.add_argument('target', help='UM File to change')

args = parser.parse_args()

cube = iris.load_cube(args.ncfile,iris.Constraint(cube_func=lambda c: c.var_name==args.ncvarname))
cube = iris.util.squeeze(cube)

# Expect that the cube doesn't have a time dimension after the squeeze
if 'time' in cube.coords():
    print("Unexpected time dimension in input variable")
    print(cube)
    sys.exit(1)

if cube.ndim == 2:
    multilevel = False
elif cube.ndim == 3:
    multilevel = True
    nlev = cube.shape[0]

f = umfile.UMFile(args.target, "r+")

if hasattr(cube.data, 'mask'):
    # Set missing value to match the fieldsfile missing value
    arr = cube.data.filled(f.missval_r)
else:
    arr = cube.data

# Loop over all the fields
replaced = False
ilev = 0
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] == args.varcode:
        if multilevel:
            print("Replacing field", k, ilookup[ITEM_CODE], 'level', ilev)
        else:
            print("Replacing field", k, ilookup[ITEM_CODE])
        # Packing
        n3 = (ilookup[LBPACK] // 100) % 10
        # Don't check shape if data is packed to land or ocean points
        if n3==0 and not (ilookup[LBROW], ilookup[LBNPT]) == arr.shape[-2:]:
            print("\nError: array shape mismatch")
            print("UM field shape", (ilookup[LBROW], ilookup[LBNPT]))
            print("netcdf field shape", arr.shape)
            sys.exit(1)
        a = f.readfld(k)
        if n3 == 0:
            print("Initial sum", a.sum())
        else:
            print("Initial sum", np.ma.masked_array(a,f.mask==0).sum())
        if multilevel:
            a[:] = arr[ilev]
        else:
            a[:] = arr[:]
        if n3 == 0:
            print("Final sum", a.sum())
        else:
            print("Final sum", np.ma.masked_array(a,f.mask==0).sum())
        f.writefld(a[:], k)
        ilev += 1
        replaced = True

if not replaced:
    print("\nWarning: requested stash code %d not found in file %s" % (args.varcode, args.target))
    print("No replacement made.")

f.close()
