#!/usr/bin/env python
# Dump header information from a UM fields file

# Martin Dix martin.dix@csiro.au

# TODO
# Should get the field names from rcf_headaddress_mod.F90

from __future__ import print_function, division
import numpy as np
import argparse, sys
from um_fileheaders import *
import umfile, stashvar

parser = argparse.ArgumentParser(description="Dump contents of a UM fieldsfile")
parser.add_argument('-H', dest='header_only', action='store_true',
                default=False, help='show header only')
parser.add_argument('--noheader', dest='noheader', action='store_true',
                default=False, help="Don't show file header")
parser.add_argument('-s', dest='short', action='store_true',
                default=False, help='short list of fields')
parser.add_argument('-S', dest='summary', action='store_true',
                default=False, help='summary similar to model list of expected fields')
parser.add_argument('infile', help='Input file')

args = parser.parse_args()

f = umfile.UMFile(args.infile)

if not f.fieldsfile:
    print("Not a UM fieldsfile")
    sys.exit(1)

f.readheader()

def getlevel(ilookup):
    if ilookup[LBPLEV] != 0:
        # Snow variables on tiles have this as 1000*tile_index + layer
        # 1001, 2001, ... 1002, 2002, ...
        # Model treats these as a single variable
        # Reverse this to get something that increments
        if ilookup[LBPLEV] > 1000:
            lev = ilookup[LBPLEV] % 1000
            tile = ilookup[LBPLEV] // 1000
            return lev*1000 + tile
        else:
            return ilookup[LBPLEV]
    else:
        if ilookup[LBLEV] == 9999:
            # Used for surface fields and 0th level of multi-level fields
            return 0
        else:
            return ilookup[LBLEV]

if not (args.summary or args.noheader):
    f.print_fixhead()
    print("Integer constants", f.inthead)
    print("REAL HEADER", f.realhead)
    if hasattr(f,"levdep"):
        print("Level dependent constants", f.levdep)
    if hasattr(f,"rowdep"):
        print("Row dependent constants", f.rowdep)
    if hasattr(f,"coldep"):
        print("Column dependent constants", f.coldep)

lastvar = None
nl = 0
nfld = 0
if not args.header_only:

    for k in range(f.fixhd[FH_LookupSize2]):
        ilookup = f.ilookup[k]
        lblrec = ilookup[LBLREC]
        lbegin = ilookup[LBEGIN] # lbegin is offset from start
        if lbegin == -99:
            break
        var = stashvar.StashVar(ilookup[ITEM_CODE],ilookup[MODEL_CODE])
        if not (args.short or args.summary):
            print("-------------------------------------------------------------")
        if args.summary:
            if not lastvar:
                # To get started
                lastvar = ilookup[ITEM_CODE]
                lastlevel = getlevel(ilookup)
                nl = 1
            else:
                # Just check that level increases to handle the tiled snow
                # variables.
                # Pressure levels should decrease
                # Check that the times match,
                if ( lastvar == ilookup[ITEM_CODE] and
                     np.all(f.ilookup[k-1][:LBLREC] == ilookup[:LBLREC]) and
                     ( getlevel(ilookup) > lastlevel or
                       ilookup[LBVC] == 8 and getlevel(ilookup) < lastlevel)):
                    # Same variable as previous one
                    lastlevel += 1
                    nl += 1
                else:
                    var = stashvar.StashVar(lastvar,ilookup[MODEL_CODE])
                    # nfld starts from 1 to match list in model output
                    nfld += 1
                    print(nfld, nl, lastvar, var.name, var.long_name)
                    lastvar = ilookup[ITEM_CODE]
                    lastlevel = getlevel(ilookup)
                    nl = 1
        else:
            print(k, ilookup[ITEM_CODE], var.name, var.long_name)

        if ilookup[LBCODE] == f.missval_i:
            # There are some files with variables codes in headers but much
            # of the rest of the data missing
            print("Header data missing")
            continue
        if args.summary or args.short:
            continue
        print(f.ilookup[k, :45])
        print(f.rlookup[k, 45:])
        npts = ilookup[LBNPT]
        nrows = ilookup[LBROW]

        try:
            data = f.readfld(k)

            # Sample values
            print("Range", data.min(), data.max())
            if len(data.shape)==2:
                print("%12.6g %12.6g %12.6g %12.6g %12.6g" % (data[0,0], data[0,npts//4], data[0,npts//2], data[0,3*npts//4], data[0,-1]))
                print("%12.6g %12.6g %12.6g %12.6g %12.6g" % (data[nrows//4,0], data[nrows//4,npts//4], data[nrows//4,npts//2], data[nrows//4,3*npts//4], data[nrows//4,-1]))
                print("%12.6g %12.6g %12.6g %12.6g %12.6g" % (data[nrows//2,0], data[nrows//2,npts//4], data[nrows//2,npts//2], data[nrows//2,3*npts//4], data[nrows//2,-1]))
                print("%12.6g %12.6g %12.6g %12.6g %12.6g" % (data[3*nrows//4,0], data[3*nrows//4,npts//4], data[3*nrows//4,npts//2], data[3*nrows//4,3*npts//4], data[3*nrows//4,-1]))
                print("%12.6g %12.6g %12.6g %12.6g %12.6g" % (data[-1,0], data[-1,npts//4], data[-1,npts//2], data[-1,3*npts//4], data[-1,-1]))
        except umfile.packerr:
            print("Can't handle packed data")

if args.summary:
    if lastvar:
        # There's one left at the end
        print(nfld+1, nl, lastvar, var.name, var.long_name)
    else:
        print("No data fields present")
