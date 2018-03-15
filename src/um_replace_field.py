#!/usr/bin/env python

# Replace a field in a UM fieldsfile with values from a netcdf file
# Note that this modifies the file in place
# Will only work for single level fields
# Also needs to handle packing properly

# Martin Dix martin.dix@csiro.au

import numpy as np
import argparse, sys
import umfile
from um_fileheaders import *
import cdms2
from cdms2 import MV2


parser = argparse.ArgumentParser(description="Replace field in UM file with a field from a netCDF file.")
parser.add_argument('-v', dest='varcode', type=int, required=True, help='Variable to be replaced (specified by STASH index = section_number * 1000 + item_number')
parser.add_argument('-n', dest='ncfile', required=True, help='Input netCDF file')
parser.add_argument('-V', dest='ncvarname', required=True, help='netCDF variable name')
parser.add_argument('target', help='UM File to change')


args = parser.parse_args()

d = cdms2.open(args.ncfile)
try:
    # Remove singleton dimensions (time or level in surface fields)
    ncvar = d.variables[args.ncvarname](squeeze=1)
except KeyError:
    print "\nError: variable %s not in %s" % (args.ncvarname, args.ncfile)
    sys.exit(1)
    

f = umfile.UMFile(args.target, "r+")

# Set new missing value to match the UM missing value 
arr = MV2.array(ncvar[:])
arr.setMissing(f.missval_r)

# Loop over all the fields
replaced = False
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] == args.varcode:
        print "Replacing field", k, ilookup[ITEM_CODE]
        if not (ilookup[LBROW], ilookup[LBNPT]) == arr.shape:
            print "\nError: array shape mismatch"
            print "UM field shape", (ilookup[LBROW], ilookup[LBNPT])
            print "netcdf field shape", arr.shape
            sys.exit(1)
        # Simplest way to get 32/64 bit size right, though umfile
        # should really fix it on write
        a = f.readfld(k)
        a[:] = arr[:]
        f.writefld(a[:], k)
        replaced = True

if not replaced:
    print "\nWarning: requested stash code %d not found in file %s" % (args.varcode, args.target)
    print "No replacement made."

f.close()
