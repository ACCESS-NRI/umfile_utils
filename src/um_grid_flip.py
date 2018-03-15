# Flip UM ancillary file NS
# Assume 64 bit IEEE big endian

# Martin Dix martin.dix@csiro.au


import Numeric as N
import getopt, sys

verbose = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:o:v')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-o':
            ofile = opt[1]
        elif opt[0] == '-v':
            verbose = True
except getopt.error:
    print "Usage: um_grid_flip.py -i ifile -o ofile"
    sys.exit(2)

f = open(ifile)
g = open(ofile, "w")

# Fixed length header
fpos = 0
s = f.read(256*8)
fpos += 256
fixhd = N.fromstring(s,N.Int64).byteswapped()

#print "Grid", fixhd[3]
#print "Calendar", fixhd[7]

# g.write(x.tostring())
g.write(s)

# Start and length of integer constants
int_start = fixhd[99]
if int_start != fpos+1:
    raise "Unexpected start of integer header"
nint = fixhd[100]
# print "NINT", nint

s = f.read(nint*8)
fpos += nint
g.write(s)

# Start and length of real constants
real_start = fixhd[104]
if real_start != fpos+1:
    raise "Unexpected start of integer header"
nreal = fixhd[105]
# print "NREAL", nreal

s = f.read(nreal*8)
fpos += nreal
x = N.fromstring(s,N.Float64).byteswapped()
if verbose:
    print "Real header at byte", real_start*8
    print "REAL HEADER", x
# Flip
x[2] = -90.
g.write(x.byteswapped().tostring())

# Level dependent constants section may be empty
lev_start = fixhd[109]
if lev_start != -32768:
    if lev_start != fpos+1:
        raise "Unexpected start of level dependent constants %d %d " % (lev_start, fpos+1)
    nlconst = fixhd[110]*fixhd[111]
    s =f.read(nlconst*8)
    fpos += nlconst
    g.write(s)

# Expect next several sections to be empty, shown by start = 0 or -32768 
if not ( fixhd[114] <= 0 and fixhd[119] <= 0 and fixhd[124] <= 0 and
         fixhd[129] <= 0 and fixhd[134] <= 0 and fixhd[139] <= 0 and
         fixhd[141] <= 0 and fixhd[143] <= 0 ):
    print fixhd[114], fixhd[119], fixhd[124], fixhd[129], fixhd[134], fixhd[139], fixhd[141], fixhd[143]
    raise "Unexpected non-empty constant section"

# Lookup table
lookup_start = fixhd[149]
if lookup_start != fpos+1:
    raise "Unexpected start of lookup table"
lookdim1 = fixhd[150]
lookdim2 = fixhd[151]

if verbose:
    print "LOOKDIM", lookdim1, lookdim2
# Read lookup
s = f.read(lookdim1*lookdim2*8)
fpos += lookdim1*lookdim2

# The lookup table has separate integer 1;45 and real 46-64 sections
# Simplest to have duplicate integer and real versions and just index
# into the appropriate parts
if lookdim1 != 64:
    raise "Unexpected lookup table dimension"

ilookup = N.reshape( N.fromstring(s, N.Int64).byteswapped(), [lookdim2, lookdim1])
rlookup = N.reshape( N.fromstring(s, N.Float64).byteswapped(), [lookdim2, lookdim1])

#print ilookup.shape
#for k in range(2):
#    print ilookup[k, :45]
#    print rlookup[k, 45:]

rlookup[:,55] = 90.
rlookup[:,58] = -rlookup[:,58] 
rlookup[:,59] = -rlookup[:,59] 
g.write(rlookup.byteswapped().tostring())

# print ilookup[5000, :]
# print rlookup[5000, 45:]

# Start of data
dstart = fixhd[159]

# print "START", dstart, fpos

# Now need to read up to the start (could just pad)
s = f.read( (dstart - (fpos+1))*8)
fpos += dstart - (fpos+1)
g.write(s)         

# print " NOW POS", dstart, fpos

# Loop over all the fields
kout = 0
kount = dstart-1 # dstart is index rather than offset
for k in range(lookdim2):
    size = ilookup[k,14]
    lbegin = ilookup[k,28] # lbegin is offset from start
    lbnrec = ilookup[k,29] # Actual size
    nlat = ilookup[k,17]
    nlon = ilookup[k,18]
    print "Array", nlat, nlon
    if lbegin == -99:
        break
    f.seek(lbegin*8)
    print "Number of words", lbnrec
    s = f.read(lbnrec*8)
    data = N.reshape( N.fromstring(s[:8*nlat*nlon], N.Float64).byteswapped(), [nlat, nlon])
    print data.shape
    newdata = data[::-1]
    g.seek(kount*8)
    g.write(newdata.byteswapped().tostring())
    g.write(s[8*nlat*nlon:])
    kout += 1
    kount += lbnrec

g.close()
