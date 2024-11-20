# Flip UM ancillary file NS. Note that this works in-place in the given file
# Martin Dix martin.dix@csiro.au


from um_fileheaders import *
import umfile, sys

f = umfile.UMFile(sys.argv[1], 'r+')

print(f.realhead)
f.realhead[RC_FirstLat] = -f.realhead[RC_FirstLat]

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    rlookup = f.rlookup[k]
    if ilookup[LBEGIN] == -99:
        break
    rlookup[BZY] *= -1
    rlookup[BDY] *= -1
    data = f.readfld(k)
    f.writefld(data[::-1],k)

f.close()
