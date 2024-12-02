#!/usr/bin/env python

# Apply a perturbation to initial condition.
# Martin Dix martin.dix@csiro.au

import os
import argparse
from numpy.random import PCG64, Generator
import mule
TIMESERIES_LBCODES = (31320, 31323)

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
    # Positional arguments
    parser.add_argument('ifile', metavar="INPUT_PATH", help='Path to the input file.')
    # Optional arguments
    parser.add_argument('-a', dest='amplitude', type=float, default=0.01,
                        help = 'Amplitude of the perturbation.')
    parser.add_argument('-s','--seed', dest='seed', type=int,
        help = 'The seed value used to generate the random perturbation (must be a non-negative integer).')
    parser.add_argument('--validate', action='store_true',
        help='Validate the output fields file using mule validation.')
    parser.add_argument('-o', '--output', dest = 'output_path', metavar="OUTPUT_PATH", help='Path to the output file. If omitted, the default output file is created by appending "_perturbed" to the input path.')
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
    if value is not None and value < 0:
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


def is_field_to_perturb(field, stash_to_perturb):
    """
    Check if the field STASH itemcode correspond to the one to perturb.
    
    Parameters
    ----------
    field : mule.Field
           Field to check.
    stash_to_perturb: int
        STASH itemcode to perturb.

    Returns
    ----------
    bool
        Returns True if the field STASH itemcode corresponds to the one to perturb.
    """
    return field.lbuser4 == stash_to_perturb

class AdditionOperator(mule.DataOperator):
    """
    Create a mule operator that adds an array to a field, provided that the two have the same shape.
    
    Attributes
    ----------
    array : numpy.ndarray
             The array to add to the field.
    """
    def __init__(self, array):
        self.array = array

    def new_field(self, source_field):
        """
        Create the new field object by copying the source field.
        """
        return source_field.copy()

    def transform(self, source_field, new_field):
        """
        Perform the field data manipulation: check that the array and source field data have the same shape and then add them together.
        """
        data = source_field.get_data()
        if (field_shape:=data.shape) != (array_shape:=self.array.shape):
            raise ValueError(f"Array and field could not be broadcast together with shapes {array_shape} and {field_shape}.")
        else:
            return data + self.array


def void_validation(*args, **kwargs):
    """
    Don't perform the validation, but print a message to inform that validation has been skipped.
    """
    print('Skipping mule validation. To enable the validation, run using the "--validate" option.')
    return


def main():
    """
    Add a bi-dimensional random perturbation to the potential temperature field 'Theta' (STASH itemcode = 4) of a UM fields file.
    """

    # Define all the variables  
    STASH_THETA = 4

    # Parse the command line arguments
    args = parse_args()

    # Create the output filename
    output_file = create_default_outname(args.ifile) if args.output_path is None else args.output_path

    # Create the random generator.
    random_generator = create_random_generator(args.seed)

    # Skip mule validation if the "--validate" option is provided
    if args.validate:
        mule.DumpFile.validate = void_validation
    ff_raw = mule.DumpFile.from_file(args.ifile)


    # Remove the time series from the data to ensure mule will work
    ff = remove_timeseries(ff_raw)

    # loop through the fields
    for ifield, field in enumerate(ff.fields):
        if is_field_to_perturb(field, STASH_THETA):
            try:
                ff.fields[ifield] = perturb_operator(field)
            except NameError: # perturb_operator is not defined
            # Only create the perturb_operator if it does not exist yet

                shape = field.get_data().shape
                perturbation = create_perturbation(args.amplitude, random_generator, shape)
                perturb_operator = AdditionOperator(perturbation)
                ff.fields[ifield] = perturb_operator(field)

    ff.to_file(output_file)

if __name__== "__main__":

    main()

