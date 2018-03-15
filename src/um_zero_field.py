#!/usr/bin/env python
# Zero specified fields in a UM file

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

vlist = []
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'v:')
    for opt in optlist:
        if opt[0] == '-v':
            # Allow comma separated lists
            for v in opt[1].split(","):
                vlist.append(int(v))
except getopt.error:
    print "Usage: um_zero_field.py [-v var] file"
    print "       -v var1,var2,... to zero only these variables"
    print "       Variables specified by STASH index = Section Number * 1000 + item number"
    sys.exit(2)

ifile = args[0]

f = umfile.UMFile(ifile, 'r+')

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] in vlist:
        print "Zeroing", k, ilookup[ITEM_CODE]
        a = f.readfld(k)
        a[:] = 0.
        f.writefld(a,k)

f.close()
