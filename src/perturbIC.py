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
    ff_out.fields=[field for field in ff.fields if field.lbcode not in TIMESERIES_LBCODES]
    return ff_out


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


def create_perturbation(amplitude, random_generator, shape, nullify_poles = True):
    """
    Create a uniformly-distributed random perturbation of given amplitude and shape, using the given random_generator.
    If nullify_poles is set to True, nullifies the perturbation amplitude at the poles.

    Parameters
    ----------
    amplitude: float
        The amplitude of the random perturbation.
    random_generator: numpy.random.Generator
        The random generator used to generate the random perturbation.
    shape: tuple or list
        Shape of the generated perturbation.
    nullify_poles: bool, optional
        If set to True, nullifies the perturbation amplitude at the poles.

    Returns
    ----------
    pertubation: numpy.ndarray 
        The generated random perturbation.
    """
    perturbation = random_generator.uniform(low = -amplitude, high = amplitude, size = shape)
    # Set poles to zero (only necessary for ND grids, but doesn't hurt EG)
    if nullify_poles:
        perturbation[[0,-1],:] = 0    
    return perturbation


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
    Add a bi-dimensional random perturbation to the potential temperature field (STASH itemcode = 4) of a UM fields file.
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


