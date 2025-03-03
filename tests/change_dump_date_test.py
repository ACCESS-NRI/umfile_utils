import pytest
import argparse
from unittest.mock import MagicMock, patch
from copy import deepcopy
from change_dump_date import (
    validate_year_value, 
    validate_month_value, 
    validate_day_value, 
    validate_date_value, 
    parse_args,
    change_header_date_file, 
    change_header_date_field, 
    create_default_outname,
    void_validation
)

# Combined Test for year_value, month_value, and day_value
@pytest.mark.parametrize(
    "func, input, expected_output, should_raise",
    [
        # Year tests
        (year_value, "0", 0, False),
        (year_value, "2024", 2024, False),
        (year_value, "9999", 9999, False),
        (year_value, "-1", None, True),  # Below range
        (year_value, "10000", None, True),  # Above range
        (year_value, "abcd", None, True),  # Non-numeric
        (year_value, "", None, True),  # Empty string should return None

        # Month tests
        (month_value, "1", 1, False),
        (month_value, "12", 12, False),
        (month_value, "6", 6, False),
        (month_value, "0", None, True),  # Below range
        (month_value, "13", None, True),  # Above range
        (month_value, "abc", None, True),  # Non-numeric
        (month_value, "", None, True),  # Empty string should return None

        # Day tests
        (day_value, "1", 1, False),
        (day_value, "31", 31, False),
        (day_value, "15", 15, False),
        (day_value, "0", None, True),  # Below range
        (day_value, "32", None, True),  # Above range
        (day_value, "xyz", None, True),  # Non-numeric
        (day_value, "", None, True),  # Empty string should return None

        #Date test
        (date_value, "20240226", 20240226, False),  # Valid date
        (date_value, "19991231", 19991231, False),  # Valid date
        (date_value, "00000000", 0, True),  # Edge case Invalid (month and day cannot be 0)
        (date_value, "20241301", None, True),  # Invalid month (13)
        (date_value, "202402", None, True),  # Too short
        (date_value, "abcdefgh", None, True),  # Non-numeric
        (date_value, "", None, True),  # Empty string is invalid
    ],)

def test_value_functions(func, input, expected_output, should_raise):
    """
    This function tests the 3 different type functions for the parser
    """

    if should_raise:
        with pytest.raises(argparse.ArgumentTypeError):
            func(input)
    else:
        assert func(input) == expected_output
def test_parse_args():
    """
    Test parse_args() function for different command-line arguments.
    """

    test_cases = [
        # Test case 1: Required input file argument
        (["input_file"], {"ifile": "input_file", "output_path": None, "validate": False, "date": None, "year": None, "month": None, "day": None}),

        # Test case 2: Input file with output file
        (["input_file", "-o", "output_file"], {"ifile": "input_file", "output_path": "output_file", "validate": False, "date": None, "year": None, "month": None, "day": None}),

        # Test case 3: Validation flag
        (["input_file", "--validate"], {"ifile": "input_file", "output_path": None, "validate": True, "date": None, "year": None, "month": None, "day": None}),

        # Test case 4: Setting a full date
        (["input_file", "--date", "20250226"], {"ifile": "input_file", "output_path": None, "validate": False, "date": 20250226, "year": None, "month": None, "day": None}),

        # Test case 5: Setting individual year, month, and day
        (["input_file", "-y", "2025", "-m", "2", "-d", "26"], {"ifile": "input_file", "output_path": None, "validate": False, "date": None, "year": 2025, "month": 2, "day": 26}),

        # Test case 6: Exclusive date and year should cause an error
        (["input_file", "--date", "20250226", "-y", "2025"], argparse.ArgumentError),
    ]

    for args, expected in test_cases:
        monkeypatch.setattr("sys.argv", ["script_name"] + args)

        if expected == argparse.ArgumentError:
            with pytest.raises(SystemExit):  # Argparse exits with error
                parse_args()
        else:
            parsed_args = parse_args()
            for key, value in expected.items():
                assert getattr(parsed_args, key) == value


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
