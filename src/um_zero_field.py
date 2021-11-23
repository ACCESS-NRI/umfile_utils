#!/usr/bin/env python
# Zero specified fields in a UM file

# Martin Dix martin.dix@csiro.au

import numpy as np
import argparse, sys
import umfile
from um_fileheaders import *

parser = argparse.ArgumentParser(description="Set fields in UM file to zero")
parser.add_argument('-v', dest='var', type=int, default=None,
                    nargs = '+', help = 'List of stash codes to zero (default is all)')
parser.add_argument('file', help='File to process (overwritten)')

args = parser.parse_args()

f = umfile.UMFile(args.file, 'r+')

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if not args.var or ilookup[ITEM_CODE] in args.var:
        print("Zeroing field", k, 'stash code', ilookup[ITEM_CODE])
        a = f.readfld(k)
        a[:] = 0.
        f.writefld(a,k)

f.close()
