#!/usr/bin/env python

# Apply a perturbation to initial condition.
# Note that this works in place.
# For ENDGAME perturb thetavd as well if it's present

# Martin Dix martin.dix@csiro.au

import argparse
import umfile
from um_fileheaders import *
from numpy.random import MT19937, RandomState, SeedSequence

parser = argparse.ArgumentParser(description="Perturb UM initial dump")
parser.add_argument('-a', dest='amplitude', type=float, default=0.01,
                    help = 'Amplitude of perturbation')
parser.add_argument('-s', dest='seed', type=int, required=True,
    help = 'Random number seed (must be non-negative integer)')
parser.add_argument('ifile', help='Input file (modified in place)')

args = parser.parse_args()

if args.seed >= 0:
    rs = RandomState(args.seed)
else:
    raise Exception('Seed must be positive')

f = umfile.UMFile(args.ifile, 'r+')

# Set up theta perturbation.
nlon = f.inthead[IC_XLen]
nlat = f.inthead[IC_YLen]
# Same at each level so as not to upset vertical stability
perturb = args.amplitude * (2.*rs.random(nlon*nlat).reshape((nlat,nlon)) - 1.)
# Set poles to zero (only necessary for ND grids, but doesn't hurt EG)
perturb[0] = 0.
perturb[-1] = 0.

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    # 4 is theta, 388 is thetavd (ENDGAME only)
    if ilookup[ITEM_CODE] in (4, 388):
        a = f.readfld(k)
        # Note that using += ensures the datatype of a doesn't change
        # (in case it's float32)
        a += perturb
        f.writefld(a,k)

f.close()
