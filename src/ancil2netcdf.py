#!/usr/bin/env python

import iris, numpy as np, datetime, sys
import stashvar_cmip6 as stashvar
from iris.coords import CellMethod
from netCDF4 import default_fillvals

def fix_latlon_coord(cube):
    def _add_coord_bounds(coord):
        if len(coord.points) > 1:
            if not coord.has_bounds():
                coord.guess_bounds()
        else:
            # For length 1, assume it's global. guess_bounds doesn't work in this case
            if coord.name() == 'latitude':
                if not coord.has_bounds():
                    coord.bounds = np.array([[-90.,90.]])
            elif coord.name() == 'longitude':
                if not coord.has_bounds():
                    coord.bounds = np.array([[0.,360.]])

    lat = cube.coord('latitude')
    lat.var_name = 'lat'
    _add_coord_bounds(lat)
    lon = cube.coord('longitude')
    lon.var_name = 'lon'
    _add_coord_bounds(lon)

def cubewrite(cube, sman, verbose):

    if cube.data.dtype == 'float64':
        cube.data = cube.data.astype(np.float32)
    elif cube.data.dtype == 'int64':
        cube.data = cube.data.astype(np.int32)

    # Set the missing_value attribute. Use an array to force the type to match
    # the data type
    if cube.data.dtype.kind == 'f':
        fill_value = 1.e20
    else:
        # Use netCDF defaults
        fill_value = default_fillvals['%s%1d' % (cube.data.dtype.kind, cube.data.dtype.itemsize)]

    cube.attributes['missing_value'] = np.array([fill_value], cube.data.dtype)

    # Check whether any of the coordinates is a pseudo-dimension
    # with integer values and if so reset to int32 to prevent
    # problems with possible later conversion to netCDF3
    for coord in cube.coords():
        if coord.points.dtype == np.int64:
            coord.points = coord.points.astype(np.int32)

    try:
        # If time is a dimension but not a coordinate dimension, coord_dims('time') returns an empty tuple
        if tdim := cube.coord_dims('time'):
            # For fields with a pseudo-level, time may not be the first dimension
            if tdim != (0,):
                tdim = tdim[0]
                neworder = list(range(cube.ndim))
                neworder.remove(tdim)
                neworder.insert(0,tdim)
                if verbose > 1:
                    print("Incorrect dimension order", cube)
                    print("Transpose to", neworder)
                cube.transpose(neworder)
            sman.write(cube, zlib=True, complevel=4, unlimited_dimensions=['time'], fill_value=fill_value)
        else:
            tmp = iris.util.new_axis(cube,cube.coord('time'))
            sman.write(tmp, zlib=True, complevel=4, unlimited_dimensions=['time'], fill_value=fill_value)
    except iris.exceptions.CoordinateNotFoundError:
        # No time dimension (probably ancillary file)
        sman.write(cube, zlib=True, complevel=4, fill_value=fill_value)

def fix_cell_methods(mtuple):
    # Input is tuple of cell methods
    newm = []
    for m in mtuple:
        newi = []
        for i in m.intervals:
            # Skip the misleading hour intervals
            if i.find('hour') == -1:
                newi.append(i)
        n = CellMethod(m.method, m.coord_names, tuple(newi), m.comments)
        newm.append(n)
    return tuple(newm)

def process(infile, outfile, args):

    if args.include_list and args.exclude_list:
        raise Exception("Error: include list and exclude list are mutually exclusive")
    cubes = iris.load(infile)

    # Sort the list by stashcode
    def keyfunc(c):
        return c.attributes['STASH']
    cubes.sort(key=keyfunc)

    with iris.fileformats.netcdf.Saver(outfile, 'NETCDF4') as sman:

        # Add global attributes
        history = "File %s converted with acnil2netcdf.py at %s" % \
                    (infile, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sman.update_global_attributes({'history':history})
        sman.update_global_attributes({'Conventions':'CF-1.6'})

        for c in cubes:
            stashcode = c.attributes['STASH']
            itemcode = 1000*stashcode.section + stashcode.item
            if args.include_list and itemcode not in args.include_list:
                continue
            if args.exclude_list and itemcode in args.exclude_list:
                continue
            umvar = stashvar.StashVar(itemcode)
            if args.simple:
                c.var_name = 'fld_s%2.2di%3.3d' % (stashcode.section, stashcode.item)
            elif umvar.uniquename:
                c.var_name = umvar.uniquename
            if c.standard_name and umvar.standard_name:
                if c.standard_name != umvar.standard_name:
                    if args.verbose:
                        sys.stderr.write("Standard name mismatch %d %d %s %s\n" % \
                           (stashcode.section, stashcode.item, c.standard_name, umvar.standard_name) )
                    c.standard_name = umvar.standard_name
            if c.units and umvar.units:
                # Simple testing c.units == umvar.units doesn't
                # catch format differences because Unit type
                # works around them. repr isn't reliable either
                ustr = '%s' % c.units
                if ustr != umvar.units:
                    if args.verbose:
                        sys.stderr.write("Units mismatch %d %d %s %s\n" % \
                             (stashcode.section, stashcode.item, c.units, umvar.units) )
                    c.units = umvar.units
            # If there's no standard_name or long_name from iris
            # use one from STASH
            if not c.standard_name:
                if umvar.standard_name:
                    c.standard_name = umvar.standard_name
            if not c.long_name:
                if umvar.long_name:
                    c.long_name = umvar.long_name

            # Interval in cell methods isn't reliable so better to remove it.
            c.cell_methods = fix_cell_methods(c.cell_methods)
            try:
                fix_latlon_coord(c)
            except iris.exceptions.CoordinateNotFoundError:
                print('\nMissing lat/lon coordinates for variable (possible timeseries?)\n')
                print(c)
                raise Exception("Variable can not be processed")

            if args.verbose:
                print(c.name(), itemcode)
            cubewrite(c, sman, args.verbose)

if __name__ == '__main__':
    import sys, argparse
    parser = argparse.ArgumentParser(description="Convert UM ancillary file to netcdf")
    parser.add_argument('-v', '--verbose', dest='verbose',
                    action='count', default=0, help='verbose output (-vv for extra verbose)')
    parser.add_argument('--include', dest='include_list', type=int,
                        nargs = '+', help = 'List of stash codes to include')
    parser.add_argument('--exclude', dest='exclude_list', type=int,
                        nargs = '+', help = 'List of stash codes to exclude')
    parser.add_argument('--simple', dest='simple', action='store_true',
                    default=False, help="Use a simple names of form fld_s01i123.")
    parser.add_argument('infile', help='Input file')
    parser.add_argument('outfile', help='Output file')

    args = parser.parse_args()

    process(args.infile, args.outfile, args)
