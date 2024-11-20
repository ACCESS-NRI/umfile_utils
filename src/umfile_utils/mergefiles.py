#!/usr/bin/env python

# Merge two UM fieldsfiles
# All fields are merged, so for finer control subset the files 
# separately first. 
# Basic header information is taken from the first file.
# By default, duplicate fields are also from the first file 
# (override with the -d option)

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *
import argparse

parser = argparse.ArgumentParser(description='Merge UM files')

parser.add_argument('-d', '--default', dest='duplicate', type=int, default=1,
                    help='default file for duplicate fields (1 or 2)')

parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', 
                    default=False, help='verbose output')

parser.add_argument('file1', help='Input file')
parser.add_argument('file2', help='Input file')
parser.add_argument('file3', help='Output file')

args = parser.parse_args()

f1 = umfile.UMFile(args.file1)

f2 = umfile.UMFile(args.file2)

g = umfile.UMFile(args.file3, "w")
g.copyheader(f1)

print("Lookup sizes", f1.fixhd[FH_LookupSize2], f1.fixhd[FH_LookupSize1],
    f2.fixhd[FH_LookupSize2], f2.fixhd[FH_LookupSize1])

g.ilookup[:] = -99 # Used as missing value

# Start of data is at fixhd[FH_DataStart], 
# This should be a multiple of 2048 + 1
# Start of lookup table fixhd[FH_LookupStart]
min_dstart = g.fixhd[FH_LookupStart] + g.fixhd[FH_LookupSize2]*g.fixhd[FH_LookupSize1]
dstart = (min_dstart//2048 + 1)*2048 + 1
g.fixhd[FH_DataStart] = dstart

# # Should pad g up to the start?
# # Check space
# space = dstart - g.fixhd[FH_LookupStart]
# print "Offsets 1",  f1.fixhd[FH_LookupStart], f1.fixhd[FH_DataStart]
# print "Offsets 2",  f2.fixhd[FH_LookupStart], f2.fixhd[FH_DataStart]
# print space, (f1.fixhd[FH_LookupSize2] + f2.fixhd[FH_LookupSize2])*f1.fixhd[FH_LookupSize1]
                                                                    
k1=0
k2=0
kout = 0
kount = dstart-1 # dstart is index rather than offset
nprog = 0
ntracer = 0
end1 = False
end2 = False

while True:
    if args.verbose:
        print("K", k1, k2, kout)
    if k1 >= f1.fixhd[FH_LookupSize2] or f1.ilookup[k1][LBEGIN]==-99:
        end1 = True
    if k2 >= f2.fixhd[FH_LookupSize2] or f2.ilookup[k2][LBEGIN]==-99:
        end2 = True
    
    if end1 and end2:
        break
    if end1:
        f = f2
        k = k2
        k2 += 1
    elif end2:
        f = f1
        k = k1
        k1 += 1
    else:        
        if f1.ilookup[k1][ITEM_CODE] == f2.ilookup[k2][ITEM_CODE]:
            if args.duplicate == 1:
                print("Warning - duplicate (using file1 version)", f1.ilookup[k1][ITEM_CODE])
                f = f1
                k = k1
            else:
                print("Warning - duplicate (using file2 version)", f1.ilookup[k1][ITEM_CODE])
                f = f2
                k = k2
            k1 += 1
            k2 += 1
        elif f1.ilookup[k1][ITEM_CODE] < f2.ilookup[k2][ITEM_CODE]:
            f = f1
            k = k1
            k1 += 1
        else:
            f = f2
            k = k2
            k2 += 1

    g.ilookup[kout] = f.ilookup[k]
    g.rlookup[kout] = f.rlookup[k]

    data = f.readfld(k,raw=True)
    g.writefld(data,kout,raw=True)
    if umfile.isprog(g.ilookup[kout]):
        nprog += 1
        if umfile.istracer(g.ilookup[kout]):
            ntracer += 1
    kout += 1

# This sort of correction should be in a new function?

# To get correct number of tracer fields need to divide by number of levels
ntracer /= g.inthead[IC_TracerLevs]

g.fixhd[FH_LookupSize2] = kout
g.fixhd[FH_NumProgFields] = nprog
g.inthead[IC_TracerVars] = ntracer
if ntracer > 0 and g.inthead[IC_TracerLevs] != g.inthead[IC_PLevels]:
    g.inthead[IC_TracerLevs] = g.inthead[IC_PLevels]

g.close()
