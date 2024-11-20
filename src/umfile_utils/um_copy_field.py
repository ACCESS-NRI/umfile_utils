#!/usr/bin/env python
# Copy one or more fields from one UM file to another
# Note that this only copies the data, not any of the header information
# (date etc). Minimal sanity checking.

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

vlist = []
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:o:v:')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-o':
            ofile = opt[1]
        elif opt[0] == '-v':
            # Allow comma separated lists
            for v in opt[1].split(","):
                vlist.append(int(v))
except getopt.error:
    print "Usage: um_copy_field.py -i ifile -o ofile -v var"
    print "       Copy fields from ifile to ofile"
    print "       Variables specified by STASH index = Section Number * 1000 + item number"
    print "       May use a list specififed as -v var1,var2,..."
    sys.exit(2)

f = umfile.UMFile(ifile, "r")
g = umfile.UMFile(ofile, "r+")

# Find the indices of the desired fields in each file.
# This assumes that each is in normal stashcode order 
# (as all files produced by model are)
findex = []
gindex = []
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] in vlist:
        findex.append(k)

for k in range(g.fixhd[FH_LookupSize2]):
    ilookup = g.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] in vlist:
        gindex.append(k)

# print "Field lengths", len(findex), len(gindex)
if len(findex) != len(gindex):
    raise Exception("Files have different number of target fields %d %d" %
                    (len(findex), len(gindex)))

# Loop over all the fields
for k in range(len(findex)):
    ilookup = f.ilookup[findex[k]]
    olookup = g.ilookup[gindex[k]]
    # print "Replacing", k, ilookup[ITEM_CODE]
    # Check that sizes match. Checking LBLREC here catches fields packed
    # to land points
    if not ( ilookup[LBLREC] == olookup[LBLREC] and
             ilookup[LBNPT] == olookup[LBNPT] and
             ilookup[LBROW] == olookup[LBROW] ):
        print "Input data shape",  ilookup[LBLREC],  ilookup[LBNPT], ilookup[LBROW] 
        print "Output data shape",  olookup[LBLREC],  olookup[LBNPT], olookup[LBROW] 
        raise Exception("Inconsistent grid sizes")
    if not ilookup[ITEM_CODE] == olookup[ITEM_CODE]:
        raise Exception("Inconsistent stash codes")
    a = f.readfld(findex[k])
    g.writefld(a,gindex[k])

g.close()
