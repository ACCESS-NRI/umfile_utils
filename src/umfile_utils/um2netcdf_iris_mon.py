# This version excludes the monthly diurnal cycle variables
from __future__ import print_function
import iris, numpy as np, datetime, sys, re
import stashvar
from iris.coords import CellMethod
import cf_units, cftime

iris.FUTURE.netcdf_no_unlimited = True

def convert_proleptic(time):
    # Convert from hour to days and shift origin from 1970 to 0001
    t0 = cftime.DatetimeProlepticGregorian(1,1,1)
    # datetime gets handled like proleptic gregorian so simple difference works
    # Need a copy because can't assign to time.points[i]
    tvals = np.array(time.points)
    tbnds = np.array(time.bounds)
    for i in range(len(time.points)):
        delta = time.units.num2date(tvals[i]) - t0
        tvals[i] = delta.days + delta.seconds/86400.
        delta = time.units.num2date(tbnds[i][0]) - t0
        tbnds[i][0] = delta.days + delta.seconds/86400.
        delta = time.units.num2date(tbnds[i][1]) - t0
        tbnds[i][1] = delta.days + delta.seconds/86400.
    time.points = tvals
    time.bounds = tbnds
    time.units = cf_units.Unit("days since 0001-01-01 00:00", calendar='proleptic_gregorian')

def cubewrite(cube,sman,compression):
    try:
        plevs = cube.coord('pressure')
        if plevs.points[0] < plevs.points[-1]:
            # Flip (assuming pressure is first index)
            plevs.attributes['positive'] = 'down'
            # Otherwise they're off by 1e-10 which looks odd in
            # ncdump
            plevs.points = np.round(plevs.points,5)
            if cube.coord_dims('pressure') == (0,):
                cube = cube[::-1]
    except iris.exceptions.CoordinateNotFoundError:
        pass
    if cube.data.dtype == 'float64':
        cube.data = cube.data.astype(np.float32)

    # If reference date is before 1600 use proleptic gregorian
    # calendar and change units from hours to days
    time = cube.coord('time')
    reftime = cube.coord('forecast_reference_time')
    refdate = reftime.units.num2date(reftime.points[0])
    if time.units.calendar=='gregorian':
        assert time.units.origin == 'hours since 1970-01-01 00:00:00'
        if refdate.year < 1600:
            convert_proleptic(time)
        else:
            time.units = cf_units.Unit("days since 1970-01-01 00:00", calendar='proleptic_gregorian')
            time.points = time.points/24.
            time.bounds = time.bounds/24.
        cube.remove_coord('forecast_period')
        cube.remove_coord('forecast_reference_time')

    # Check whether any of the coordinates is a pseudo-dimension
    # with integer values and if so reset to int32 to prevent
    # problems with possible later conversion to netCDF3
    for coord in cube.coords():
        if coord.points.dtype == np.int64:
            coord.points = coord.points.astype(np.int32)

    try:
        if cube.coord_dims('time'):
            sman.write(cube, zlib=True, complevel=compression, unlimited_dimensions=['time'])
        else:
            tmp = iris.util.new_axis(cube,cube.coord('time'))
            sman.write(tmp, zlib=True, complevel=compression, unlimited_dimensions=['time'])
    except iris.exceptions.CoordinateNotFoundError:
        # No time dimension (probably ancillary file)
        sman.write(cube, zlib=True, complevel=compression)

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

def bounds_callback(cube,field,filename):
    # This skips the monthly diurnal cycle variables from the UM
    m = cube.cell_methods[0]
    if m.intervals == ('24 hour',):
        raise iris.exceptions.IgnoreCubeException()

def process(infile,outfile,verbose=False,nckind=3,compression=4,nomask=False,include_list=None,exclude_list=None):

    if include_list and exclude_list:
        raise Exception("Error: include list and exclude list are mutually exclusive")
    cubes = iris.load(infile,callback=bounds_callback)

    # Sort the list by stashcode
    def keyfunc(c):
        return c.attributes['STASH']
    cubes.sort(key=keyfunc)

    # Check whether there are any pressure level fields that should be
    # masked. Can use temperature to mask instantaneous fields, so really
    # should check whether these are time means
    need_heaviside = False
    have_heaviside = False
    hcrit = 0.5
    for c in cubes:
        stashcode = c.attributes['STASH']
        if stashcode.section == 30 and 201 <= stashcode.item <= 303:
            need_heaviside = True
        if stashcode.section == 30 and stashcode.item == 301:
            have_heaviside = True
            heaviside = c

    if not nomask and need_heaviside and not have_heaviside:
        print("""Warning - heaviside field needed for masking pressure level data is not present.
    These fields will be skipped""")

    nc_formats = {1: 'NETCDF3_CLASSIC', 2: 'NETCDF3_64BIT',
                  3: 'NETCDF4', 4: 'NETCDF4_CLASSIC'}
    with iris.fileformats.netcdf.Saver(outfile, nc_formats[nckind]) as sman:

        # Add global attributes
        history = "File %s with converted with um2netcdf_iris_mon.py at %s" % (infile, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sman.update_global_attributes({'history':history})
        sman.update_global_attributes({'Conventions':'CF-1.6'})

        for c in cubes:
            stashcode = c.attributes['STASH']
            itemcode = 1000*stashcode.section + stashcode.item
            if include_list and itemcode not in include_list:
                continue
            if exclude_list and itemcode in exclude_list:
                continue
            umvar = stashvar.StashVar(itemcode)
            if umvar.uniquename:
                c.var_name = umvar.uniquename
                # Could there be cases with both max and min?
                if any([m.method == 'maximum' for m in c.cell_methods]):
                    c.var_name += "_max"
                if any([m.method == 'minimum' for m in c.cell_methods]):
                    c.var_name += "_min"
            # The iris name mapping seems wrong for these - perhaps assuming rotated grids?
            if c.standard_name == 'x_wind':
                c.standard_name = 'eastward_wind'
            if c.standard_name == 'y_wind':
                c.standard_name = 'northward_wind'
            if c.standard_name and umvar.standard_name:
                if c.standard_name != umvar.standard_name:
                    if verbose:
                        sys.stderr.write("Standard name mismatch %d %d %s %s\n" % (stashcode.section, stashcode.item, c.standard_name, umvar.standard_name) )
                    c.standard_name = umvar.standard_name
            if c.units and umvar.units:
                # Simple testing c.units == umvar.units doesn't
                # catch format differences becuase Unit type
                # works around them. repr isn't reliable either
                ustr = '%s' % c.units
                if ustr != umvar.units:
                    if verbose:
                        sys.stderr.write("Units mismatch %d %d %s %s\n" % (stashcode.section, stashcode.item, c.units, umvar.units) )
                    c.units = umvar.units
            # Temporary work around for xconv
            if c.long_name and len(c.long_name) > 110:
                c.long_name = c.long_name[:110]
            # If there's no standard_name or long_name from iris
            # use one from STASH
            if not c.standard_name:
                if umvar.standard_name:
                    c.standard_name = umvar.standard_name
            if not c.long_name:
                if umvar.long_name:
                    c.long_name = umvar.long_name

            # Interval in cell methods isn't reliable so better to
            # remove it.
            c.cell_methods = fix_cell_methods(c.cell_methods)

            if stashcode.section == 30 and stashcode.item == 301:
                continue
            if not nomask and stashcode.section == 30 and 201 <= stashcode.item <= 303:
                # Pressure level data should be masked
                if have_heaviside:
                    # Temporarily turn off warnings from 0/0
                    with np.errstate(divide='ignore',invalid='ignore'):
                        c.data = np.ma.masked_array(c.data/heaviside.data, heaviside.data <= hcrit).astype(np.float32)
                else:
                    continue
            if verbose:
                print(c.name(), itemcode)
            cubewrite(c,sman,compression)

if __name__ == '__main__':
    import sys, argparse
    parser = argparse.ArgumentParser(description="Convert UM fieldsfile to netcdf")
    parser.add_argument('-k', dest='kind', required=False, type=int,
                        default=3, help='specify kind of netCDF format for output file: 1 classic, 2 64-bit offset, 3 netCDF-4, 4 netCDF-4 classic model. Default 3', choices=[1,2,3,4])
    parser.add_argument('-c', dest='compression', required=False, type=int,
                        default=4, help='compression level (0=none, 9=max). Default 4')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    default=False, help='verbose output')
    parser.add_argument('--include', dest='include', type=int,
                        nargs = '+', help = 'List of stash codes to include')
    parser.add_argument('--exclude', dest='exclude', type=int,
                        nargs = '+', help = 'List of stash codes to exclude')
    parser.add_argument('--nomask', dest='nomask', action='store_true',
                    default=False, help="Don't apply heaviside function mask to pressure level fields")
    parser.add_argument('infile', help='Input file')
    parser.add_argument('outfile', help='Output file')

    args = parser.parse_args()

    process(args.infile,args.outfile,args.verbose,args.kind,args.compression,args.nomask,args.include,args.exclude)
