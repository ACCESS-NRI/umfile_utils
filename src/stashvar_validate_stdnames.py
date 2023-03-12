# Check that the standard names set in stashvar are valid according to iris
# and highlight any that aren't set

# import stashvar
import stashvar_cmip6 as stashvar
from iris._cube_coord_common import get_valid_standard_name
from iris.fileformats.um_cf_map import STASH_TO_CF

for v, properties in stashvar.atm_stashvar.items():
    units = properties[2]
    std_name = properties[3]
    if std_name and not get_valid_standard_name(std_name):
        print("Invalid", v, std_name)
    item = v % 1000
    section = v // 1000
    key = 'm01s%2.2di%3.3d' % (section, item)
    if key in STASH_TO_CF:
        if STASH_TO_CF[key].standard_name and std_name and STASH_TO_CF[key].standard_name != std_name:
            print("Name mismatch", v, std_name, STASH_TO_CF[key].standard_name)
        if STASH_TO_CF[key].units and units and STASH_TO_CF[key].units != units:
            print("Units mismatch", v, units, STASH_TO_CF[key].units)