# Limit soil moisture to be <= saturation

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

dzsoil = np.array([0.1, 0.25, 0.65, 2.0])

f = umfile.UMFile(sys.argv[1], 'r+')

# On the first pass, just get the saturation fraction
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] == 43:
        saturation = f.readfld(k)
        break

level = 0
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] == 9:
        sm = f.readfld(k)
        sm = np.minimum(sm, 1000*dzsoil[level]*saturation)
        level += 1
        f.writefld(sm,k)

f.close()
