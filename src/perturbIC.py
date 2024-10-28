#!/usr/bin/env python

# Apply a perturbation to initial condition.
# Note that this works in place.
# For ENDGAME perturb thetavd as well if it's present

# Martin Dix martin.dix@csiro.au

#!/usr/bin/env python

# Apply a perturbation to initial condition.
# Note that this works in place.
# For ENDGAME perturb thetavd as well if it's present

# Martin Dix martin.dix@csiro.au

import argparse
import src.umfile
from .um_fileheaders import *
from numpy.random import PCG64, Generator

def parse_args():
    """
    This function parses the arguments from the command line

    Parameters
    ----------
    None

    Returns
    ----------
    args_parsed : ArguementParser object
        Contains the arguments from the command line that can be access with their dest
    """
    parser = argparse.ArgumentParser(description="Perturb UM initial dump")
    parser.add_argument('-a', dest='amplitude', type=float, default=0.01,
                        help = 'Amplitude of perturbation')
    parser.add_argument('-s', dest='seed', type=int, default=None,
        help = 'Random number seed (must be non-negative integer)')
    parser.add_argument('-o', dest='output', type=str, default=None,
        help = 'Output file (if none given modified in place)')
    parser.add_argument('ifile', help='Input file (modified in place)')
    args_parsed = parser.parse_args()
    return args_parsed

def set_seed(args):
    """
    This function sets the seed, if any, for the random generator

    Parameters
    ----------
    args : ArgumentParser object
           The argument parser object with amplitude, seed from commandline

    Returns
    ----------
    Random Object
    or 
    Exception
    """
    if args.seed == None:
        return Generator(PCG64())

    elif args.seed >=0:
        return Generator(PCG64(args.seed))
    else:
        raise Exception('Seed must be positive')

def is_inplace(args):
    """
    This provides an outline for editing if a new file should be 
    created

    Parameters
    ----------
    args: ArgumentParser object
         The argument parser object with output file name

    Returns
    ----------
    Boolean - returns False for editing in place and True if a new 
        outfile has been created

    subprocess.run(['cp', original_file, new_file])
    """

    if args.output == None:
        return False

    else:
        subprocess.run(['cp', args.ifile, args.output])
        return True

def create_perturbation(args, rs, nlon, nlat):
    """
    This function create a random pertrbation of amplitude args.amplitude 

    Parameters
    ----------
    args : Dictionary - The argumenst from the commandline (amplitude, seed)
    rs : Random Object - The random object that has a seed (if defined)
           Argument 2 description
    nlon: Int - This is the lon
           Argument 3 description

    Returns
    ----------
    pertubation -  Array - Returns a perturbation where the poles are set to 0

    """
    perturbation = args.amplitude * (2.*rs.random(nlon*nlat).reshape((nlat,nlon)) - 1.)

    # Set poles to zero (only necessary for ND grids, but doesn't hurt EG)
    perturbation[0] = 0
    perturbation[-1] = 0
    return perturbation

def is_end_of_file(f, k, data_limit):
    """
    This function checks to see if there is data associated with the metadata

    Parameters
    ----------
    f : umFile Object 
        This is the fields file that holds the restart data 
    
    k : int
        This integer is indexing the metadata in the fields file

    data_limit : int
        This int is a placeholder indicating the end of the data
    Returns
    ----------
    boolean - True if the end of the data is reached and False everwhere else

    """
    ilookup = f.ilookup[k]
    if ilookup[LBEGIN] == data_limit:
        return True
    else:
        return False

def if_perturb(ilookup,k,f,perturb,surface_temp_item_code,endgame):
    """
    This function checks to make sure that the correct field is used (surface temperature)

    Parameters
    ----------
    ilookup : 
    k : int
            This integer is indexing the metadata in the fields file

    f : umFile Object
           Holds the entire umfile including metadata and data
    
    perturb : Array 
        Holds the random perturbation and has shape nlon x nlat  
    
    surface_temp_item_code : int
        This integer represents the item code for surface temperature or theata
    
    endgame : int
        This integer represents the FIXME

    Returns
    ----------
    boolean - True if this is the correct data to be perturbed. False for all other item codes
    Array - If True the perturbation is added to the data array

    """
    if ilookup[ITEM_CODE] in (surface_temp_item_code,endgame):

        a = f.readfld(k)
        a += perturb
        
        return True, a

    else:

        return False, None

def main():
    """
    This function executes all the steps to add the perturbation.The results if saving the perturbation 
    in the restart file. 
    """

    #Define all the variables  
    data_limit = -99
    surface_temp_item_code = 4
    endgame = 388

    #Obtain the arguements from the commandline
    #Then set the seed if there is one
    args = parse_args()
    random_obj = set_seed(args)

    f = umfile.UMFile(args.ifile, 'r+')

    # The definitions of the grid
    nlon = f.inthead[IC_XLen]
    nlat = f.inthead[IC_YLen]

    # Same at each level so as not to upset vertical stability
    perturb = create_perturbation(args, random_obj, nlon, nlat)

    for k in range(f.fixhd[FH_LookupSize2]):

        #Check to make sure not at the edge of the data
        if is_end_of_file(f, k, data_limit):
            break

        ilookup = f.ilookup[k]

        #Find the correct field and add perturbation
        is_perturb, a = if_perturb(ilookup,k,f,perturb,surface_temp_item_code,endgame)
        if is_perturb:

            f.writefld(a,k)

    f.close()


if __name__== "__main__":

    main()
