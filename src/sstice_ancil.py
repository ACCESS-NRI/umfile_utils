# Set up master ancillary files for CAP from the PCMDI SST and ice
# netcdf files.

# Need to delete the global calendar attribute first
# ncatted -a calendar,global,d,, amipobs_sst.nc

import umfile, iris, sys, datetime
from um_fileheaders import *
import numpy as np

# iris.FUTURE.cell_datetime_objects = True
# Not working yet

# SST file
sst = iris.load_cube(sys.argv[1])

lon = sst.coord('longitude')
lat = sst.coord('latitude')
time = sst.coord('time')
dates = time.units.num2date(time.points)

f = umfile.UMFile('temp', "w")
f.int = np.int64
f.float = np.float64
f.wordsize=8
f.byteorder = '>' # Big endian
f.sectorsize = 1

f.createheader(15, 6)

f.fixhd[:] = f.missval_i # Initialise to missing

# Minimal fixed header
f.fixhd[FH_SubModel] = 1
f.fixhd[FH_VertCoord] = 1
f.fixhd[FH_HorizGrid] = 0 # Global
f.fixhd[FH_Dataset] = 4 # Ancillary
f.fixhd[FH_CalendarType] = 1 # Gregorian
f.fixhd[FH_GridStagger] = 3
f.fixhd[FH_AncilDataId] = 1 # Ancillary time series
f.fixhd[FH_ModelVersion] = 805

# Initial date
f.fixhd[FH_DTYear]    = dates[0].year
f.fixhd[FH_DTMonth]   = dates[0].month
f.fixhd[FH_DTDay]     = dates[0].day
f.fixhd[FH_DTHour]    = dates[0].hour
f.fixhd[FH_DTMinute] = f.fixhd[FH_DTSecond] = 0
daydiff = (
    datetime.datetime(dates[0].year,dates[0].month, dates[0].day) -
    datetime.datetime(dates[0].year,1,1) )
f.fixhd[FH_DTDayNo] = daydiff.days + 1

# Final date
f.fixhd[FH_VTYear]    = dates[-1].year
f.fixhd[FH_VTMonth]   = dates[-1].month
f.fixhd[FH_VTDay]     = dates[-1].day
f.fixhd[FH_VTHour]    = dates[-1].hour
f.fixhd[FH_DTMinute] = f.fixhd[FH_VTSecond] = 0
f.fixhd[FH_VTMinute:FH_VTDayNo+1] = 0
daydiff = (
    datetime.datetime(dates[-1].year,dates[-1].month, dates[-1].day) -
    datetime.datetime(dates[-1].year,1,1) )
f.fixhd[FH_VTDayNo] = daydiff.days + 1

# Monthly step
f.fixhd[FH_CTYear:FH_CTDayNo+1] = 0
f.fixhd[FH_CTMonth] = 1

f.fixhd[FH_DataSize] = sst.data.size

f.fixhd[FH_IntCSize] = 15
f.fixhd[FH_RealCSize] = 6

f.inthead = np.zeros(f.fixhd[FH_IntCSize], f.int) + f.missval_i
f.inthead[IC_XLen] = len(lon.points)
f.inthead[IC_YLen] = len(lat.points)
f.inthead[2] = len(dates) # Seems to be used in ancil files
f.inthead[14] = 1 # Number of field types in file
f.inthead[IC_PLevels] = 1

f.realhead = np.zeros(f.fixhd[FH_RealCSize], f.float) + f.missval_r
f.realhead[RC_LongSpacing] = lon.points[1] - lon.points[0]
f.realhead[RC_LatSpacing] = lat.points[1] - lat.points[0]
f.realhead[RC_FirstLong] = lon.points[0]
f.realhead[RC_FirstLat] = lat.points[0]
f.realhead[RC_PoleLong] = 0.
f.realhead[RC_PoleLat] = 90.

# Start integer header after the fixed header
f.fixhd[FH_IntCStart] = 257
f.fixhd[FH_RealCStart] = f.fixhd[FH_IntCStart] + f.fixhd[FH_IntCSize]
f.fixhd[FH_LookupStart] =  f.fixhd[FH_RealCStart] + f.fixhd[FH_RealCSize]
# Create lookup tables 
f.fixhd[FH_LookupSize1] = 64
f.fixhd[FH_LookupSize2] = sst.shape[0]

f.fixhd[FH_DataStart] = f.fixhd[FH_LookupStart] + \
    f.fixhd[FH_LookupSize1]*f.fixhd[FH_LookupSize2]

f.ilookup = np.zeros((f.fixhd[FH_LookupSize2], f.fixhd[FH_LookupSize1]), f.int)
f.rlookup = np.zeros((f.fixhd[FH_LookupSize2], f.fixhd[FH_LookupSize1]), f.float)

for k in range(sst.shape[0]):
    f.ilookup[k,MODEL_CODE] = 1
    f.ilookup[k,ITEM_CODE] = 24 # Surface temperature
    f.ilookup[k,LBPACK] = 2
    f.ilookup[k,LBYR]  = f.ilookup[k,LBYRD]  = dates[k].year
    f.ilookup[k,LBMON] = f.ilookup[k,LBMOND] = dates[k].month
    f.ilookup[k,LBDAT] = f.ilookup[k,LBDATD] = dates[k].day
    f.ilookup[k,LBHR]  = f.ilookup[k,LBHRD]  = dates[k].hour
    # Day no relative to the start of the year (matches what CAP
    # produces) 
    daydiff = (
       datetime.datetime(dates[k].year,dates[k].month, dates[k].day) -
       datetime.datetime(dates[k].year,1,1) )
    f.ilookup[k,LBDAY] = f.ilookup[k,LBDAYD] = daydiff.days + 1

    # For ancillary files at least
    f.ilookup[k,LBTIM] = f.fixhd[FH_CalendarType]
    f.ilookup[k,LBCODE] = 1
    f.ilookup[k,LBHEM] = 0
    f.ilookup[k,LBREL] = 2 # Header release version <= vn8.0
    f.ilookup[k,LBVC] = 129 # Surface
    f.ilookup[k,DATA_TYPE] = 1 # Real
    f.ilookup[k,LBROW] = len(lat.points)
    f.ilookup[k,LBNPT] = len(lon.points)

    f.rlookup[k,BPLAT] = f.realhead[RC_PoleLat] 
    f.rlookup[k,BPLON] = f.realhead[RC_PoleLong] 
    f.rlookup[k,BZY] = f.realhead[RC_FirstLat] - f.realhead[RC_LatSpacing]
    f.rlookup[k,BDY] = f.realhead[RC_LatSpacing]
    f.rlookup[k,BZX] = f.realhead[RC_FirstLong] - f.realhead[RC_LongSpacing]
    f.rlookup[k,BDX] = f.realhead[RC_LongSpacing]

    f.rlookup[k,BMDI] = f.missval_r
    f.rlookup[k,BMKS] = 1.0

    # Better way to do this on creation?
    f.rlookup[k] = f.rlookup[k].newbyteorder('>')

    f.writefld(sst.data[k],k)

f.close()
