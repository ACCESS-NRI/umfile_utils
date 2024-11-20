# Compare two files produced by um2netcdf4.py and variants

import sys, netCDF4, argparse, numpy as np

parser = argparse.ArgumentParser(description="Compare netcdf files from um2netcdf4.py")
parser.add_argument('-d', dest='strict_dims', action='store_true',
                    default=False, help="Strict comparison of dimensions")
parser.add_argument('-s', dest='strict', action='store_true',
                    default=False, help="Strict comparison")
parser.add_argument('file1', help='Input file1')
parser.add_argument('file2', help='Input file2')

args = parser.parse_args()

d1 = netCDF4.Dataset(args.file1)
d2 = netCDF4.Dataset(args.file2)

if args.strict:
    args.strict_dims = True

if args.strict_dims:
    # Compare dimensions
    dims1 = set(d1.dimensions.keys())
    dims2 = set(d2.dimensions.keys())

    if dims1 - dims2:
        print("File 1 has dimensions not in file 2:", dims1 - dims2)
    if dims2 - dims1:
        print("File 2 has dimensions not in file 1:", dims2 - dims1)
    if dims1.symmetric_difference(dims2):
        print("Common dimensions", dims1.intersection(dims2))
    for dim in dims1.intersection(dims2):
        if d1.dimensions[dim].size == d2.dimensions[dim].size:
            # Check values
            if dim == 'bnds':
                continue
            v1 = d1.variables[dim]
            v2 = d2.variables[dim]
            if not np.allclose(v1[:], v2[:]):
                diff = abs(v1[:] - v2[:])
                imax = np.unravel_index(diff.argmax(), diff.shape)
                print("Dimension values differ:", dim, imax, v1[imax], v2[imax])
        else:
            print("Dimension sizes differ:", dim, d1.dimensions[dim].size, d2.dimensions[dim].size)

# Get names of pressure dimensions and whether they're increasing or decreasing
d1inc = {}
d2inc = {}
for d in d1.dimensions:
    if d == 'bnds':
        continue
    v = d1.variables[d]
    if (hasattr(v,'long_name') and 'pressure' in v.long_name or
        hasattr(v,'standard_name') and 'pressure' in v.standard_name):
        if v[0] < v[-1]:
            d1inc[d] = True
        else:
            d1inc[d] = False
for d in d2.dimensions:
    if d == 'bnds':
        continue
    v = d2.variables[d]
    if (hasattr(v,'long_name') and 'pressure' in v.long_name or
        hasattr(v,'standard_name') and 'pressure' in v.standard_name):
        if v[0] < v[-1]:
            d2inc[d] = True
        else:
            d2inc[d] = False

print("d1inc:", d1inc)
print("d2inc:", d2inc)

# Expect variable names of form fld_*
vars1 = {v for v in d1.variables if v.startswith('fld_')}
vars2 = {v for v in d2.variables if v.startswith('fld_')}
if vars1 - vars2:
    print("File 1 has variables not in file 2:", vars1 - vars2)
if vars2 - vars1:
    print("File 2 has variables not in file 1:", vars2 - vars1)

for v in sorted(vars1.intersection(vars2)):
    v1 = d1.variables[v]
    v2 = d2.variables[v]
    # This might just be due to renaming of dimensions
    if args.strict_dims and v1.dimensions != v2.dimensions:
        print("Dimension mismatch:", v, v1.dimensions, v2.dimensions)
    if v1.shape == v2.shape:
        # Compare values
        # Is the vertical axis reversed. Assume this is always the second dimension
        if (v1.dimensions[1] in d1inc and v2.dimensions[1] in d2inc and
            d1inc[v1.dimensions[1]] ^ d2inc[v2.dimensions[1]]):
            print("Comparing %s with reversed pressure dimension" % v)
            v2 = v2[:,::-1]
        if not np.allclose(v1[:], v2[:]):
            diff = abs(v1[:] - v2[:])
            imax = np.unravel_index(diff.argmax(), diff.shape)
            print("Values differ:", v, imax, v1[imax], v2[imax])
        if v1[:].mask.sum() != v2[:].mask.sum():
            print("Number of masked points differs:", v, v1[:].mask.sum(), v2[:].mask.sum())
    else:
        print("Shape mismatch:", v, v1.shape, v2.shape)
