#!/usr/bin/env python
# Select a subset from a UM fieldsfile
# -p option will select only the prognostic fields required for an initial
# dump and will also check some header fields.

# Output word size and endianness match input.

# This doesn't change the "written" date in a dump header.
# Martin Dix martin.dix@csiro.au

from __future__ import print_function
import numpy as np
import mule
import argparse

prognostic_stash_codes = [0, 33, 34]
mask = 30

def parse_arguments():
    """
    Parse command-line arguments.

    Parameters
    ----------
    None
    """
    parser = argparse.ArgumentParser(description="Subset UM fields based on user-specified options.")

    # Positional arguments
    parser.add_argument('ifile', metavar="INPUT_PATH", help='Path to the input file.')
    # Optional arguments
    parser.add_argument('-o', '--output', dest = 'output_path', metavar="OUTPUT_PATH", help='Path to the output file. If omitted, the default output file is created by appending "_perturbed" to the input path.')
    parser.add_argument('-p', '--prognostic', dest='prognostic',  action='store_true',
                        help="Include only prognostic (section 0,33,34) variables")
    parser.add_argument('-v', '--incude', dest='include_list', type=str,
                        help="Comma-separated list of variables to INCLUDE (STASH indices)")
    parser.add_argument('-x', '--exclude', dest='exclude_list',type=str,
                        help="Comma-separated list of variables to EXCLUDE (STASH indices)")
    parser.add_argument('--validate', action='store_true',
                        help='Validate the output fields file using mule validation.')
    # Parse arguments
    args_parsed = parser.parse_args()

    # Convert from string list to a list of integers
    args_parsed.include_list = [int(v) for v in args_parsed.include_list.split(",")] if args_parsed.include_list else []
    args_parsed.exclude_list = [int(x) for x in args_parsed.exclude_list.split(",")] if args_parsed.exclude_list else []


    # Check if neither -v nor -x is provided
    if not args_parsed.include_list and not args_parsed.exclude_list:
        raise argparse.ArgumentError(None, "Error: Either -v or -x must be specified.")

    # Return arguments
    return args_parsed

def validate_arguments(include_list, exclude_list, prognostic):
    """
    Checks that the inclusion and exclusion lists are not provided simultaneously
    and ensures that the 'prognostic' flag is not used with explicit inclusion or exclusion lists.

    Parameters
    ----------
    include_list : list of int
            List of STASH codes for fields to include.
    exclude_list : list of int
            List of STASH codes for fields  to exclude.
    prognostic : bool
                 Whether to include only prognostic fields.
    Returns
    ----------
    None
    """
    if include_list and exclude_list:
        raise Exception("Error: -x and -v are mutually exclusive")

    if prognostic and (include_list or exclude_list):
        raise Exception("Error: -p incompatible with explicit list of variables")
        
def void_validation(*args, **kwargs):
    """
    Don't perform the mule validation, but print a message to inform that validation has been skipped.
    """
    print('Skipping mule validation. To enable the validation, run using the "--validate" option.')

def initialize_output_file(ff):
    """
    Initialize the output UM file by copying the input file and preparing it for output.

    Parameters
    ----------
    ff : mule.DumpFile
        The input UM file object to be copied.
    Returns
    -------
    mule.DumpFile
        A new copy of the input UM file with its fields initialized to an empty list.
    """
    file_copy = ff.copy()
    file_copy.fields = []
    return file_copy

def create_default_outname(f, suffix="_subset"):
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

def is_prognostic(field):
    """
    Check if a field is prognostic.

    A field is considered prognostic if its `lbuser4` attribute matches one of the values
    in the list [0, 33, 34], which correspond to the section numbers for prognostic variables.

    Parameters
    ----------
    field : object
        A field object with an `lbuser4` attribute that is checked to determine if it is prognostic.

    Returns
    -------
    bool
        True if the field is prognostic (i.e., its `lbuser4` is in [0, 33, 34]), False otherwise.
    """

    return field.lbuser4 in prognostic_stash_codes

def include_field(field, prognostic, include_list, exclude_list):
    """
    Determines if a field should be included based on the provided conditions.
    Parameters
    ----------
    field : object
        The field object to be checked.
    prognostic : bool
        A boolean flag indicating if only prognostic fields should be included.
    include_list : list of int
        A list of STASH item codes to include.
    exclude_list : list of int
        A list of STASH item codes to exclude.

    Returns
    -------
    bool
        True if the field should be included, False otherwise.
    """
    # Check if the field is part of the exclusion list
    if field.stash in exclude_list:
        return False

    # Check if the field is part of the inclusion list (if specified)
    if include_list and field.stash not in include_list:
        return False

    # If no inclusion or exclusion list, include the field based on its type
    if prognostic and field.is_prognostic():
        return True
        
    # Include all fields if no filters are applied
    if not prognostic and not include_list and not exclude_list:
        return True  

    return False


def check_fields_for_masking(input_file, include_list, prognostic):
    """
    Checks if packed fields in the input file require a land-sea mask and modifies
    the include list in place if necessary.

    Parameters
    ----------
    input_file : mule.DumpFile
    The input file containing the fields to be checked.
    include_list : list of int
        A list of STASH item codes to include in the output. If packed fields require a
        land-sea mask, STASH item code 30 will be added to this list.
    prognostic : bool
        A flag indicating whether only prognostic fields should be considered for inclusion.

    Returns
    -------
    None
    """

    needmask, masksaved = False, False
    for field in input_file.fields:
        if include_field(field, prognostic, include_list, []):
            # Check packing requirements and land-sea mask presence and adjust if necessary.
            needmask |= (field.lbpack == 2 and field.lblev in (1, 2))
            masksaved |= (field.lbuser4 == mask)

    if include_list and needmask and not masksaved:
        print("Adding land-sea mask to output fields because of packed data.")
        include_list.append(30)

def append_fields(input_file, outfile, prognostic, include_list, exclude_list):
    """
    Copies fields from the input UM file to the output UM file based on inclusion and exclusion criteria.

    Parameters
    ----------
    input_file : mule.DumpFile
        The input UM file containing the fields to be copied.

    outfile : mule.DumpFile
        The output UM file to which the selected fields will be copied.

    prognostic : bool
        If True, only prognostic fields will be copied.

    include_list : list of int
        A list of STASH item codes to include. Only these fields will be copied to the output file.

    exclude_list : list of int
    A list of STASH item codes to include. Only these fields will be copied to the output file.

    exclude_list : list of int
        A list of STASH item codes to exclude. Fields with these item codes will not be copied to the output file.

    Returns
    -------
    None
        This function modifies the output_file in place and does not return any value.
    """
    #Loop through all the fields
    for field in input_file.fields:
        # Check if the field should be included or excluded.
        if include_field(field, prognostic, include_list, exclude_list):
            outfile.fields.append(field.copy())


def main():
    """
    Select or remove a subset of fields from a UM fields file.
    """
    # Parse the inputs and validate that they do not xlist or vlist are given.
    args = parse_arguments()
    validate_arguments(args.include_list, args.exclude_list, args.prognostic)

    # Skip the mule validation if the "--validate" option is provided.
    if args.validate:
        mule.DumpFile.validate = void_validation

    ff = mule.DumpFile.from_file(args.ifile)

    # Create the output UM file that will be saved.
    outfile = initialize_output_file(ff)

    # Create the output filename.
    output_filename = create_default_outname(args.ifile) if args.output_path is None else args.output_path

    # Find the fields, if any, that needs a land-sea mask.
    check_fields_for_masking(ff, args.include_list, args.prognostic)

    # Loop over all the fields.
    append_fields(ff, outfile, args.prognostic, args.include_list, args.exclude_list)

    outfile.to_file(output_filename)

if __name__== "__main__":
    main()
