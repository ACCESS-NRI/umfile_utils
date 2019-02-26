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

codes = {1207:1202, 3287:3314}

newflds = []
for fld in ff.fields:
    if fld.lbuser4 in codes:
        tmp = fld.copy()
        tmp.lbuser4 = codes[fld.lbuser4]
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
