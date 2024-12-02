# Find reason for mismatch in number of prognostic fields.
# Compare model output that lists the expected fields with the
# fields in the astart file

# Expected fields start with
# No of objects in this submodel:                    197
#       Type Modl Sect Item   Address   Length Levels Gridtype Halotype
#    1    0    1    0    2          1  1083684    38     18       1

# Arguments are model output and restart file

import sys, umfile, collections
from um_fileheaders import *

lines = open(sys.argv[1]).readlines()

# Expected fields
header_found = False
for k, l in enumerate(lines):
    if l.lstrip().startswith("No of objects in this submodel"):
        header_found = True
        break

if not header_found:
    print("Error - header line not found in %s" % (sys.argv[1]))
    print("Expecting line starting with 'No of objects in this submodel'")
    sys.exit(1)

# Now look for line starting with 1
k += 1
while not lines[k].lstrip().startswith("1 "):
    k += 1

expected = {}
while True:
    fields = lines[k].split()
    if len(fields) < 10 or fields[1] != '0':
        break
    # Stashcode and number of levels
    expected[int(fields[4])] = int(fields[7])
    k += 1

# Now look at the restart file
f = umfile.UMFile(sys.argv[2])
if not f.fieldsfile:
    print("Error: %s is not a UM fieldsfile")
    sys.exit(1)

start_fields = collections.defaultdict(int)
for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break
    if umfile.isprog(ilookup):
        start_fields[ilookup[ITEM_CODE]] += 1


print("No. of prognostic fields in start file:", sum(start_fields.values()))
nexpect = sum(expected.values())
print("Expected no. of prognostic fields:     ", nexpect)

expt = set(expected.keys())
rest = set(start_fields.keys())

# Fields missing from restart
missing = expt-rest
unexpected = rest-expt
if missing:
    print("\nFields missing from restart", sorted(missing))
if unexpected:
    print("\nUnexpected fields in restart", sorted(unexpected))
for fld in expt.intersection(rest):
    if expected[fld] != start_fields[fld]:
        print("Mismatch in number of fields with code", fld, expected[fld], start_fields[fld])
