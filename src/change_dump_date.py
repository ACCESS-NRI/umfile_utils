#!/usr/bin/env python
# Change the initial and valid date of a UM dump file

# Change both the file header and the date header of each record.
# The latter may not be strictly necessary but it makes looking at file with
# xconv less confusing.

import getopt, sys
import argparse
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
    parser = argparse.ArgumentParser(description="Change the date on a UM dumpfile")
    # Positional arguments
    parser.add_argument('ifile', metavar="INPUT_PATH", help='Path to the input file.')
    # Optional arguments
    parser.add_argument('-y', dest='year', type=int, help = 'The year to be changed, must be positive')
    parser.add_argument('-m', dest='month', type=int,help = 'The month to be changed, must be between 1-12')
    parser.add_argument('-d', dest='day', type=int, help = 'The day to be changed must be between 1-31')
    parser.add_argument('--validate', action='store_true', help='Validate the output fields file using mule validation.')
    parser.add_argument('-o', '--output', dest = 'output_path', metavar="OUTPUT_PATH",
            help='Path to the output file. If omitted, the default output file is created by appending "_perturbed" to the input path.')
    args_parsed = parser.parse_args()
    return args_parsed

def alter_header_date(dump_file, year, month, day):
    # Update the initial and valid dates in the file headers
    dump_file.fixed_length_header.t1_year = year
    dump_file.fixed_length_header.t1_month = month
    dump_file.fixed_length_header.t1_day = day
      
def alter_lookup_headers_validity_time(field, year, month,day):

    field.lbyr = year
    field.lbmon = month
    field.lbdat = day

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

def main():

    args = parse_args()
    ff = mule.DumpFile.from_file(args.ifile)

    output_file = create_default_outname(args.ifile) if args.output_path is None else args.output_path

    alter_header_date(ff, args.year, args.month, args.day)

    for field in ff.fields:
        alter_lookup_headers_validity_time(field, args.year, args.month, args.day)

    dump_file.to_file(output_file)

    print(f"Updated file saved as {output_file_path}")
    f.close()
