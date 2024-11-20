#!/usr/bin/env python
# Modify specified fields in a UM file

# Martin Dix martin.dix@csiro.au

import numpy as np
import argparse, sys
import umfile
from um_fileheaders import *

parser = argparse.ArgumentParser(description="Modify field in UM file with offset and scale factor, new = a*old + b.")
parser.add_argument('-a', dest='scale', type=float, default=1, help='Scale factor (default 1)')
parser.add_argument('-b', dest='offset', type=float, default=0, help='Offset (default 0)')
parser.add_argument('-v', action='append', dest='varcode', type=int, required=True, help='Variable to be modified (specified by STASH index = section_number * 1000 + item_number. -v argument may be repeated to process multiple fields.')
parser.add_argument('file', help='File to be modified')

args = parser.parse_args()

if args.scale == 1 and args.offset == 0:
    print("Nothing to be done, a=1, b=0")
    sys.exit(0)

f = umfile.UMFile(args.file, 'r+')

changed = False
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if ilookup[ITEM_CODE] == args.varcode:
        a = f.readfld(k)
        a[:] = a[:] * args.scale + args.offset
        f.writefld(a,k)
        changed = True

if not changed:
    print('Warning: no fields changed')

f.close()
