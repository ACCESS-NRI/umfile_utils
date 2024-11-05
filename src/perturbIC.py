# Apply a perturbation to initial condition.
# Note that this works in place.
# For ENDGAME perturb thetavd as well if it's present

# Martin Dix martin.dix@csiro.au

import argparse
import umfile
from um_fileheaders import *
from numpy.random import PCG64, Generator
import mule


def parse_args():
    """
    This function parses the arguments from the command line.

    Parameters
    ----------
    None

    Returns
    ----------
    args_parsed : ArguementParser object
        Contains the arguments from the command line that can be access with the dest
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

def get_rid_of_timeseries(ff):
    """
    This function checks to see if there are times series, then gets rid of them so that 
    mule can run.

    Parameters
    ----------
    args : ArgumentParser object
           The argument parser object with amplitude, seed from commandline

    Returns
    ----------
    ff/ff_out : Returns a mule fields object with no timeseries
    """
    ff_out = ff.copy()
    num_ts = 0

    #Perform timeseries removal without rewriting file
    for fld in ff.fields:

        # Check for the grid code that denotes a timeseries
        if fld.lbcode in (31320, 31323):
            num_ts += 1

        else:
            ff_out.fields.append(fld)

    #Either return the fields with the timeseries removed
    if num_ts > 0:
        print(f'{num_ts} timeseries fields skipped')
        return ff_out
    
    #Or return all the feilds
    else:
        print('No timeseries fields found')
        return ff
    


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
    This function allows for editing out-of-place. 

    Parameters
    ----------
    args: ArgumentParser object
         The argument parser object with output file name.

    Returns
    ----------
    Boolean - returns False for editing in place and True if a new 
        outfile has been created

    """

    if args.output == None:
        return False

    else:
        subprocess.run(['cp', args.ifile, args.output])
        return True

def create_perturbation(args, rs, nlon, nlat):
    """
    This function create a random pertrbation of amplitude args.amplitude.

    Parameters
    ----------
    args : Dictionary
        The argumenst from the commandline (amplitude, seed).

    rs : Random Object 
        The random object that has a seed (if defined).
           
    nlon: Int 
        This is the longitude limit for the grid.

    nlat: Int
        This is the latitude limit for the grid.
       
    Returns
    ----------
    pertubation -  Array - Returns a perturbation where the poles are set to 0

    """
    perturbation = args.amplitude * (2.*rs.random(nlon*nlat).reshape((nlat,nlon)) - 1.)

    # Set poles to zero (only necessary for ND grids, but doesn't hurt EG)
    perturbation[0] = 0
    perturbation[-1] = 0
    return perturbation

def is_end_of_file(field,data_limit):
    """
    This function checks to see if there is data associated with the metadata.

    Parameters
    ----------
    f : umFile Object 
        This is the fields file that holds the restart data. 
    
    k : int
        This integer is indexing the metadata in the fields file.

    data_limit : int
        This int is a placeholder indicating the end of the data.
    Returns
    ----------
    boolean - True if the end of the data is reached and False everwhere else.

    """

    if field.lbuser4 == data_limit:
        return True
    else:
        return False

def do_perturb(field, surface_temp_code):
    """
    This function checks to make sure that the correct field is used (surface temperature).

    Parameters
    ----------
    
    field : mule fields Object
           Holds the entire umfile including metadata and data.

    surface_stash_code : int
        This integer represents the item code for surface temperature or theta.
    

    Returns
    ----------
    boolean - True if this is the correct data to be perturbed. False for all other item code

    """
         
    if field.lbuser4 == surface_temp_code:
        return True

    else:
        return False

def main():
    """
    This function checks to make sure that the correct field is used (surface temperature).

    Returns
    ----------
    UM fields file - The modifed fields file that has the perturbed field.

    """

    # Define all the variables  
    data_limit = -99
    surface_temp_code = 24

    # Obtain the arguements from the commandline
    # Then set the seed if there is one
    args = parse_args()
    random_obj = set_seed(args)

    #Check if there is timeseries then remove them to avoid mule errors.
    ff_raw = mule.FieldsFile.from_file(args.ifile)

    # The definitions of the grid
    # Set up theta perturbation.
    nlon = ff.integer_constants.num_cols
    nlat = ff.integer_constants.num_rows

    # Remove the time series from the data to ensure mule will work
    ff = get_rid_of_timeseries(ff_raw)

    # Same at each level so as not to upset vertical stability.
    perturbation = create_perturbation(args, random_obj, nlon, nlat)

    for ifield, field in enumerate(ff.fields):

        if is_end_of_file(field, data_limit):
            break
        # Find the surface temperature field and add the perturbation.
        if do_perturb(field, surface_temp_code):

            data = field.get_data()
            ff.fields[ifield] = data+perturbation

    ff.to_file(args.ifile)


if __name__== "__main__":

    main()
