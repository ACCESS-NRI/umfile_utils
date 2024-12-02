# Plot a land mask and interactively flip points. Output a list
# of changes.

# For a global grid need to work around quirks of iris treating 
# longitude range as -180 to 180

from __future__ import division, print_function
import iris
import iris.plot as iplt
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import argparse, sys
from matplotlib.colors import BoundaryNorm

parser = argparse.ArgumentParser(description="Interactvely edit a UM land-sea mask")
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', 
                    default=False, help='verbose output')

parser.add_argument('maskfile', nargs='?', help='Input mask file (default qrparm.mask)', default='qrparm.mask')
parser.add_argument('-m', dest='mapres', required=False, default='m', help='Map resolution', choices='almh')
parser.add_argument('-o', dest='outfile', type=argparse.FileType('w'), help='Output file for corrections (default is standard out)', default=sys.stdout)

args = parser.parse_args()

mask = iris.load_cube(args.maskfile)

global fmask, lon, lat, nlon, nlat, cyclic, changed
# Global files have latitude, longitude, 
# LAMs have grid_latitude, grid_longitude
lat, lon = mask.dim_coords
nlat, nlon = mask.shape
cyclic = lon.circular

if mask.data.min() < 0:
    # Plots better when flipped
    mask.data = -1*mask.data

# 4th value is never used for some reason
cmap = matplotlib.colors.ListedColormap(((0.3,0.3,1),(0.7,0.7,1),(0,0.65,0),(1,1,0),(0.,0.35,0)))

changed = False

if cyclic:
    crs = ccrs.PlateCarree(central_longitude=180)
else:
    crs = ccrs.PlateCarree()

ax = plt.axes(projection=crs)

def draw_GAcoast(ax,coastcolor='black'):
    # http://www.ga.gov.au/metadata-gateway/metadata/record/61395/
    # MapInfo Interchange format
    f = open('cstauscd_l.mif')
    desc = open('cstauscd_l.mid')

    l = f.readline()
    while l[:4] != "DATA":
        l = f.readline()

    minlon, maxlon = ax.get_xlim()
    minlat, maxlat = ax.get_ylim()

    while True:
        l = f.readline()
        if not l:
            break
        dline = desc.readline()
        # Exclude State border and tile edge line segements
        coast = dline.find("coastline") > 0
        if l.startswith("PLINE"):
            n = int(l[5:])
            lon = []
            lat = []
            for i in range(n):
                l = f.readline()
                lon.append(float(l.split()[0]))
                lat.append(float(l.split()[1]))
                if coast and min(lat) <= maxlat and max(lat) >= minlat and \
                             min(lon) <= maxlon and max(lon) >= minlon :
                    ax.plot(lon,lat,linewidth=1,color=coastcolor)
        elif l.startswith("LINE"):
            s = l.split()
            lon = [float(s[1]), float(s[3])]
            lat = [float(s[2]), float(s[4])]
            if coast and min(lat) <= maxlat and max(lat) >= minlat and \
                             min(lon) <= maxlon and max(lon) >= minlon :
                ax.plot(lon,lat,linewidth=1,color=coastcolor)

global PM
# cmap = plt.get_cmap('PiYG')
norm = BoundaryNorm([-1,0,1,2,3], ncolors=cmap.N, clip=True)
PM = iplt.pcolormesh(mask, cmap=cmap, norm=norm)

if args.mapres == 'a':
    draw_GAcoast(ax)
elif args.mapres == 'l':
    ax.coastlines(resolution='110m')
elif args.mapres == 'h':
    ax.coastlines(resolution='10m')
else:
    ax.coastlines(resolution='50m')

ax.gridlines(linestyle='--', draw_labels=True, alpha=0.5)

# Make a copy so can see what's changed later
# (PM.set_array alters mask.data for LAMs)
origmask = np.array(mask.data[:])

def grid_callback(ax):
    # Try to sensibly redraw the grid lines when the map is zoomed.
    xt = ax.get_xticks()
    yt = ax.get_yticks()
    # print("Orig",xt)
    if cyclic:
        for i in range(len(xt)):
            if xt[i] < 0:
                xt[i] = 180 + xt[i]
            else:
                xt[i] = xt[i] - 180
    # print("New ",xt)
    # Get rid of the old lines (doesn't seem to work)
    ax._gridliners = []
    ax.gridlines(linestyle='--', draw_labels=True, xlocs=xt, ylocs=yt, alpha=0.5)

# From the image_zcoord example
def format_coord(x, y):

    global lon, lat, cyclic
    if cyclic:
        x += 180.
    i = lon.nearest_neighbour_index(x)
    j = lat.nearest_neighbour_index(y)
    return 'lon=%1.4f, lat=%1.4f, [%d,%d]'%(x, y, j, i)

ax.format_coord = format_coord
ax.callbacks.connect('xlim_changed', grid_callback)
ax.callbacks.connect('ylim_changed', grid_callback)

# http://matplotlib.org/1.3.1/users/event_handling.html
def onclick(event):
    # Disable click events if using the zoom & pan modes.
    # Need to turn off zoom to restore the clicking
    if plt.gcf().canvas.widgetlock.locked():
        return
    if args.verbose:
        print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' % (
            event.button, event.x, event.y, event.xdata, event.ydata))
    global fmask, lon, lat, PM, nlon, nlat, changed
    if cyclic:
        # Underlying plot still starts at -180, so fix the coordinate offset
        i = lon.nearest_neighbour_index(event.xdata+180)
    else:
        i = lon.nearest_neighbour_index(event.xdata)
    j = lat.nearest_neighbour_index(event.ydata)
    changed = True
    fmask = PM.get_array()
    if cyclic:
        fmask.shape = (nlat,nlon+1)
    else:
        fmask.shape = (nlat,nlon)
    # To make visible which points have been flipped, set new land
    # to 2, new ocean to -1
    if fmask[j,i] == 1:
        fmask[j,i] = -1
    elif fmask[j,i] == 0:
        fmask[j,i] = 2
    elif fmask[j,i] == -1:
        # Flip back to original
        fmask[j,i] = 1
    elif fmask[j,i] == 2:
        fmask[j,i] = 0
#   http://wiki.scipy.org/Cookbook/Matplotlib/Animations
    PM.set_array(fmask[:,:].ravel())
    plt.draw()
    
cid = plt.gcf().canvas.mpl_connect('button_press_event', onclick)
plt.show()

if changed:

    if cyclic:
        # Remove the extra longitude
        fmask = fmask[:,:-1]

    # Now save a list of the changed points for CAP
    print("Number of points changed", np.sum(fmask != origmask))

    # Need to flip the order here to N-S.
    orig = origmask[::-1].ravel()
    new = fmask[::-1].ravel()

    for k in range(len(orig)):
        if orig[k] != new[k]:
            if new[k] == -1: # Flipped ocean value
                status = ".FALSE."
            else:
                status = ".TRUE."
            args.outfile.write("&DATAC FIELD_NO=1, POINT_NO=%d, DATA_NEW=%s /\n" % \
                     (k+1, status))

