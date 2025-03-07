import pytest
import argparse
from unittest.mock import MagicMock, patch
from copy import deepcopy
from change_dump_date import (    
    validate_year_value, 
    validate_month_value, 
    validate_day_value, 
    validate_date_value, 
    validate_required_args,
    validate_mutually_exclusive_args,
    parse_args,
    change_header_date_file, 
    change_header_date_all_fields, 
    create_default_outname,
    void_validation
)

@pytest.mark.parametrize(
    "input, expected_output, should_raise",
    [
        ("0", 0, False),
        ("2024", 2024, False),
        ("9999", 9999, False),
        ("472", 472, False),
        ("23", 23, False),
        ("5", 5, False),
        ("-1", None, True),  # Below range
        ("10000", None, True),  # Above range
        ("abcd", None, True),  # Non-numeric
        ("None", None, False),  # None input
    ],
)
def test_validate_year_value(input, expected_output, should_raise):
    """
    Tests validate_year_value function.
    """
    if should_raise:
        with pytest.raises(argparse.ArgumentTypeError):
            validate_year_value(input)
    else:
        assert validate_year_value(input) == expected_output


@pytest.mark.parametrize(
    "input, expected_output, should_raise",
    [
        ("1", 1, False),
        ("12", 12, False),
        ("6", 6, False),
        ("0", None, True),  # Below range
        ("13", None, True),  # Above range
        ("abc", None, True),  # Non-numeric
        ("None", None, False),  # None input
    ],
)
def test_validate_month_value(input, expected_output, should_raise):
    """
    Tests validate_month_value function.
    """
    if should_raise:
        with pytest.raises(argparse.ArgumentTypeError):
            validate_month_value(input)
    else:
        assert validate_month_value(input) == expected_output


@pytest.mark.parametrize(
    "input, expected_output, should_raise",
    [
        ("1", 1, False),
        ("31", 31, False),
        ("15", 15, False),
        ("0", None, True),  # Below range
        ("32", None, True),  # Above range
        ("xyz", None, True),  # Non-numeric
        ("None", None, False),  # None input
    ],
)
def test_validate_day_value(input, expected_output, should_raise):
    """
    Tests validate_day_value function.
    """
    if should_raise:
        with pytest.raises(argparse.ArgumentTypeError):
            validate_day_value(input)
    else:
        assert validate_day_value(input) == expected_output


@pytest.mark.parametrize(
    "input, expected_output, should_raise",
    [
        ("20240226", (2024, 2, 26), False),  # Valid date (adjusted output to tuple)
        ("19991231", (1999, 12, 31), False),  # Valid date
        ("00000000", None, True),  # Edge case Invalid (month and day cannot be 0)
        ("20241301", None, True),  # Invalid month (13)
        ("202402", None, True),  # Too short
        ("abcdefgh", None, True),  # Non-numeric
    ],
)
def test_validate_date_value(input, expected_output, should_raise):
    """
    Tests validate_date_value function.
    """
    if should_raise:
        with pytest.raises(argparse.ArgumentTypeError):
            validate_date_value(input)
    else:
        assert validate_date_value(input) == expected_output


@pytest.mark.parametrize(
    "year, month, day, date, should_raise",
    [
        (None, None, None, 20240226, False),  # Only date provided, valid
        (2024, None, None, None, False),  # Only year provided, valid
        (None, 2, None, None, False),  # Only month provided, valid
        (None, None, 26, None, False),  # Only day provided, valid
        (None, None, None, None, True),  # No arguments provided, should raise error
    ]
)
def test_validate_required_args(year, month, day, date, should_raise):
    if should_raise:
        with pytest.raises(ValueError, match="At least one argument among --date, --year, --month or --day must be provided."):
            validate_required_args(year, month, day, date)
    else:
        validate_required_args(year, month, day, date)  # Should not raise


@pytest.mark.parametrize(
    "year, month, day, date, should_raise",
    [
        (None, None, None, 20240226, False),  # Only date, valid
        (2024, None, None, None, False),  # Only one part of -y,-m,-d, valid
        (2024, 2, 26, None, False),  # Year, month, and day together, valid
        (None, None, None, None, False),  # No arguments, valid (handled by required check)
        (None, 2, None, 20240226, True),  # -y,-m, or -d and date given together, should raise error
        (2024, 2, 26, 20240226, True),  # Year, month, day, and date together, should raise error
    ]
)
def test_validate_mutually_exclusive_args(year, month, day, date, should_raise):
    if should_raise:
        with pytest.raises(ValueError, match="The arguments --date and any of --year, --month or --day are mutually exclusive."):
            validate_mutually_exclusive_args(year, month, day, date)
    else:
        validate_mutually_exclusive_args(year, month, day, date)  # Should not raise

@pytest.mark.parametrize(
    "user_args, expected_namespace, should_raise",
    [
        # Test case 1: Required input file argument (FAILS, so add a valid date)
        (["input_file", "--date", "20250226"],  # Added --date to meet validation requirement
         {"ifile": "input_file", "output_path": None, "validate": False, "date": "20250226", "year": 2025, "month": 2, "day": 26}, 
         False),

        # Test case 2: Input file with output file (FAILS, so add a valid date)
        (["input_file", "-o", "output_file", "--date", "20250226"],  # Added --date
         {"ifile": "input_file", "output_path": "output_file", "validate": False, "date": "20250226", "year": 2025, "month": 2, "day": 26}, 
         False),

        # Test case 3: Validation flag (FAILS, so add a valid date)
        (["input_file", "--validate", "--date", "20250226"],  # Added --date
         {"ifile": "input_file", "output_path": None, "validate": True, "date": "20250226", "year": 2025, "month": 2, "day": 26}, 
         False),

        # Test case 4: Setting a full date (Already valid)
        (["input_file", "--date", "20250226"], 
         {"ifile": "input_file", "output_path": None, "validate": False, "date": "20250226", "year": 2025, "month": 2, "day": 26}, 
         False),

        # Test case 5: Setting individual year, month, and day (Already valid)
        (["input_file", "-y", "2025", "-m", "2", "-d", "26"], 
         {"ifile": "input_file", "output_path": None, "validate": False, "date": None, "year": 2025, "month": 2, "day": 26}, 
         False),

        # Test case 6: Exclusive date and year should raise an error
        (["input_file", "--date", "20250226", "-y", "2025"], 
         None, 
         True),
    ]
)

def test_parse_args(monkeypatch, user_args, expected_namespace, should_raise):
    """
    Test parse_args() function for different command-line arguments.
    """
    monkeypatch.setattr("sys.argv", ["script_name"] + user_args)

    if should_raise:
        with pytest.raises(ValueError):  # Ensuring validation rules trigger exceptions
            parse_args()
    else:
        parsed_args = parse_args()
        expected = argparse.Namespace(**expected_namespace)
        assert vars(parsed_args) == vars(expected)

# Test the file header date change
class MockFieldsFile:
    def __init__(self):
        self.fixed_length_header = MockHeader()
class MockHeader:
    def __init__(self):
        self.t1_year = 2000
        self.v1_year = 2000
        self.t1_month = 1
        self.v1_month = 1
        self.t1_day = 1
        self.v1_day = 1

# Parameterized test for the function
@pytest.mark.parametrize(
    "new_year, new_month, new_day, expected_year, expected_month, expected_day",
    [
        (2025, 12, 31, 2025, 12, 31),  # Test case 1: Set full date
        (2025, None, None, 2025, 1, 1),  # Test case 2: Only year set
        (None, 5, None, 2000, 5, 1),  # Test case 3: Only month set
        (None, None, 15, 2000, 1, 15),  # Test case 4: Only day set
        (None, None, None, 2000, 1, 1),  # Test case 5: No changes
    ]
)
def test_change_header_date_file(new_year, new_month, new_day, expected_year, expected_month, expected_day):
    """
    This test check that the fileheader is being changed properly depending on which parameters it is given.
    """

    ff = MockFieldsFile()

    change_header_date_file(ff, new_year, new_month, new_day)

    assert ff.fixed_length_header.t1_year == expected_year
    assert ff.fixed_length_header.v1_year == expected_year
    assert ff.fixed_length_header.t1_month == expected_month
    assert ff.fixed_length_header.v1_month == expected_month
    assert ff.fixed_length_header.t1_day == expected_day
    assert ff.fixed_length_header.v1_day == expected_day

# Mocking the fields and the FieldsFile
class MockField:
    def __init__(self):
        self.lbyr = 2000  # Default year
        self.lbmon = 1    # Default month
        self.lbdat = 1    # Default day
class MockFieldsTestFile:
    def __init__(self, num_fields=1):
        self.fields = [MockField() for _ in range(num_fields)]  # Create a list of fields

# Parameterized test for the function
@pytest.mark.parametrize(
    "new_year, new_month, new_day, expected_year, expected_month, expected_day",
    [
        (2025, 12, 31, 2025, 12, 31),  # Test case 1: Set full date
        (2025, None, None, 2025, 1, 1),  # Test case 2: Only year set
        (None, 5, None, 2000, 5, 1),  # Test case 3: Only month set
        (None, None, 15, 2000, 1, 15),  # Test case 4: Only day set
        (None, None, None, 2000, 1, 1),  # Test case 5: No changes
    ]
)
def test_change_header_date_field(new_year, new_month, new_day, expected_year, expected_month, expected_day):
    """
    This test checks that the header date of each field is changed correctly based on the input parameters.
    """
    ff = MockFieldsTestFile(num_fields=3)  # Create a mock FieldsFile with 3 fields

    change_header_date_field(ff, new_year, new_month, new_day)

    # Check that each field's header date has been updated correctly
    for field in ff.fields:
        assert field.lbyr == expected_year
        assert field.lbmon == expected_month
        assert field.lbdat == expected_day
# Assuming your function is already defined as `create_default_outname`
@pytest.mark.parametrize(
    "existing_files, filename, suffix, expected_output",
    [
        # Case 1: Filename with suffix doesn't exist, return filename with suffix
        ([], "testfilename", "_newdate", "testfilename_newdate"),

        # Case 2: Filename with suffix exists, returns filename with suffix appending 1
        (["testfilename_newdate"], "testfilename", "_newdate", "testfilename_newdate1"),

        # Case 3: Filename with suffix and a few numbered versions exist, returns
        # filename with suffix and the first numbered version that doesn't exist
        (
            ["testfilename_newdate", "testfilename_newdate1", "testfilename_newdate2"],
            "testfilename",
            "_newdate",
            "testfilename_newdate3",
        ),

        # Case 4: Custom suffix passed and no file exists
        ([], "testfilename", "_custom", "testfilename_custom"),

        # Case 5: Custom suffix passed and a file with the custom suffix exists
        (["testfilename_custom"], "testfilename", "_custom", "testfilename_custom1"),
    ],
    ids=[
        "file_do_not_exist",
        "file_exists",
        "multiple_files_exist",
        "custom_suffix_no_existing_file",
        "custom_suffix_file_exists",
    ],
)
@patch("os.path.exists")
def test_create_default_outname(mock_exists, existing_files, filename, suffix, expected_output):
    """
    Test the function that creates the default output file name with and without a suffix.
    5 cases tested with pytest.mark.parametrize.
    """
    # Mock os.path.exists to simulate the presence of specific files
    mock_exists.side_effect = lambda f: f in existing_files

    result = create_default_outname(filename, suffix)
    assert result == expected_output

@patch("os.path.exists")
def test_create_default_outname_suffix_not_passed(mock_exists):
    """
    Test the function that creates the default output file name, without passing a suffix.
    """
    # Mock os.path.exists to simulate the presence of specific files
    mock_exists.side_effect = lambda f: f in ["testfilename_newdate"]

    result = create_default_outname("testfilename")
    assert result == "testfilename_newdate1"

@patch("os.path.exists")
def test_create_default_outname_suffix_passed(mock_exists):
    """
    Test the function that creates the default output file name, passing a custom suffix.
    """
    # Mock os.path.exists to simulate the presence of specific files
    mock_exists.return_value = False
    filename = "testfilename"
    suffix = "_testsuffix"
    result = create_default_outname(filename, suffix)
    expected_output = "testfilename_testsuffix"
    assert result == expected_output


def test_void_validation(capfd):
    """
    Test that the void_validation function doesn't do anything but printing a message to stdout, for any input arguments.
    """
    args = [1, "test", None, False]
    kwargs = {"a": 1, "b": "test", "c": None, "d": False}
    init_args = deepcopy(args)
    init_kwargs = deepcopy(kwargs)
    result = void_validation(*args, **kwargs)
    # Capture the output
    captured = capfd.readouterr()
    # Test output message to stdout
    assert (
        captured.out.strip() == 'Skipping mule validation. To enable the validation, run using the "--validate" option.'
    )
    # Test no output message to stderr
    assert captured.err == ""
    # Test no return value
    assert result is None
    # Test no side effects for input arguments
    assert args == init_args
    assert kwargs == init_kwargs
