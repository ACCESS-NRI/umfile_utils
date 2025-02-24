import os
import mule
import argparse

def year_value(value):
    """
    Ensure the year is a non-negative integer between 0 and 9999.
    """
    if not value:
        return None
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid year: {value}. Must be an integer between 0 and 9999.")
    if ivalue < 0 or ivalue > 9999:
        raise argparse.ArgumentTypeError(f"Invalid year: {value}. Must be between 0 and 9999.")
    return ivalue

def month_value(value):
    """
    Ensure the month is between 1 and 12 (inclusive).
    """
    if not value:
        return None
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid month: {value}. Must be an integer between 1 and 12.")
    if ivalue < 1:
        raise argparse.ArgumentTypeError(f"Invalid month: {value}. Must be a positive integer.")
    if ivalue > 12:
        raise argparse.ArgumentTypeError(f"Invalid month: {value}. Must be between 1 and 12.")
    return ivalue

def day_value(value):
    """
    Ensure the day is between 1 and 31 (inclusive).
    """
    if not value:
        return None
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid day: {value}. Must be an integer between 1 and 31.")
    if ivalue < 1:
        raise argparse.ArgumentTypeError(f"Invalid day: {value}. Must be a positive integer.")
    if ivalue > 31:
        raise argparse.ArgumentTypeError(f"Invalid day: {value}. Must be between 1 and 31.")
    return ivalue

def date_value(value):
    """
    Ensure the date is in YYYYMMDD format and extract year, month, and day.
    """
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date: {value}. Must be in YYYYMMDD format.")
    if len(value) != 8:
        raise argparse.ArgumentTypeError(f"Invalid date: {value}. Must be exactly 8 digits (YYYYMMDD).")
    return ivalue

def parse_args():
    """
    Parse the command line arguments.

    Returns
    ----------
    args_parsed : argparse.Namespace
        Argparse namespace containing the parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Modify UM dump file timestamps.")
    parser.add_argument('ifile', metavar="INPUT_PATH", help='Path to the input file.')
    parser.add_argument('-o', '--output', dest='output_path', metavar="OUTPUT_PATH",
                        help='Path to the output file. If omitted, the default output file is created by appending "_perturbed" to the input path.')
    parser.add_argument('--validate', action='store_true',
        help='Validate the output fields file using mule validation.')

    parser.add_argument('--date', type=date_value, help='New date in YYYYMMDD format.')
    parser.add_argument('-y', '--year', type=year_value, help='New year value (0-9999).')
    parser.add_argument('-m', '--month', type=month_value, help='New month value (1-12).')
    parser.add_argument('-d', '--day', type=day_value, help='New day value (1-31).')

    args_parsed = parser.parse_args()

    # Ensure at least one of -y, -m, or -d is specified if --date is not used
    if args_parsed.date and (args_parsed.year or args_parsed.month or args_parsed.day):
        parser.error("At least one of --date (YYYYMMDD) and -y -m -d commands are exclusive")

    return args_parsed

def parse_date(args):
    """
    Parses the --date YYYYMMDD into -y -m -d format

    Parameters
    __________

    args :  argparse.Namespace
        Argparse namespace containing the parsed command line arguments
    """
    date = str(args.date)

    #Parse the specific portions
    args.year = int(date[:4])
    args.month = int(date[4:6])
    args.day = int(date[6:])

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

    if new_year != None:
        ff.fixed_length_header.t1_year = new_year
        ff.fixed_length_header.v1_year = new_year

    ff.fixed_length_header.t1_month = new_month
    ff.fixed_length_header.t1_day = new_day
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
        if new_year != None:
            field.lbyr = new_year

        field.lbmon = new_month
        field.lbdat = new_day

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

    if new_year is not None:
        ff.fixed_length_header.t1_year = new_year
        ff.fixed_length_header.v1_year = new_year
    if new_month is not None:
        ff.fixed_length_header.t1_month = new_month
        ff.fixed_length_header.v1_month = new_month
    if new_day is not None:
        ff.fixed_length_header.t1_day = new_day
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
        if new_year is not None:
            field.lbyr = new_year
        if new_month is not None:
            field.lbmon = new_month
        if new_day is not None:
            field.lbdat = new_day

def create_default_outname(filename, suffix="_newdate"):
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
    print(args.year)
    if args.date:
        parse_date(args)
    print(args.year)
    ff = mule.UMFile.from_file(args.ifile)

    output_file = create_default_outname(args.ifile) if args.output_path is None else args.output_path
    # Skip mule validation if the "--validate" option is provided

    if not args.validate:
        ff.validate = void_validation

    change_fileheader_date(ff, args.year, args.month, args.day)
    change_fieldheader_date(ff, args.year, args.month, args.day)

    # Create the output filename

    ff.to_file(output_file)


if __name__== "__main__":

    main()

