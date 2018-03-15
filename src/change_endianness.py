# Swap endianness of UM fieldsfile or ancillary file

# Martin Dix martin.dix@csiro.au


import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:o:')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-o':
            ofile = opt[1]
except getopt.error:
    print "Usage: change_endianness.py -i ifile -o ofile"
    sys.exit(2)

f = umfile.UMFile(ifile)

g = umfile.UMFile(ofile, "w")
g.copyheader(f)
g.rlookup = g.rlookup.byteswap()

# Set output byteorder to be opposite of input
if f.byteorder == '>':
    g.byteorder = '<'
elif f.byteorder == '<':
    g.byteorder = '>'
else:
    # Native
    if sys.byteorder == 'little':
        g.byteorder = '>' # Big
    else:
        g.byteorder = '<'

# If native byteorder set that rather than '<' or '>' to match what np.dtype uses.
if (g.byteorder == '<' and sys.byteorder == 'little') or \
   (g.byteorder == '>' and sys.byteorder == 'big'):
    g.byteorder = '='
    
print "Byte orders", f.byteorder, g.byteorder

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    data = f.readfld(k)
    # Why does this have to be explicit?
    g.writefld(data,k)
    
g.close()
