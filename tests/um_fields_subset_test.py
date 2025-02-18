
import pytest
from copy import deepcopy
from unittest.mock import patch, MagicMock
from hypothesis import HealthCheck, given, settings, strategies as st
from hypothesis.extra import numpy as stnp
from um_fields_subset_mule import (
    parse_args, 
    field_not_present_warning, 
    include_fields, exclude_fields, 
    filter_fieldsfile, 
    create_default_outname, 
    void_validation, 
    convert_to_list, 
    PROGNOSTIC_STASH_CODES,
)
import numpy as np

@pytest.mark.parametrize(
    "input, expected_output, should_raise",
    [
        ("1,2,3", [1, 2, 3], False),
        ("10,  20,30  ", [10, 20, 30], False),
        ("10.1,10,32", None, True),  # Contains a non-integer
        ("10 20 30", None, True),    # Missing commas
        ("-1,-2,-3", None, True),    # Contains negative numbers
        ("0,1,2", None, True),        # Contains zero
        ("a,1,2", None, True)        # Contains a non-number
    ]
)
def test_convert_to_list(input, expected_output, should_raise):
    """Test convert_to_list with valid and invalid inputs."""
    if should_raise:
        with pytest.raises(argparse.ArgumentTypeError, match="All values must be positive integers."):
            convert_to_list(input)
    else:
        assert convert_to_list(input) == expected_output

def test_parse_args_prognostic():
    """
    Test parse_args with the '--prognostic' argument passed
    """
    test_args = ["--prognostic"]
    with patch("sys.argv", ["script_name", "input_file"] + test_args):
        args = parse_args()
        assert args.ifile == "input_file"
        assert args.prognostic is True

@pytest.mark.parametrize(
    # description of the arguments
    "mutually_exclusive_args", 
    [
        ["--prognostic", "--include", "1,2,3"], 
        ["--prognostic", "--exclude", "1,2,3"], 
        ["--include", "1,2,3", "--exclude", "1,2,3"], 
    ],
)
def test_parse_args_mutually_exclusive(mutually_exclusive_args):
    """
    Test parse_args with mutually exclusive arguments.
    """
    with patch("sys.argv", ["script_name", "input_file"] + mutually_exclusive_args), pytest.raises(SystemExit):
        parse_args()

def test_parse_args_include():
    """
    Test parse_args with the '--include' argument passed.
    """
    test_args = ["--include", "1,2,3"]
    with patch("sys.argv", ["script_name", "input_file"] + test_args):
        args = parse_args()
        assert args.include_list == [1, 2, 3]

# Define strategy for creating fake STASH codes and fields to test the warning function.
stash_code_strategy = st.lists(st.integers(min_value=1, max_value=35000), min_size=1, max_size=10)
fields_strategy = st.lists(stnp.arrays(dtype=np.int32, shape=(10,)), min_size=1, max_size=5)

@pytest.fixture
def create_mock_field():
    """Factory function to create a mule field mock object."""

    def _create_field(lbuser4 = None):
        return MagicMock(
            lbuser4=lbuser4,
        )
    return _create_field

def test_field_not_present_warning_raised(create_mock_field):
    """
    Test the field_not_present_warning function when a warning is to be raised.
    """
    mock_fields = [create_mock_field(lbuser4=1), create_mock_field(lbuser4=2), create_mock_field(lbuser4=3)]
    stash_list = [1,1000,2]
    with pytest.warns(UserWarning, match=r"The following STASH codes are not found in the input file: \{1000\}"):
        field_not_present_warning(mock_fields, stash_list)

def test_field_not_present_warning_not_raised(create_mock_field):
    """
    Test the field_not_present_warning function when a warning is NOT to be raised.
    """
    mock_fields = [create_mock_field(lbuser4=1), create_mock_field(lbuser4=2), create_mock_field(lbuser4=3)]
    specified_stash_codes = {1,3,2}
    with warnings.catch_warnings():
        warnings.filterwarnings("error", message="The following STASH codes are not found in the input file: .*")
        field_not_present_warning(mock_fields, specified_stash_codes)



# Define a simple mock field class to replace MagicMock.
class MockField:
    def __init__(self, lbuser4):
        self.lbuser4 = lbuser4

    def copy(self):  # Ensure copying works properly.
        return MockField(self.lbuser4)


def test_filter_fieldsfile_include(create_mock_field, create_mock_umfile):
    """
    Test filter_fieldsfile when the '--include' options is provided.
    """
    # Create a mock file with mock fields.
    mock_file = create_mock_umfile()
    include_list = [1,2]
    with patch("um_fields_subset.include_fields") as mock_include:
        warnings.filterwarnings("ignore", message="The following STASH codes are not found in the input file: .*") # Avoid raising warnings if STASH codes are not found in the input file
        mock_include.return_value = "expected_fields"
        result = filter_fieldsfile(mock_file, prognostic=False, include_list=include_list, exclude_list=None)
        mock_include.assert_called_once_with(mock_file.fields, include_list)
        assert result.fields == "expected_fields"
        

def test_filter_fieldsfile_prognostic(create_mock_field, create_mock_umfile):
    """
    Test filter_fieldsfile when the '--prognostic' options is provided.
    """
    # Create a mock file with mock fields.
    mock_file = create_mock_umfile()
    with patch("um_fields_subset.include_fields") as mock_include, warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="The following STASH codes are not found in the input file: .*") # Avoid raising warnings if STASH codes are not found in the input file
        mock_include.return_value = "expected_fields"
        result = filter_fieldsfile(mock_file, prognostic=True, include_list=None, exclude_list=None)
        mock_include.assert_called_once_with(mock_file.fields, PROGNOSTIC_STASH_CODES)
        assert result.fields == "expected_fields"

def test_filter_fieldsfile_exclude(create_mock_field, create_mock_umfile):
    """
    Test filter_fieldsfile when the '--exclude' options is provided.
    """
    # Create a mock file with mock fields.
    mock_file = create_mock_umfile()
    exclude_list = [1,2]
    with patch("um_fields_subset.exclude_fields") as mock_exclude:
        warnings.filterwarnings("ignore", message="The following STASH codes are not found in the input file: .*") # Avoid raising warnings if STASH codes are not found in the input file
        mock_exclude.return_value = "expected_fields"
        result = filter_fieldsfile(mock_file, prognostic=False, include_list=None, exclude_list=exclude_list)
        mock_exclude.assert_called_once_with(mock_file.fields, exclude_list)
        assert result.fields == "expected_fields"

@pytest.mark.parametrize(
    # description of the arguments
    "existing_files, filename, expected_output",
    [
        # Case 1: Filename with suffix doesn't exist, return filename with suffix
        ([], "testfilename", "testfilename_subset"),
        # Case 2: Filename with suffix exists, returns filename with suffix appending 1
        (["testfilename_subset"], "testfilename", "testfilename_subset1"),
        # Case 3: Filename with suffix and a few numbered versions exist, returns
        # filename with suffix and the first numbered version that doesn't exist
        (
            ["testfilename_subset", "testfilename_subset1", "testfilename_subset2"],
            "testfilename",
            "testfilename_subset3",
        ),
    ],
    ids=[
        "file_do_not_exist",
        "file_exists",
        "multiple_files_exist",
    ],
)
@patch("os.path.exists")
def test_create_default_outname_suffix_not_passed(mock_exists, existing_files, filename, expected_output):
    """
    Test the function that creates the default output file name, without passing a suffix.
    3 cases tested with pytest.mark.parametrize.
    """
    # Mock os.path.exists to simulate the presence of specific files
    mock_exists.side_effect = lambda f: f in existing_files
    result = create_default_outname(filename)
    assert result == expected_output


@patch("os.path.exists")
def test_create_default_outname_suffix_passed(mock_exists):
    """
    Test the function that creates the default output file name, passing a custom suffix.
    """
    # Mock os.path.exists to simulate the presence of specific files
    mock_exists.return_value = False
    filename = "testfilename"
    suffix = "testsuffix"
    result = create_default_outname(filename, suffix)
    expected_output = "testfilenametestsuffix"
    assert result == expected_output

def test_void_validation(capfd):
    """Test that the void_validation function doesn't do anything but printing a message to stdout, for any input arguments."""
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
