# Craete a new fieldsfile with any timeseries fields removed

import mule
import sys
from types import MethodType
# Modified version with the expected latitudes of the river field reversed
import validate_esm15_override

ff = mule.DumpFile.from_file(sys.argv[1])
ff_out = ff.copy()
num_ts = 0
for fld in ff.fields:
    # Check for the grid code that denotes a timeseries
    if fld.lbcode in (31320, 31323):
        num_ts += 1
    else:
        ff_out.fields.append(fld)

if num_ts > 0:
    print(f'{num_ts} timeseries fields skipped')
else:
    print('No timeseries fields found')

ff_out.validate = MethodType(validate_esm15_override.validate_umf, ff_out)

ff_out.to_file(sys.argv[2])
