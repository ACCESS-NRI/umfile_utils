from __future__ import print_function
from um_fileheaders import *
import numpy as np
from six.moves import builtins
import types

class umfile_error(Exception):
    pass

class packerr(Exception):
    pass

class UMFile():
    # Should this inherit from io.something?
    """ Extended version of file class that uses 8 byte words """

    missval_i = -32768
    missval_r = -1073741824

    def __init__(self, filename, mode=None):
        if not mode:
            mode = 'rb'
        if not "b" in mode:
            mode += "b"
        self.fileobj = builtins.open(filename, mode)
        if "r" in mode:
            self.determine_file_type()
            self.readheader()
            self.readlookup()
            self.sectorsize = self.getsectorsize()
        self.mask = None
        self.nland = None
        
    def close(self):
        # Unless file was opened readonly, need to write the new header
        # information before closing.
        if not self.fileobj.mode == 'r':
            self.writeheader()
            self.writelookup()
        self.fileobj.close()
        
    def wordseek(self,offset):
        self.fileobj.seek(offset*self.wordsize)

    def wordread(self,size):
        return self.fileobj.read(size*self.wordsize)

    def arraywrite(self,array):
        # Could use tofile here, but no real advantage.
        # Need to check whether the native format is big or little
        # Here assuming little
        if array.dtype.byteorder == self.byteorder:
            return self.fileobj.write(array.tobytes())
        else:
            return self.fileobj.write(array.byteswap().tobytes())

    def determine_file_type(self):
        # Get word length and byte order?
        # Read first 16 bytes and try to interpret in various ways
        self.fileobj.seek(0)
        s = self.fileobj.read(16)
        # For a UM fieldsfile, first word should be 20 and second 1, 2, or 4
        # For ancillary file first word -32768
        # Include = in the test to make output easier
        self.fieldsfile = False
        self.ppfile = False
        for endian in ('=', '>', '<'):
            h = np.fromstring(s,np.int64).newbyteorder(endian)
            # print "testing 64 bit", h[:2]
            if h[0] in [15, 20, -32768] and h[1] in (1, 2, 4):
                self.byteorder = endian
                self.wordsize = 8
                self.int = np.int64
                self.float = np.float64
                self.fieldsfile = True
                return
            h = np.fromstring(s,np.int32).newbyteorder(endian)
            # print "testing 32 bit", h[:2]
            if h[0] in [15, 20, -32768] and h[1] in (1, 2, 4):
                self.byteorder = endian
                self.wordsize = 4
                self.int = np.int32
                self.float = np.float32
                self.fieldsfile = True
                return
            if h[0] == 256:
                self.byteorder = endian
                self.wordsize = 4
                self.int = np.int32
                self.float = np.float32
                self.ppfile = True
                return
        raise umfile_error("Error - file type not determined")
        
    def readheader(self):
        if not self.fieldsfile:
            return
        self.fileobj.seek(0)
        # Fixed length header of length 256
        s = self.wordread(256)
        self.fixhd = np.fromstring(s,self.int).newbyteorder(self.byteorder)

        # Integer constants
        self.wordseek(self.fixhd[FH_IntCStart]-1)
        nint = self.fixhd[FH_IntCSize]
        s = self.wordread(nint)
        self.inthead = np.fromstring(s,self.int).newbyteorder(self.byteorder)

        # Real constants
        self.wordseek(self.fixhd[FH_RealCStart]-1)
        nreal = self.fixhd[FH_RealCSize]
        s = self.wordread(nreal)
        self.realhead = np.fromstring(s,self.float).newbyteorder(self.byteorder)

        # Level dependent constants
        if self.fixhd[FH_LevDepCStart] > 0:
            self.wordseek(self.fixhd[FH_LevDepCStart]-1)
            nlconst = self.fixhd[FH_LevDepCSize1]*self.fixhd[FH_LevDepCSize2]
            s=self.wordread(nlconst)
            self.levdep = np.fromstring(s,self.float).newbyteorder(self.byteorder)
            self.levdep.shape=(self.fixhd[FH_LevDepCSize2],self.fixhd[FH_LevDepCSize1])

        # Row dependent constants
        if self.fixhd[FH_RowDepCStart] > 0:
            self.wordseek(self.fixhd[FH_RowDepCStart]-1)
            nlconst = self.fixhd[FH_RowDepCSize1]*self.fixhd[FH_RowDepCSize2]
            s=self.wordread(nlconst)
            self.rowdep = np.fromstring(s,self.float).newbyteorder(self.byteorder)
            self.rowdep.shape=(self.fixhd[FH_RowDepCSize2],self.fixhd[FH_RowDepCSize1])

        # Column dependent constants
        if self.fixhd[FH_ColDepCStart] > 0:
            self.wordseek(self.fixhd[FH_ColDepCStart]-1)
            nlconst = self.fixhd[FH_ColDepCSize1]*self.fixhd[FH_ColDepCSize2]
            s=self.wordread(nlconst)
            # Should reshape this to a 2D array
            self.coldep = np.fromstring(s,self.float).newbyteorder(self.byteorder)
            self.coldep.shape=(self.fixhd[FH_ColDepCSize2],self.fixhd[FH_ColDepCSize1])

    def getsectorsize(self):
        # Calculate sectorsize as gcd of the data offsets.
        # Assume it's not larger than default 2048
        sector = gcd(2048,self.fixhd[FH_DataStart] - 1)  # Actual start off by 1.
        for k in range(self.fixhd[FH_LookupSize2]):
            if self.ilookup[k,LBEGIN] == -99:
                break
            sector = gcd(sector,self.ilookup[k,LBNREC])
        return sector
        
    def createheader(self, intsize, realsize, levdepdim1=0, levdepdim2=0):
        # Create a standard header, given level dependent constants as arguments
        # Lengths of other sections may be version dependent?
        # Fixed length header of length 256
        self.fixhd = np.zeros(256,self.int)

        # Integer constants
        self.inthead = np.zeros(intsize,self.int)

        # Real constants
        self.realhead = np.zeros(realsize,self.float)

        # Level dependent constants
        if levdepdim1 > 0 and levdepdim2 > 0:
            self.levdep = np.zeros((levdepdim2,levdepdim1),self.float)

    def copyheader(self,f):
        """Copy all the header properties from specified open file"""

        for attr in ["wordsize", "byteorder", "int", "float", "fieldsfile",
                     "ppfile"]:
            setattr(self, attr, getattr(f,attr))

        # Array attributes need to be copied.
        for attr in ["fixhd", "realhead", "inthead"]:
            setattr(self, attr, getattr(f,attr).copy())

        # These ones need not exist
        for attr in ["levdep", "rowdep", "coldep"]:
            if hasattr(f, attr):
                setattr(self, attr, getattr(f,attr).copy())

        self.ilookup = f.ilookup.copy()
        self.rlookup = f.rlookup.copy()
        self.sectorsize = f.sectorsize

    def writeheader(self):
        # Header must already be defined by copying or creating
        # Fixed length header of length 256
        self.wordseek(0)
        self.arraywrite(self.fixhd)

        # Integer constants
        self.wordseek(self.fixhd[FH_IntCStart]-1)
        self.arraywrite(self.inthead)

        # Real constants
        self.wordseek(self.fixhd[FH_RealCStart]-1)
        self.arraywrite(self.realhead)

        # Level dependent constants
        if self.fixhd[FH_LevDepCStart] > 0:
            self.wordseek(self.fixhd[FH_LevDepCStart]-1)
            self.arraywrite(self.levdep)

        if self.fixhd[FH_RowDepCStart] > 0:
            self.wordseek(self.fixhd[FH_RowDepCStart]-1)
            self.arraywrite(self.rowdep)

        if self.fixhd[FH_ColDepCStart] > 0:
            self.wordseek(self.fixhd[FH_ColDepCStart]-1)
            self.arraywrite(self.coldep)


    def readlookup(self):
        lookdim1 = self.fixhd[FH_LookupSize1]
        lookdim2 = self.fixhd[FH_LookupSize2]
        # Read lookup
        self.wordseek(self.fixhd[FH_LookupStart]-1)
        s = self.wordread(lookdim1*lookdim2)

        # The lookup table has separate integer 1;45 and real 46-64 sections
        # Simplest to have duplicate integer and real versions and just index
        # into the appropriate parts
        # Is it possible to make just make them views of the same data?
        if lookdim1 != 64:
            raise umfile_error("Unexpected lookup table dimension %d %d" % (lookdim1, lookdim2))

        self.ilookup = np.reshape( np.fromstring(s, self.int).newbyteorder(self.byteorder), [lookdim2, lookdim1])
        self.rlookup = np.reshape( np.fromstring(s, self.float).newbyteorder(self.byteorder), [lookdim2, lookdim1])

    def print_fixhead(self):
        print("FIXED HEADER")
        for i in range(256):
            if i % 8 == 0:
                print("%5d:" % i,end="")
            if self.fixhd[i] == self.missval_i or self.fixhd[i] == self.missval_r:
                # -32768 is integer missing value, -1073741824 is an FP NaN
                print("       _",end="")
            else:
                print("%8d" % self.fixhd[i],end="")
            if i % 8 == 7:
                print()

    def getmask(self):
        # Is it already defined
        if self.mask != None:
            return
        # Get the land sea mask, code 30
        for k in range(self.fixhd[FH_LookupSize2]):
            if self.ilookup[k,LBEGIN] == -99:
                break
            if self.ilookup[k,ITEM_CODE] == 30:
                self.mask = self.readfld(k)
                self.nland = np.sum(self.mask!=0)
                return
        raise packerr("Land sea mask required for packing/unpacking")

    def readfld(self, k, raw=False):
        # Read field number k
        ilookup = self.ilookup[k]
        lbnrec = ilookup[LBNREC] # Size padded to record size 
        lblrec = ilookup[LBLREC] # Actual size w/o padding
        lbegin = ilookup[LBEGIN] # lbegin is offset from start

        self.wordseek(lbegin)
        s = self.wordread(lbnrec)

        if raw:
            return s

        packing = [0, ilookup[LBPACK]%10, ilookup[LBPACK]//10 % 10,
                   ilookup[LBPACK]//100 % 10, ilookup[LBPACK]//1000 % 10,
                   ilookup[LBPACK]//10000]
        if packing[1] == 0:
            # IEEE at same precision as the file
            nbytes = lblrec*self.wordsize
            if ilookup[DATA_TYPE]==1:
                dtype = self.float
            else:
                # Treat integer and logical together
                dtype = self.int
        elif packing[1] == 2:
            # 32 bit IEEE
            nbytes = lblrec*4
            if ilookup[DATA_TYPE]==1:
                dtype = np.float32
            else:
                dtype = np.int32
        else:
            raise packerr("Packing with N1 = %d not supported" % packing[1])

        if packing[2] == 0:
            # No compression
            npts = ilookup[LBNPT]
            nrows = ilookup[LBROW]
            # print "S", len(s), nbytes, len(np.fromstring(s[:nbytes], ftype))
            if nrows*npts == ilookup[LBLREC]:
                # As expected
                data = np.reshape( np.fromstring(s[:nbytes], dtype).newbyteorder(self.byteorder), [nrows, npts])
            else:
                # There are some fields (accumulated runoff) that are packed to
                # land points, but don't have packing set correctly
                data = np.fromstring(s[:nbytes], dtype).newbyteorder(self.byteorder)
        elif packing[2] == 2:
            # Compressed using mask, nlon, nlat are the values from the land
            # sea mask
            if self.mask is None:
                self.getmask()
            nrows, npts = self.mask.shape
            tmp =  np.fromstring(s[:nbytes], dtype).newbyteorder(self.byteorder)
            # Set output array to missing, forcing the missing value to the 
            # correct type.
            data = np.zeros((nrows,npts), dtype) + np.array([self.missval_r], dtype)
            if packing[3]==1:
                # Use land mask (non-zero) values
                # Should check the sizes match that expected
                data.flat[self.mask.flat!=0] = tmp
            else:
                # Ocean values
                data.flat[self.mask.flat==0] = tmp
        else:
            raise packerr("Packing with N2 = %d not supported - field code %d" % (packing[2],ilookup[ITEM_CODE]))

        return data

    def writefld(self, data, k, raw=False, overwrite=False):
        # write the kth field
        if overwrite:
            filepos = self.ilookup[k,LBEGIN]
        else:
            if k==0:
                filepos =  self.fixhd[FH_DataStart] - 1
            else:
                filepos = self.ilookup[k-1,LBEGIN] + self.ilookup[k-1,LBNREC]
        self.wordseek(filepos)

        # If overwriting a field in an existing file don't change the header
        if not overwrite:
            self.ilookup[k,LBEGIN] = filepos

            # Need to set the output record size here
            if self.fixhd[FH_Dataset] == 3:
                # Fieldsfile, NADDR is relative to start of fixed length header
                # (i.e. relative to start of file)
                self.ilookup[k,NADDR] = filepos
            else:
                # Ancillary files behave like dumps?
                # NADDR is relative to start of data. Note that this uses LBLREC
                # so ignores the packing and the record padding. No relation to
                # the actual disk address in LBEGIN.
                if k == 0:
                    self.ilookup[k,NADDR] = 1
                else:
                    self.ilookup[k,NADDR] = self.ilookup[k-1,NADDR] + self.ilookup[k-1,LBLREC]


        if raw:
            # Data is just array of bytes
            self.fileobj.write(data)
            # Header is unchanged
            return
        else:
            # Need to pack properly
            packing = [0, self.ilookup[k,LBPACK]%10, self.ilookup[k,LBPACK]//10 % 10,
                       self.ilookup[k,LBPACK]//100 % 10, self.ilookup[k,LBPACK]//1000 % 10,
                       self.ilookup[k,LBPACK]//10000]
            # First consider packing to land or sea points
            if packing[2] == 0:
                # No packing
                packdata = data
            elif packing[2] == 2:
                if self.mask is None:
                    self.getmask()
                    # Need to restore the file pointer after the mask read
                    self.wordseek(filepos)
                if packing[3]==1:
                    # Use land mask (non-zero) values
                    # Should check the sizes match that expected
                    packdata = data[self.mask!=0]
                else:
                    # Ocean values
                    packdata = data[self.mask==0]
            else:
                raise packerr("Packing with N2 = %d not supported - field code %d" % (packing[2],self.ilookup[k,ITEM_CODE]))
            
            # Now write the data
            # arraywrite could actually return the sizes?
            lblrec = packdata.size

            self.arraywrite(packdata)

        if not overwrite:
            # Make the sector size a variable?
            self.ilookup[k,LBLREC] = lblrec
            if packing[1] == 2 and self.wordsize == 8:
                size = (lblrec+1)/2
            else:
                size = lblrec
            lbnrec = int(np.ceil(size/float(self.sectorsize))) * self.sectorsize
            self.ilookup[k,LBNREC] = lbnrec

    def writelookup(self):
        # lookdim1 = self.fixhd[FH_LookupSize1]
        # lookdim2 = self.fixhd[FH_LookupSize2]
        # For compatibility with the old version use the full size
        lookdim2, lookdim1 = self.ilookup.shape
        # Need to combine the ilookup and rlookup arrays to a single array
        # Convert the float part to an integer array
        lookup = np.fromstring(self.rlookup[:lookdim2,:].tobytes(),self.int).newbyteorder(self.byteorder)
        # Now copy the true integer part on top
        lookup.shape = (lookdim2, lookdim1)
        lookup[:,:45] = self.ilookup[:,:45]

        self.wordseek(self.fixhd[FH_LookupStart]-1)
        self.arraywrite(lookup)


        
class Axis:
    def __init__(self,name,values):
        # Should check name is lat, lon or lev and that the values are
        # appropriate for the axis type.
        self.name = name
        self.values = values

    def __eq__(self, a):
        if self.name == a.name and len(self.values) == len(a.values):
            return np.allclose(self.values, a.values)
        else:
            return False

def gcd(a,b):
    while a > 0:
        c = b%a
        b = a
        a = c
    return b

class UniqueList(list):
    # List without duplicates
    def append(self,a):
        if type(a) in [types.ListType,np.ndarray]:
            for x in a:
                if not x in self:
                    list.append(self,x)
        else:
            if not a in self:
                list.append(self,a)
        
class Grid:
    def __init__(self, lon, lat, lev):
        # Check that dimensions match
        # Really only for timeseries?
        if len(lat) == len(lon) == len(lev):
            self.lon = lon
            self.lat = lat
            self.lev = lev
        else:
            raise umfile_error("Inconsistent grids")

    def __eq__(self, g):
        if len(self.lon) == len(g.lon) and len(self.lat) == len(g.lat) and len(self.lev) == len(g.lev):
            return np.allclose(self.lon, g.lon) and np.allclose(self.lat, g.lat) \
               and np.allclose(self.lev, g.lev)
        else:
            return False

def isprog(ilookup):
    # Check whether a STASH code corresponds to a prognostic variable.
    # Section 33 is tracers, 34 is UKCA
    # Also check whether variable is instantaneous, LBTIM < 10
    # No time processing  ilookup[LBPROC] == 0
    # Not a time series LBCODE < 30000
    # Also 3100 - 3129 seem to be treated as prognostics
    varcheck = ilookup[ITEM_CODE]//1000 in [0,33,34] or \
               3100 <= ilookup[ITEM_CODE] <= 3129
    timecheck = ilookup[LBTIM] < 10 and ilookup[LBPROC] == 0 and ilookup[LBCODE] < 30000
    return varcheck and timecheck

def istracer(ilookup):
    return  ilookup[ITEM_CODE]//1000 == 33 and ilookup[LBTIM] < 10 and ilookup[LBPROC] == 0 and ilookup[LBCODE] < 30000
