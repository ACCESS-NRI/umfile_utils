# Add fields to a dump file to allow warm restart with extra
# diagnostics. Uses a list of pairs of stashcodes, (present, new)
# where fields with the "present" stashcode are copied to the "new"
# stashcode and zeroed.

import mule
from operator import attrgetter
from mule.operators import ScaleFactorOperator
import sys

zero_operator = ScaleFactorOperator(0.0)

ff = mule.DumpFile.from_file(sys.argv[1])

# codes = {1207:1202, 3287:3314}
# For Roger's AMIP run new fields are
newlist = [34102, 34104, 34105, 34106, 34108, 34109, 34110, 34111,
           34114, 34115, 34116, 34117, 34120, 34121, 34126]
# and can all be taken from 34072
codes = {34072: newlist}

newflds = []
for fld in ff.fields:
    # lbtim > 10 restricts this to diagnostic variables
    if fld.lbuser4 in codes and fld.lbtim > 10:
        if isinstance(codes[fld.lbuser4],list):
            tmplist = codes[fld.lbuser4]
        else:
            tmplist = [codes[fld.lbuser4]]
        for code in tmplist:
            tmp = fld.copy()
            tmp.lbuser4 = code
            newflds.append(zero_operator(tmp))

# To keep proper ordering of the dump file take all the prognostic
# fields with lbtim < 10 first

ff_out = ff.copy()
for k, fld in enumerate(ff.fields):
    if fld.lbtim < 10:
        ff_out.fields.append(fld)
    else:
        break

# Assume sort is stable for the rest
remaining = ff.fields[k:] + newflds

remaining.sort(key=attrgetter('lbuser4'))

ff_out.fields += remaining

ff_out.to_file(sys.argv[2])
