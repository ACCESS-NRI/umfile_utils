#!/usr/bin/env python

# Dump header and field information from a UM LBC file
# These pack all levels together into a single record

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
from um_fileheaders import *
import umfile, stashvar

short = False
header = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:hs')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-h':
            header = True
        elif opt[0] == '-s':
            short = True
except getopt.error:
    print "Usage: lbc_dump [-s] -i ifile "
    sys.exit(2)

if args:
    ifile = args[0]
    
f = umfile.UMFile(ifile)

if not f.fieldsfile:
    print "Not a UM fieldsfile"
    sys.exit(1)

if f.fixhd[FH_Dataset] != 5:
    print "Not an LBC file", f.fixhd[FH_Dataset]
    sys.exit(1)

f.print_fixhead()

print "Integer constants", f.inthead

print "REAL HEADER", f.realhead

if hasattr(f,"levdep"):
    print "Level dependent constants", f.levdep

if hasattr(f,"rowdep"):
    print "Row dependent constants", f.rowdep

if hasattr(f,"coldep"):
    print "Column dependent constants", f.coldep

if not header:
    
    for k in range(f.fixhd[FH_LookupSize2]):
        ilookup = f.ilookup[k]
        lblrec = ilookup[LBLREC]
        lbegin = ilookup[LBEGIN] # lbegin is offset from start
        lbnrec = ilookup[LBNREC] # Actual size
        if lbegin == -99:
            break
        var = stashvar.StashVar(ilookup[ITEM_CODE],ilookup[MODEL_CODE])
        if not short:
            print "-------------------------------------------------------------"
        print k, ilookup[ITEM_CODE], var.name, var.long_name
        if not short:
            print f.ilookup[k, :45]
            print f.rlookup[k, 45:]
        npts = ilookup[LBNPT]
        nrows = ilookup[LBROW]

        data = f.readfld(k)

        # Sample values
        print ilookup[ITEM_CODE], data[0], "Range", data.min(), data.max()
