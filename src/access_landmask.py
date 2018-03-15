# Set up a land mask fiel for access
# Ancillary mask file qrparm.mask at appropriate resolution must alreay exist.
# Also qrparm.landfrac
# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *
import cdms2

d = cdms2.open('um_n96_landseamask_gice2n96.nc')
ncvar = d('umland',squeeze=1).filled()
mask = np.where(ncvar<0.01,0,1).astype(np.int64)
frac = np.where(ncvar<0.01,0,ncvar).astype(np.float64)
print "MASK", mask.shape

f = umfile.UMFile('qrparm.mask', "r+")
f.readheader()
f.readlookup()

varcode = 30

# Loop over all the fields
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] == varcode:
        print "Replacing", k, ilookup[ITEM_CODE]
        f.wordseek(lbegin)
        npts = ilookup[LBNPT]
        nrows = ilookup[LBROW]
        a = f.readfld(k)
        a[:] = mask[:]
        f.writefld(a,k)

f.close()

f = umfile.UMFile('qrparm.landfrac', "r+")
f.readheader()
f.readlookup()

varcode = 505

# Loop over all the fields
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] == varcode:
        print "Replacing", k, ilookup[ITEM_CODE]
        # f.wordseek(lbegin)
        npts = ilookup[LBNPT]
        nrows = ilookup[LBROW]
        a = f.readfld(k)
        print "A", a.min(), a.max()
        a.shape = (nrows,npts)
        print "SHAPES", a.shape, frac.shape
        a[:] = frac[:]
        f.writefld(a,k)

f.close()
