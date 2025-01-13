import pytest
from copy import deepcopy
from unittest.mock import patch, MagicMock
from um_fields_subset_mule import (parse_arguments, validate_arguments, create_default_outname, filter_fields, check_packed_fields, append_fields, PROG_STASH_CODES, MASK_CODE,void_validation)
from hypothesis import given, strategies as st
import numpy as np

def test_parse_arguments_all_arguments():
    """Test with all arguments provided."""
    test_args = ["script_name", "test_input_file", "-o", "output_file", "-p", "-v", "1,2,3", "-x", "4,5"]
    with patch("sys.argv", test_args):
        args = parse_arguments()
        assert args.ifile == "test_input_file"
        assert args.output_path == "output_file"
        assert args.prognostic
        assert args.include_list == [1, 2, 3]
        assert args.exclude_list == [4, 5]

def test_parse_arguments_missing_include_or_exclude():
    """Test that an error is raised if neither -v nor -x is specified."""
    test_args = ["script_name", "test_input_file"]
    with patch("sys.argv", test_args):
        with pytest.raises(Exception):
            parse_arguments()

def test_validate_arguments_exclusion_inclusion_conflict():
    """Test that -v and -x cannot be used together."""
    with pytest.raises(Exception):
        validate_arguments([1, 2], [3], False)

def test_validate_arguments_prognostic_and_explicit_lists():
    """Test that -p cannot be used with explicit lists."""
    with pytest.raises(Exception):
        validate_arguments([1, 2], [], True)
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

# Define a strategy for generating the list of field codes
def list_strategy():
    return st.lists(st.integers(min_value=1, max_value=32), min_size=0, max_size=10)

# Define a strategy to create mock fields
def field_strategy():
    return st.builds( lambda stash, lbpack, lblev, lbuser4: MagicMock(stash=stash, lbpack=lbpack, lblev=lblev, lbuser4=lbuser4),
        stash=st.integers(min_value=1, max_value=36),      # stash values range
        lbpack=st.integers(min_value=1, max_value=4),
        lblev=st.integers(min_value=1, max_value=4),
        lbuser4=st.integers(min_value=0, max_value=36)     # lbuser4 values range (updated for prognostic codes)
    )

# Define a strategy for a list of fields
def field_list_strategy():
    return st.lists(field_strategy(), min_size=1, max_size=10)

@given(
    input_fields=field_list_strategy(),
    prognostic=st.booleans(),
    include_list=list_strategy(),
    exclude_list=list_strategy(),
)
def test_filter_fields(input_fields, prognostic, include_list, exclude_list):
    """
    Test the filter_fields function with various input combinations.
    """
    # Mock the input_file with fields
    input_file = MagicMock()
    input_file.fields = input_fields

    # Call the function being tested
    filtered_fields = filter_fields(input_file, prognostic, include_list, exclude_list)

    # Assert the logic
    for field in input_fields:
        if field.stash in exclude_list:
            assert field not in filtered_fields  # Excluded fields must NOT be in the result
        elif include_list and field.stash in include_list:
            assert field in filtered_fields  # Included fields must be in the result
        elif prognostic and field.lbuser4 in PROG_STASH_CODES:
            assert field in filtered_fields  # Prognostic fields must be in the result if prognostic=True
        elif not prognostic and not include_list and not exclude_list:
            assert field in filtered_fields  # All fields should be included if no filters are applied
        else:
            assert field not in filtered_fields  # Otherwise, the field should NOT be in the result

@given(field_list=field_list_strategy(),)

def test_check_packed_fields(field_list):
    """
    Test the check_packed_fields function with different scenarios.
    """
    MASK_CODE = 30  # Define the MASK_CODE constant for testing

    needmask = False
    masked = False

    for field in field_list:
         if field.lbpack == 2 and field.lblev in (1,2):
            needmask = True

        if field.stash == MASK_CODE:
            masked = True

    checked_field_list = check_packed_fields(field_list)

    if needmask and not masked:
        assert MASK_CODE in checked_field_list

    elif not needmask:
        assert field_list == checked_field_list

# Define a strategy to generate mock fields
def field_strategy():
    return st.builds(
        lambda: MagicMock(copy=MagicMock(return_value=MagicMock())),  # Each field has a copy method
    )

# Define a strategy to generate a list of mock fields
field_list_strategy = st.lists(field_strategy(), min_size=1, max_size=10)

@given(
    filtered_fields=field_list_strategy
)
def test_append_fields_hypothesis(filtered_fields):
    """
    Test the append_fields function with Hypothesis to ensure it works with various inputs.
    """
    # Mock the output file
    outfile = MagicMock()
    outfile.fields = []

    # Call the function
    append_fields(outfile, filtered_fields)

    # Assert the length of outfile.fields matches filtered_fields
    assert len(outfile.fields) == len(filtered_fields)

    # Assert that each field in filtered_fields has its `copy` method called and is in outfile.fields
    for original_field, appended_field in zip(filtered_fields, outfile.fields):
        # Check that `copy` was called on the field
        original_field.copy.assert_called_once()
        # Check that the copied field matches what's in outfile.fields
        assert appended_field == original_field.copy.return_value


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

                                                                                                  212,0-1       Bot


