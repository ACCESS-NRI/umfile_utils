# Calculate CPMIP complexity from CM2 UM restart.
# Ignore fields 376-286 from JULES snow scheme
# Ignore CABLE fields > 833
# Count tiled fields using 10751 land points

# For ESM don't skip any fields and count land as 10865

import mule, sys

ff = mule.DumpFile.from_file(sys.argv[1])
esm = True

tot = 0
for fld in ff.fields:
    if esm:
        if fld.lbpack == 120:
            tot += 10865
        else:
            tot += 145*192
    else:
        if 376 <= fld.lbuser4 <= 386 or 834 <= fld.lbuser4 <= 1000:
            continue
        if fld.lbpack == 120:
            tot += 10751
        else:
            tot += 144*192
    print(fld.lbuser4, fld.lbpack, tot)
print("TOT", tot)
