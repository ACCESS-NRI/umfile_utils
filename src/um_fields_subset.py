#!/usr/bin/env python
# Select a subset from a UM fieldsfile
# -p option will select only the prognostic fields required for an initial
# dump and will also check some header fields.

# Output word size and endianness match input.

# This doesn't change the "written" date in a dump header.
# Martin Dix martin.dix@csiro.au

# TODO: Specify ranges for variables.
# Give a warning if field to be excluded is not found?

from __future__ import print_function
import numpy as np
import mule
import argparse

def validate_arguments(vlist, xlist, prognostic):

    if vlist and xlist:
        raise Exception("Error: -x and -v are mutually exclusive")

    if prognostic and (vlist or xlist):
        raise Exception("Error: -p incompatible with explicit list of variables")

def void_validation(*args, **kwargs):
    """
    Don't perform the validation, but print a message to inform that validation has been skipped.
    """
    print('Skipping mule validation. To enable the validation, run using the "--validate" option.')
    return

def parse_arguments():

    parser = argparse.ArgumentParser(description="Subset UM fields based on user-specified options.")

    # Define arguments
    parser.add_argument('-i', '--input', dest='ifile',  required=True, help="Input file")
    parser.add_argument('-o', '--output', dest='ofile',  required=True, help="Output file")
    parser.add_argument('-n', '--nfields', dest='nfields',  type=int, default=9999999999,
                        help="Maximum number of fields to process (default: 9999999999)")
    parser.add_argument('-p', '--prognostic', dest='prognostic',  action='store_true',
                        help="Include only prognostic (section 0,33,34) variables")
    parser.add_argument('-s', '--section', dest='section', action='store_true',
                        help="Use section numbers instead of variable indices for -v and -x")
    parser.add_argument('-v', '--vlist', dest='vlist', type=str,
                        help="Comma-separated list of variables to INCLUDE (STASH indices)")
    parser.add_argument('-x', '--xlist', dest='xlist',type=str,
                        help="Comma-separated list of variables to EXCLUDE (STASH indices)")
    parser.add_argument('--validate', action='store_true',
                        help='Validate the output fields file using mule validation.')
    # Parse arguments
    args = parser.parse_args()

    #Convert from string to int
    args.vlist = [int(v) for v in args.vlist.split(",")] if args.vlist else []
    args.xlist = [int(x) for x in args.xlist.split(",")] if args.xlist else []


    # Check if neither -v nor -x is provided
    if not args.vlist and not args.xlist:
        raise argparse.ArgumentError(None, "Error: Either -v or -x must be specified.")

    # Return arguments
    return args

def match(code,vlist,section):
    if section:
        return code//1000 in vlist
    else:
        return code in vlist

def initialize_output_file(ff, ofile):
    """Initialize the output UM file."""
    g = ff.copy()
    g.fields = []
    return g

def include_field(field, prognostic, vlist, xlist, section):
    """Determine if a field should be included based on filters."""
    stash_code = field.stash  # STASH code of the field

    return (
        (prognostic and field.is_prognostic) or
        (vlist and match(stash_code, vlist, section)) or
        (xlist and not match(stash_code, xlist, section)) or
        (not prognostic and not vlist and not xlist)
    )

def check_packed_fields(input_file, vlist, prognostic, section):
    """Check if packed fields require the land-sea mask."""
    needmask, masksaved = False, False
    for field in input_file.fields:
        if include_field(field, prognostic, vlist, [], section):
            # No need to decode packing, using Mule attributes instead
            needmask |= (field.lbpack == 2 and field.lblev in (1, 2))  # Adjust conditions as necessary
            masksaved |= (field.lbuser4 == 30)  # 30 corresponds to land-sea mask
    if vlist and needmask and not masksaved:
        print("Adding land sea mask to output fields because of packed data")
        vlist.append(30)

def copy_fields(input_file, output_file, nfields, prognostic, vlist, xlist, section):
    """Copy selected fields from input to output UM file."""
    kout, nprog, ntracer = 0, 0, 0
    for field in input_file.fields:
        if kout >= nfields:
            break
        if include_field(field, prognostic, vlist, xlist, section):
            output_file.fields.append(field.copy())
            kout += 1

def main():

    # Parse the inputs and validate that they do not xlist or vlist are given
    args = parse_arguments()
    validate_arguments(args.vlist, args.xlist, args.prognostic)

    # Skip the mule validation if the "--validate" option is provided
    if args.validate:
        mule.DumpFile.validate = void_validation

    ff = mule.DumpFile.from_file(args.ifile)
    # Create the output UM file that will be saved to
    outfile = initialize_output_file(ff, args.ofile)

    # Find the fields, if any, that needs a land-sea mask
    check_packed_fields(ff, args.vlist, args.prognostic, args.section)

    # Loop over all the fields
    copy_fields(ff, outfile, args.nfields, args.prognostic, args.vlist, args.xlist, args.section)

    outfile.to_file(args.ofile)

if __name__== "__main__":
    main()

