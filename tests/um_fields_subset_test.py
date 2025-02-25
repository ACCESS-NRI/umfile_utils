import pytest
import argparse
import warnings
from copy import deepcopy
from unittest.mock import MagicMock, patch

import numpy as np
from hypothesis import strategies as st
from hypothesis.extra import numpy as stnp
from umfile_utils.um_fields_subset import (
    PROGNOSTIC_STASH_CODES,
    convert_to_list,
    create_default_outname,
    warn_if_stash_not_present,
    filter_fieldsfile,
    parse_args,
    void_validation,
    include_fields,
    exclude_fields,
    main,
)

@pytest.fixture
def create_mock_umfile():
    def _mock_umfile():
        """Factory function to create a mule UMfile mock object and initialize it with empty fields."""
        return MagicMock(fields=[])

    return _mock_umfile

@pytest.fixture
def create_mock_field():
    """Factory function to create a mule field mock object."""

    def _create_field(**kwargs):
        return MagicMock(
            **kwargs,
            copy= lambda: _create_field(**kwargs),
        )
    return _create_field

@pytest.mark.parametrize(
    "input, expected_output, should_raise",
    [
        ("1,2,3", [1, 2, 3], False),
        ("10,  20,30  ", [10, 20, 30], False),
        ("10.1,10,32", None, True),  # Contains a non-integer
        ("10 20 30", None, True),  # Missing commas
        ("-1,-2,-3", None, True),  # Contains negative numbers
        ("0,1,2", None, True),  # Contains zero
        ("a,1,2", None, True),  # Contains a non-number
    ],
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


def test_warn_if_stash_not_present_raised(create_mock_field):
    """
    Test the warn_if_stash_not_present function when a warning is to be raised.
    """
    mock_fields = [create_mock_field(lbuser4=1), create_mock_field(lbuser4=2), create_mock_field(lbuser4=3)]
    stash_list = [1, 1000, 2]
    with pytest.warns(UserWarning, match=r"The following STASH codes are not found in the input file: \{1000\}"):
        warn_if_stash_not_present(mock_fields, stash_list)


def test_warn_if_stash_not_present_not_raised(create_mock_field):
    """
    Test the warn_if_stash_not_present function when a warning is NOT to be raised.
    """
    mock_fields = [create_mock_field(lbuser4=1), create_mock_field(lbuser4=2), create_mock_field(lbuser4=3)]
    specified_stash_codes = {1, 3, 2}
    with warnings.catch_warnings():
        warnings.filterwarnings("error", message="The following STASH codes are not found in the input file: .*")
        warn_if_stash_not_present(mock_fields, specified_stash_codes)


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
    include_list = [1, 2]
    with (
        patch("umfile_utils.um_fields_subset.include_fields") as mock_include,
        patch("umfile_utils.um_fields_subset.warn_if_stash_not_present") as mock_warn_isnp,
    ):
        mock_include.return_value = "expected_fields"
        mock_warn_isnp.side_effect = None
        result = filter_fieldsfile(mock_file, prognostic=False, include_list=include_list, exclude_list=None)
        mock_include.assert_called_once_with(mock_file.fields, include_list)
        assert result.fields == "expected_fields"


def test_filter_fieldsfile_prognostic(create_mock_field, create_mock_umfile):
    """
    Test filter_fieldsfile when the '--prognostic' options is provided.
    """
    # Create a mock file with mock fields.
    mock_file = create_mock_umfile()
    with (
        patch("umfile_utils.um_fields_subset.include_fields") as mock_include,
        patch("umfile_utils.um_fields_subset.warn_if_stash_not_present") as mock_warn_isnp,
    ):
        mock_include.return_value = "expected_fields"
        mock_warn_isnp.side_effect = None
        result = filter_fieldsfile(mock_file, prognostic=True, include_list=None, exclude_list=None)
        mock_include.assert_called_once_with(mock_file.fields, PROGNOSTIC_STASH_CODES)
        assert result.fields == "expected_fields"


def test_filter_fieldsfile_exclude(create_mock_field, create_mock_umfile):
    """
    Test filter_fieldsfile when the '--exclude' options is provided.
    """
    # Create a mock file with mock fields.
    mock_file = create_mock_umfile()
    exclude_list = [1, 2]
    with (
        patch("umfile_utils.um_fields_subset.exclude_fields") as mock_exclude,
        patch("umfile_utils.um_fields_subset.warn_if_stash_not_present") as mock_warn_isnp,
    ):
        mock_exclude.return_value = "expected_fields"
        mock_warn_isnp.side_effect = None
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

def test_include_fields(create_mock_field):
    """Test the include_fields function."""
    with patch("umfile_utils.um_fields_subset.warn_if_stash_not_present") as mock_warn_isnp:
        mock_warn_isnp.side_effect = None
        fields = [create_mock_field(lbuser4=1), create_mock_field(lbuser4=2), create_mock_field(lbuser4=3), create_mock_field(lbuser4=1)]
        stash_list = {1, 3, 1000}
        expected_result = [create_mock_field(lbuser4=1), create_mock_field(lbuser4=3), create_mock_field(lbuser4=1)]
        result = include_fields(fields, stash_list)
        # Ensure the warning function was called
        mock_warn_isnp.assert_called_once_with(fields, stash_list)
        # Ensure the output is correct
        assert len(result) == len(expected_result)
        for r, er in zip(result, expected_result):
            assert r is not er # Ensure the function returns a new list
            assert r.lbuser4 == er.lbuser4 # Ensure the stash codes are correct

def test_exclude_fields(create_mock_field):
    """Test the exclude_fields function."""
    with patch("umfile_utils.um_fields_subset.warn_if_stash_not_present") as mock_warn_isnp:
        mock_warn_isnp.side_effect = None
        fields = [create_mock_field(lbuser4=1), create_mock_field(lbuser4=2), create_mock_field(lbuser4=3), create_mock_field(lbuser4=1)]
        stash_list = {1, 3, 1000}
        expected_result = [create_mock_field(lbuser4=2)]
        result = exclude_fields(fields, stash_list)
        # Ensure the warning function was called
        mock_warn_isnp.assert_called_once_with(fields, stash_list)
        # Ensure the output is correct
        assert len(result) == len(expected_result)
        for r, er in zip(result, expected_result):
            assert r is not er # Ensure the function returns a new list
            assert r.lbuser4 == er.lbuser4 # Ensure the stash codes are correct


@patch("umfile_utils.um_fields_subset.parse_args")
@patch("umfile_utils.um_fields_subset.create_default_outname")
@patch("mule.DumpFile.from_file")
@patch("umfile_utils.um_fields_subset.filter_fieldsfile")
@patch("umfile_utils.um_fields_subset.void_validation")
def test_main(
    mock_void_validation,
    mock_filter_fieldsfile,
    mock_mule_dumpfile_from_file,
    mock_create_default_outname,
    mock_parse_args,
    create_mock_umfile,
    create_mock_field,
):
    """Test the main function."""
    # Mock the return value of parse_args
    mock_args = MagicMock(
        ifile="test_input_file",
        include_list={1, 2, 3},
        exclude_list=None,
        prognostic=None,
        validate=True,
        output_path=None,
    )
    mock_parse_args.return_value = mock_args

    # Mock the return value of mule.DumpFile.from_file
    mock_ff = create_mock_umfile()
    mock_mule_dumpfile_from_file.return_value = mock_ff

    # Mock the return value of filter_fieldsfile
    mock_filtered_ff = create_mock_umfile()
    mock_filter_fieldsfile.return_value = mock_filtered_ff
    
    main()

    # Assertions
    mock_parse_args.assert_called_once()
    mock_create_default_outname.assert_called_once_with(mock_args.ifile)
    mock_mule_dumpfile_from_file.assert_called_once_with(mock_args.ifile)
    mock_filter_fieldsfile.assert_called_once_with(mock_ff, mock_args.prognostic, mock_args.include_list, mock_args.exclude_list)
    mock_filtered_ff.to_file.assert_called_once_with(mock_create_default_outname.return_value)
    mock_void_validation.assert_not_called()

    #  ============= #
    # Case with validation disabled and output path provided
    #  ============= #

    # Reset mock calls
    mock_create_default_outname.reset_mock()
    
    # Set the output path and validate to False
    mock_args.output_path = "test_output_file"
    mock_args.validate = False
    
    main()

    # Assertions
    assert mock_filtered_ff.validate == mock_void_validation
    mock_create_default_outname.assert_not_called()

