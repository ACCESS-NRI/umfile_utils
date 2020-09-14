# Check that the standard names set in stashvar are valid according to iris

# import stashvar
import stashvar_cmip6 as stashvar
from iris._cube_coord_common import get_valid_standard_name

for v, properties in stashvar.atm_stashvar.items():
    std_name = properties[3]
    if std_name and not get_valid_standard_name(std_name):
        print("Invalid", v, std_name)