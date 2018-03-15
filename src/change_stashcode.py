#!/usr/bin/env python
# Change the stashcode of selected fields in a UM fieldsfile
# Note that the reconfiguration can read and sort an out of order file so
# don't need to worry about reordering fields here.

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

vdict = {}
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'v:')
    for opt in optlist:
        if opt[0] == '-v':
            oldindex,newindex = opt[1].split(",")
            oldindex = int(oldindex)
            newindex = int(newindex)
            vdict[oldindex] = newindex
except getopt.error:
    print "Usage: change_stashcode.py -v oldindex,newindex file"
    print "       Variables specified by STASH index = Section Number * 1000 + item number"
    print "       May use multiple -v arguments"
    sys.exit(2)

ifile = args[0]
f = umfile.UMFile(ifile,'r+')

changed = False
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN]
    if lbegin == -99:
        break
    # Format is Section Number * 1000 + item number
    if ilookup[ITEM_CODE] in vdict:
        changed = True
        ilookup[ITEM_CODE] = vdict[ilookup[ITEM_CODE]]

if not changed:
    print "Warning - no fields changed"

f.close()

