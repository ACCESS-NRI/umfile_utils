#!/usr/bin/env python
# Select a subset from a UM fieldsfile
# -p option will select only the prognostic fields required for an initial
# dump and will also check some header fields.

# Output word size and endianness match input.

# This doesn't change the "written" date in a dump header.
# Martin Dix martin.dix@csiro.au

import mule
import os
import argparse
from itertools import chain
PROGNOSTIC_STASH_CODES = tuple(chain(range(1,999+1), range(33001,34999+1)))

def parse_args():
    """
    Parse command-line arguments.

    Parameters
    ----------
    None

    Returns
    ----------
    args_parsed : argsparse.Namespace
        Argparse namespace containing the parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Subset UM fields based on user-specified options.")

    # Positional arguments
    parser.add_argument(dest='ifile', metavar="INPUT_PATH", help='Path to the input file.')
    # Optional arguments
    parser.add_argument('-o', '--output', dest = 'output_path', metavar="OUTPUT_PATH", help='Path to the output file. If omitted, the default output file is created by appending "_subset" to the input path.')
    meg = parser.add_mutually_exclusive_group(required=True)
    meg.add_argument('-p', '--prognostic', dest='prognostic',  action='store_true',
                        help="Only include prognostic variables (sections 0, 33 and 34). Cannot be used together with --include or --exclude.")
    meg.add_argument('--include', dest='include_list', type=str, metavar="STASH_CODE",
                        help="Comma-separated list of STASH codes to include in the output file. Any STASH code present in the input file, but not contained in this STASH code list, will not be present in the output file. Cannot be used together with --prognostic or --exclude.")
    meg.add_argument('--exclude', dest='exclude_list', type=str, metavar="STASH_CODE"
                        help="Comma-separated list of STASH codes to exclude from the output file. All STASH codes present in the input file, but not contained in this STASH code list, will be present in the output file. Cannot be used together with --prognostic or --include.")
    parser.add_argument('--validate', action='store_true',
                        help='Validate the output fields file using mule validation.')
    # Parse arguments
    args_parsed = parser.parse_args()

    # Convert from string to int
    args_parsed.include_list = [int(v) for v in args_parsed.include_list.split(",")] if args_parsed.include_list else []
    args_parsed.exclude_list = [int(x) for x in args_parsed.exclude_list.split(",")] if args_parsed.exclude_list else []


    # Check if neither -v nor -x is provided
    if not args_parsed.include_list and not args_parsed.exclude_list and not args_parsed.prognostic:
        raise argparse.ArgumentError(None, "Error: Either -v or -x or -p must be specified.")

    # Return arguments
    return args_parsed
    


def void_validation(*args, **kwargs):
    """
    Don't perform the validation, but print a message to inform that validation has been skipped.
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

def create_default_outname(filename, suffix="_subset"):
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


def filter_fields(input_file, prognostic, include_list, exclude_list):
    """
    Creates a list of fields from the input file that should be included based on user conditions.

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
    list
        A list of fields that need to be in the file
    """
    filtered_fields = []
    for field in input_file.fields:

        # Check if the field is part of the exclusion list
        if field.stash in exclude_list:
            continue
            
        # Check if the field is part of the inclusion list (if specified)
        if include_list  and field.stash in include_list:
            filtered_fields.append(field)

        # If no inclusion or exclusion list, include the field based on its type
        elif prognostic and field.lbuser4 in PROG_STASH_CODES:
            filtered_fields.append(field)

        elif not prognostic and not include_list and not exclude_list:
            filtered_fields.append(field)

    return filtered_fields


def check_packed_fields(filtered_fields):
    """
    Checks if packed fields in the input file require a land-sea mask and modifies
    the include list if necessary.

    Parameters
    ----------
    filtered_fields : list of int
        A list of STASH item codes to include in the output. If packed fields require a
        land-sea mask, STASH item code 30 will be added to this list.

    Returns
    -------
    None
        This function modifies the `include_list` in place by appending the land-sea mask
        (STASH code 30) if required.
    """
    print('calling check_packed')
    needmask, masksaved = False, False
    print(filtered_fields)

    for field in filtered_fields:
        print(field.stash, field.lbpack, field.lblev)

        needmask |= (field.lbpack == 2 and field.lblev in (1,2))
        masksaved |= (field.stash == MASK_CODE)

    if needmask and not masksaved:
        print('adding mask')
        filtered_fields.append(30)

    else:
        print('not adding mask')
        print(masksaved)
        print(needmask)

    return filtered_fields

def append_fields(outfile, filtered_fields):
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
        A list of STASH item codes to exclude. Fields with these item codes will not be copied to the output file.

    Returns
    -------
    None
        This function modifies the output_file in place and does not return any value.
    """
    for field in filtered_fields:
        # Ad to the outfile fields 
        outfile.fields.append(field.copy())


def main():

    # Parse the inputs and validate that they do not xlist or vlist are given.
    args = parse_arguments()

    # Skip the mule validation if the "--validate" option is provided.
    if args.validate:
        mule.DumpFile.validate = void_validation

    ff = mule.load_umfile(args.ifile)


    # Create the output filename.
    output_filename = create_default_outname(args.ifile) if args.output_path is None else args.output_path

    #Create list of fields that meet all the user defined conditions
    filtered_fields = filter_fields(ff, args.prognostic, args.include_list, args.exclude_list)

    # Find the fields, if any, that needs a land-sea mask.
    filtered_fields = check_packed_fields(filtered_fields)

    # Loop over all the fields.
    append_fields(outfile, filtered_fields)

    outfile.to_file(output_filename)
    
if __name__== "__main__":
    main()
