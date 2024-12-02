#!/usr/bin/env python

# Merge two UM fieldsfiles
# Files must have exactly same fields, grids etc

# This version only merges the specified region (defined as for 
# subset_ancillary) from field in file1 to field in file2
# Merge region is specified by the indices of the lower left corner (x0,y0)
# and the extents nx, ny. 
# These are specified as arguments -x x0,nx -y y0,ny
# Note that (x0,y0) are 0 based indices
# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

def usage():
    print "Usage: mergefiles_region.py  -x x0,nx -y y0,ny file1 file2 outputfile"
    sys.exit(2)

verbose = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'x:y:v')
    for opt in optlist:
        if opt[0] == '-v':
            verbose = True
        elif opt[0] == '-x':
            x0 = int(opt[1].split(',')[0])
            nx = int(opt[1].split(',')[1])
        elif opt[0] == '-y':
            y0 = int(opt[1].split(',')[0])
            ny = int(opt[1].split(',')[1])
except getopt.error:
    usage()
    sys.exit(2)

if len(args) != 3:
    print "Missing filename arguments"
    usage()

# Section to take
if verbose:
    print "Section", x0, y0, nx, ny

f1 = umfile.UMFile(args[0])
f2 = umfile.UMFile(args[1])
g = umfile.UMFile(args[2], "w")
g.copyheader(f1)

for k in range(f1.fixhd[FH_LookupSize2]):
    if f1.ilookup[k][LBEGIN]==-99  or f2.ilookup[k][LBEGIN]==-99:
        break
    
    if f1.ilookup[k][ITEM_CODE] != f2.ilookup[k][ITEM_CODE]:
        raise Exception("files do not match %d %d %d" %
    (k,  f1.ilookup[k][ITEM_CODE],  f2.ilookup[k][ITEM_CODE]))

    data1 = f1.readfld(k)
    dataout = f2.readfld(k)
    dataout[y0:y0+ny,x0:x0+nx] = data1[y0:y0+ny,x0:x0+nx]
    
    g.writefld(dataout.astype(g.float),k)

g.close()
