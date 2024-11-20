# Add stashmaster names to iris cube or cubelist

from stashvar import atm_stashvar

def _add_name(cube):
    code = cube.attributes['STASH']
    stashcode = code.section*1000 + code.item
    try:
        cube.stash_name = atm_stashvar[stashcode][0]
    except KeyError:
        cube.stash_name = 'Unknown'
    # Also add to the attributes directory so that it shows
    # when cube is printed.
    cube.attributes['stash_name'] = cube.stash_name
    
def add_stashname(cubes):
    if isinstance(cubes,list):
        for c in cubes:
            _add_name(c)
    else:
        _add_name(cubes)

