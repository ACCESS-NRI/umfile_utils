#!/usr/bin/env python
# Reset any negative snow values, stash codes 23 and 240

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *


ifile = sys.argv[1]

f = umfile.UMFile(ifile, 'r+')

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] in [23, 240]:
        a = f.readfld(k)
        a[a<0.] = 0.
        f.writefld(a,k)

f.close()
