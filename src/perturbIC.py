#!/usr/bin/env python

# Apply a perturbation to initial condition.
# Martin Dix martin.dix@csiro.au

import os
import argparse
from numpy.random import PCG64, Generator
import mule


def parse_args():
    """
   Parse the command line arguments.

    Parameters
    ----------
    None

    Returns
    ----------
    args_parsed : argparse.Namespace
        Argparse namespace containing the parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Perturb UM initial dump")
    parser.add_argument('-a', dest='amplitude', type=float, default=0.01,
                        help = 'Amplitude of the perturbation.')
    parser.add_argument('-s','--seed', dest='seed', type=int
        help = 'The seed value used to generate the random perturbation (must be a non-negative integer).')
    parser.add_argument('ifile', metavar="INPUT_PATH", help='Path to the input file.')
    parser.add_argument('--validate', action='store_true',
        help='Validate the output fields file using mule validation.)
    args_parsed = parser.parse_args()
    return args_parsed

def create_random_generator(value=None):
    """
    Create the random generator object using the provided value as a seed.

    Parameters
    ----------
    value : int
           The seed value used to create the random generator.

    Returns
    ----------
    numpy.random.Generator
        The numpy random generator object.
    """
    if value < 0:
        raise ValueError('Seed value must be non-negative.')
    return Generator(PCG64(value))    

def remove_timeseries(ff):
    """
    Remove any timeseries from a fields file.

    Parameters
    ----------
    ff : mule.dump.DumpFile
           The mule DumpFile to remove the timeseries from.

    Returns
    ----------
    ff_out : mule.dump.DumpFile 
        The mule DumpFile with no timeseries.
    """
    ff_out = ff.copy()
    num_ts = 0

    # Perform timeseries removal without rewriting file
    for fld in ff.fields:

        # Check for the grid code that denotes a timeseries
        if fld.lbcode in (31320, 31323):
            num_ts += 1
        else:
            ff_out.fields.append(fld)

    # Either return the fields with the timeseries removed
    if num_ts > 0:
        print(f'{num_ts} timeseries fields skipped')
        return ff_out
    # Or return all the feilds
    else:
        print('No timeseries fields found')
        return ff


def create_default_outname(filename, suffix="_perturbed"):
    """
    Create a default output filename by appending a suffix to the input filename. 
    If an output filename already exists, a number will be appended to produce a unique output filename. 

    Parameters
    ----------
    filename: str
         The input filename.
    suffix: str, optional
        The suffix to append to the filename.

    Returns
    ----------
    output_filename: str 
        The default output filename.
    """
    output_filename = f"{filename}{suffix}"
    num=""
    if os.path.exists(output_filename):
        num = 1
        while os.path.exists(f"{output_filename}{num}"):
            num += 1
    return f"{output_filename}{num}"


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

def is_end_of_file(field_data, data_limit):
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

    if field_data  == data_limit:
        return True
    else:
        return False

def do_perturb(field, surface_stash_code):
    """
    This function checks to make sure that the correct field is used (surface temperature)

    Parameters
    ----------
    
    field : mule fields Object
           Holds the entire umfile including metadata and datai

    surface_stash_code : int

    Returns
    ----------
    boolean - True if this is the correct data to be perturbed. False for all other item code
    """
    if field.lbuser4 == surface_stash_code:
        return True
    else:
        return False

class SetAdditionOperator(mule.DataOperator):
    """
    This class creates a mule operator that adds a random perturbation to a field

    Parameters
    __________

    perturb : np.array
             An array of the random values to be added to the field
    
    Returns
    __________

    field - The field with the perturbation added to it
    """
    def __init__(self, perturb):
        self.perturbation = perturb

    def new_field(self, source_field):
        """Creates the new field object"""
        return source_field.copy()

    def transform(self, source_field, new_field):
        """Performs the data manipulation"""
        data = source_field.get_data()

        # Multiply by 0 to keep the array shape
        return data + self.perturbation


def void_validation(*args, **kwargs):
    """
    Don't perform the validation, but print a message to inform that validation has been skipped.
    """
    print('Skipping mule validation. To enable the validation, run using the "--validate" option.')


def set_validation(validate):
    """
    This function sets the validation. It is for testing purposes to cirucmvent the river fields flipped grid in ESM15

    Parameters
    __________

    validate : boolean
              This variable is mandatory from the user and is True for testing purposes

    """
    if validate:
        mule.DumpFile.validate = void
    else:
        print("May encounter an error  if using ESM15 with the river field grids set validate to True to circumvent")

def main():
    """
    This function executes all the steps to add the perturbation.The results if saving the perturbation 
    in the restart file. 
    """

    # Define all the variables  
    STASH_THETA = 4

    # Parse the command line arguments
    args = parse_args()

    # Create the output filename
    output_file = create_default_outname(args.ifile)
     
    # Create the random generator.
    random_generator = create_random_generator(args.seed)

    # Skips the validation entirely for use on ESM15 due to river fields error
    # Creates the mule field object 
    set_validation(args.validate)
    ff_raw = mule.DumpFile.from_file(args.ifile)
    
    # Set up the definitions of the grid the Dumpfile object doesn't have a way to do this?
    nlon = 192
    nlat = 145

    # Remove the time series from the data to ensure mule will work
    ff = remove_timeseries(ff_raw)

    # Creates a random perturbation array 
    perturbation = create_perturbation(args, random_obj, nlon, nlat)

    # Sets up the mule opertator to add the perturbation to the data
    addperturbation = SetAdditionOperator(perturbation)

    # Loop through the fields to find the surface termperature
    for ifield, field in enumerate(ff.fields):

        # Checks the loop has reached the end of the data
        if is_end_of_file(field.lbuser4, data_limit):
            break
        # Find the surface temperature field and add the perturbation
        if field.lbuser4 == surface_temp_stash:
            ff.fields[ifield] = addperturbation(field)

    ff.to_file(output_file)

if __name__== "__main__":

    main()


