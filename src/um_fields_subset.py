#!/usr/bin/env python
# Select a subset from a UM fieldsfile
# -p option will select only the prognostic fields required for an initial
# dump and will also check some header fields.

# Output word size and endianness match input.

# This doesn't change the "written" date in a dump header.

# Martin Dix martin.dix@csiro.au

# TODO: Specify ranges for variables.
# Give a warning if field to be excluded is not found?

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

vlist = []
xlist = []
nfields = 9999999999
prognostic = False
section = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:n:o:psv:x:')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-n':
            nfields = int(opt[1])
        elif opt[0] == '-o':
            ofile = opt[1]
        elif opt[0] == '-p':
            prognostic = True
        elif opt[0] == '-s':
            section = True
        elif opt[0] == '-v':
            # Allow comma separated lists
            for v in opt[1].split(","):
                vlist.append(int(v))
        elif opt[0] == '-x':
            for v in opt[1].split(","):
                xlist.append(int(v))
except getopt.error:
    print "Usage: um_fields_subset.py -i ifile -o ofile [-p] [-s] [-v var] [-x var]"
    print "       -p include only prognostic (section 0,33,34) variables"
    print "       -s means -x and -v specify section rather than variable indices"
    print "       -v var1,var2,... to INCLUDE only these variables"
    print "       -x var1,var2,... to EXCLUDE only these variables"
    print "       Variables specified by STASH index = Section Number * 1000 + item number"
    sys.exit(2)

if vlist and xlist:
    raise Exception("Error: -x and -v are mutually exclusive")

if prognostic and (vlist or xlist):
    raise Exception("Error: -p incompatible with explicit list of variables")

def isprog(ilookup):
    # Check whether a STASH code corresponds to a prognostic variable.
    # Section 33 is tracers, 34 is UKCA
    # Also check whether variable is instantaneous, LBTIM < 10
    # No time processing  ilookup[LBPROC] == 0
    # Not a time series LBCODE < 30000
    return ilookup[ITEM_CODE]//1000 in [0,33,34] and ilookup[LBTIM] < 10 and ilookup[LBPROC] == 0 and ilookup[LBCODE] < 30000

def istracer(ilookup):
    return  ilookup[ITEM_CODE]//1000 == 33 and ilookup[LBTIM] < 10 and ilookup[LBPROC] == 0 and ilookup[LBCODE] < 30000

def match(code,vlist,section):
    if section:
        return code//1000 in vlist
    else:
        return code in vlist


f = umfile.UMFile(ifile)

g = umfile.UMFile(ofile, "w")
g.copyheader(f)
g.ilookup[:] = -99 # Used as missing value
g.rlookup[:] = np.fromstring(np.array([-99],g.int).tostring(),g.float)

# Initial check for packed fields that require the land-sea mask
needmask=False
masksaved = False
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99 or k >= nfields:
        break
    # Format is Section Number * 1000 + item number
    if ( prognostic and isprog(ilookup) or 
         vlist and match(ilookup[ITEM_CODE],vlist,section) or 
         xlist and not match(ilookup[ITEM_CODE],xlist,section) or 
         not prognostic and not vlist and not xlist ) :
        packing = [0, ilookup[LBPACK]%10, ilookup[LBPACK]//10 % 10,
                   ilookup[LBPACK]//100 % 10, ilookup[LBPACK]//1000 % 10,
                   ilookup[LBPACK]//10000]
        if packing[2]==2 and packing[3] in (1,2):
            needmask=True
        if ilookup[ITEM_CODE]==30:
            masksaved = True
        
if vlist and needmask and not masksaved:
    print "Adding land sea mask to output fields because of packed data"
    vlist.append(30)

# Loop over all the fields, counting the number of prognostic fields
kout = 0
nprog = 0
ntracer = 0
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    if ilookup[LBEGIN] == -99 or k >= nfields:
        break
    # Format is Section Number * 1000 + item number

    if ( prognostic and isprog(ilookup) or 
         vlist and match(ilookup[ITEM_CODE],vlist,section) or 
         xlist and not match(ilookup[ITEM_CODE],xlist,section) or 
         not prognostic and not vlist and not xlist ) :

        g.ilookup[kout,:] = ilookup[:]
        g.rlookup[kout,:] = f.rlookup[k,:]
        s = f.readfld(k,raw=True)
        g.writefld(s, kout, raw=True)
        # data = f.readfld(k)
        # g.writefld(data, kout)
        kout += 1
        if isprog(ilookup):
            nprog += 1
        if istracer(ilookup):
            # Should this also count UKCA fields as tracers?
            ntracer += 1

# To get correct number of tracer fields need to divide by number of levels
ntracer /= f.inthead[IC_TracerLevs]

# Set the header to be just large enough
g.fixhd[FH_LookupSize2] = kout
if g.fixhd[FH_NumProgFields] != nprog:
    print "Resetting no of prognostic fields from %d to %d" % (g.fixhd[FH_NumProgFields], nprog)
    g.fixhd[FH_NumProgFields] = nprog
if g.inthead[IC_TracerVars] != ntracer:
    print "Resetting no of tracer fields from %d to %d" % (g.inthead[IC_TracerVars], ntracer)
    g.inthead[IC_TracerVars] = ntracer
if ntracer > 0 and g.inthead[IC_TracerLevs] != g.inthead[IC_PLevels]:
    print "Resetting no of tracer levels from %d to %d" % ( g.inthead[IC_TracerLevs], g.inthead[IC_PLevels])
    g.inthead[IC_TracerLevs] = g.inthead[IC_PLevels]

g.close()
