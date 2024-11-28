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
import getopt, sys
import umfile
from um_fileheaders import *
import mule
import argparse

def validate_arguments(vlist, xlist, prognostic):

    if vlist and xlist:
        raise Exception("Error: -x and -v are mutually exclusive")

    if prognostic and (vlist or xlist):
        raise Exception("Error: -p incompatible with explicit list of variables")

def parse_arguments():

    parser = argparse.ArgumentParser(description="Subset UM fields based on user-specified options.")

    # Define arguments
    parser.add_argument('-i', '--input', required=True, help="Input file")
    parser.add_argument('-o', '--output', required=True, help="Output file")
    parser.add_argument('-n', '--nfields', type=int, default=9999999999,
                        help="Maximum number of fields to process (default: 9999999999)")
    parser.add_argument('-p', '--prognostic', action='store_true',
                        help="Include only prognostic (section 0,33,34) variables")
    parser.add_argument('-s', '--section', action='store_true',
                        help="Use section numbers instead of variable indices for -v and -x")
    parser.add_argument('-v', '--vlist', type=str,
                        help="Comma-separated list of variables to INCLUDE (STASH indices)")
    parser.add_argument('-x', '--xlist', type=str,
                        help="Comma-separated list of variables to EXCLUDE (STASH indices)")

    # Parse arguments
    args = parser.parse_args()

    # Process lists from strings to integers
    vlist = [int(v) for v in args.vlist.split(",")] if args.vlist else []
    xlist = [int(x) for x in args.xlist.split(",")] if args.xlist else []

    # Check if neither -v nor -x is provided
    if not vlist and not xlist:
        raise argparse.ArgumentError(None, "Error: Either -v or -x must be specified.")

    # Return arguments
    return args.input, args.output, args.nfields, args.prognostic, args.section, vlist, xlist

def match(code,vlist,section):
    if section:
        return code//1000 in vlist
    else:
        return code in vlist

def initialize_output_file(ifile, ofile):
    """Initialize the output UM file."""
    f = mule.DumpFile.from_file(ifile)
    g = f.copy()
    g.fields = []
    return f, g

def decode_packing(lbpack):
    """Decode the packing scheme of a field."""
    return [0, lbpack % 10, lbpack // 10 % 10, lbpack // 100 % 10, lbpack // 1000 % 10, lbpack // 10000]

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
            packing = decode_packing(field.lbpack)
            needmask |= (packing[2] == 2 and packing[3] in (1, 2))
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
            if field.lbuser7 in (0, 33, 34):  # Prognostic sections
                nprog += 1
            if field.lbuser4 >= 34001 and field.lbuser4 <= 34100:  # Example tracer range
                ntracer += 1
    return kout, nprog, ntracer

def finalize_header(output_file, kout, nprog, ntracer):
    """Finalize the output file header."""


    # Create a copy of the current integer constants
    integer_constants = output_file.integer_constants.copy()

    # Update the number of fields
    integer_constants[22] = kout  # Update the number of fields

    # Update the number of prognostic fields
    if integer_constants[23] != nprog:
        print(f"Resetting number of prognostic fields from {integer_constants[23]} to {nprog}")
        integer_constants[23] = nprog

    # Update the number of tracer fields
    if integer_constants[40] != ntracer:
        print(f"Resetting number of tracer fields from {integer_constants[40]} to {ntracer}")
        integer_constants[40] = ntracer

    # Ensure tracer levels match physical levels
    if ntracer > 0 and integer_constants[41] != integer_constants[28]:
        print(f"Resetting number of tracer levels from {integer_constants[41]} to {integer_constants[28]}")
        integer_constants[41] = integer_constants[28]

    # Assign the modified integer constants back to the output file
    output_file.integer_constants = integer_constants

def main():
    ifile, ofile, nfields, prognostic, section, vlist, xlist = parse_arguments()
    validate_arguments(vlist, xlist, prognostic)

    #Create the output UM file that will be saved to
    f, g = initialize_output_file(ifile, ofile)

    #Find the fields, if any, that needs a land-sea mask
    check_packed_fields(f, vlist, prognostic, section)

    # Loop over all the fields, counting the number of prognostic fields
    kout, nprog, ntracer = copy_fields(f, g, nfields, prognostic, vlist, xlist, section)

    #Create the header and make sure it is large enough
    finalize_header(g, kout, nprog, ntracer)
    g.close()

if __name__== "__main__":
    main()

