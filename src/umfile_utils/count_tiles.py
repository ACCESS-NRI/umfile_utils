# Total number of non-zero tiles in a land fraction ancillary file
import iris, sys

frac = iris.load_cube(sys.argv[1], iris.AttributeConstraint(STASH='m01s00i216'))
ftot = frac.data.sum(axis=0)
print("No of land points", (ftot >0).sum())
print("No of tiles", (frac.data > 0).sum())
