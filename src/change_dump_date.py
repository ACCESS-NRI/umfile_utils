import os
import mule
import argparse

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
    parser = argparse.ArgumentParser(description="Modify UM dump file timestamps.")
    parser.add_argument('ifile', metavar="INPUT_PATH", help='Path to the input file.')
    parser.add_argument('-y', '--year', type=int, help='New year value.', required=True)
    parser.add_argument('-m', '--month', type=int, help='New month value (1-12).', required=True)
    parser.add_argument('-d', '--day', type=int, help='New day value (1-31).', required=True)
    parser.add_argument('-o', '--output', dest='output_path', metavar="OUTPUT_PATH",
                        help='Path to the output file. If omitted, the default output file is created by appending "_perturbed" to the input path.')
    parser.add_argument('--validate', action='store_true',
        help='Validate the output fields file using mule validation.')
    return parser.parse_args()

def change_fileheader_date(ff, new_year, new_month, new_day):
    """
    Update the initial and valid date in the fixed-length header of a UM fields file.

    Parameters
    ----------
    ff : mule.FieldsFile
        The UM fields file object whose header will be updated.
    new_year : int
        The new year to set in the file header.
    new_month : int
        The new month to set in the file header.
    new_day : int
        The new day to set in the file header.

    Returns
    -------
    None
    """
    ff.fixed_length_header.t1_year = new_year
    ff.fixed_length_header.t1_month = new_month
    ff.fixed_length_header.t1_day = new_day

    ff.fixed_length_header.v1_year = new_year
    ff.fixed_length_header.v1_month = new_month
    ff.fixed_length_header.v1_day = new_day

def change_fieldheader_date(ff, new_year, new_month, new_day):
    """
    Update the header date of each field in the  UM fields file.

    Parameters
    ----------
    ff : mule.FieldsFile
        The UM fields file object whose header will be updated.
    new_year : int
        The new year to set in the file header.
    new_month : int
        The new month to set in the file header.
    new_day : int
        The new day to set in the file header.

    Returns
    -------
    None
    """

    for field in ff.fields:
        field.lbyr = new_year
        field.lbmon = new_month
        field.lbdat = new_day

def create_default_outname(filename, suffix="_date_changed"):
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

def void_validation(*args, **kwargs):
    """
    Don't perform the validation, but print a message to inform that validation has been skipped.
    """
    print('Skipping mule validation. To enable the validation, run using the "--validate" option.')

def main():
    """
    Main function to load, modify, and save the UM dump file.
    """
    args = parse_args()

    ff = mule.FieldsFile.from_file(args.ifile)

    output_file = create_default_outname(args.ifile) if args.output_path is None else args.output_path
    print(ff.fixed_length_header.t1_year)
    # Skip mule validation if the "--validate" option is provided

    if not args.validate:
        ff.validate = void_validation

    change_fileheader_date(ff, args.year, args.month, args.day)
    change_fieldheader_date(ff, args.year, args.month, args.day)

    print(ff.fixed_length_header.t1_year)
    # Create the output filename

    ff.to_file(output_file)


if __name__== "__main__":

    main()
