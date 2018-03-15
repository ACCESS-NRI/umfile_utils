#!/usr/bin/env python

# Count number of land points in a UM landmask ancillary file.
# Program expects that the mask is the first field.
# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

verbose = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'v')
    for opt in optlist:
        if opt[0] == '-v':
            verbose = True
except getopt.error:
    print "Usage: count_land [-v] file"
    sys.exit(2)

ifile = args[0]

f = umfile.UMFile(ifile)

# Start of data
dstart = f.fixhd[FH_DataStart]

# Expecting only a single field
k = 0
ilookup = f.ilookup[k]
lblrec = ilookup[LBLREC]
lbegin = ilookup[LBEGIN] # lbegin is offset from start
lbnrec = ilookup[LBNREC] # Actual size
packing = [0, ilookup[LBPACK]%10, ilookup[LBPACK]//10 % 10,
           ilookup[LBPACK]//100 % 10, ilookup[LBPACK]//1000 % 10,
           ilookup[LBPACK]//10000]
npts = ilookup[LBNPT]
nrows = ilookup[LBROW]

# Check field name and data type.
# Expecting stash code 1 0 30 LAND MASK
if ilookup[ITEM_CODE] != 30:
    print "Variable is not land mask, stashcode is", ilookup[ITEM_CODE]
    sys.exit(1)
if ilookup[DATA_TYPE] != 3:
    print "Variable is not expected logical type, code is", ilookup[DATA_TYPE]
    sys.exit(1)

data = f.readfld(0)

# Mask may be +-1 depending on compiler used in ancillary program.
print (data != 0).sum()
