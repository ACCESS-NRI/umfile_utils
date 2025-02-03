import pytest
import warnings
from copy import deepcopy
from unittest.mock import patch, MagicMock
from um_fields_subset_mule import (parse_args, create_default_outname, field_not_present_warning,PROG_STASH_CODES, MASK_CODE, void_validation)
from hypothesis import given, strategies as st
from hypothesis.extra import numpy as stnp
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

def test_field_not_present_warning(stash_list, fields):
    # Flatten each numpy array in the list of fields (not the list itself)
    mock_fields = [MagicMock(lbuser4=item) for array in fields for item in array.flatten()]
    
    # Set up mocking of the warnings.warn function
    with patch("warnings.warn") as mock_warn:
        # We use a set for stash_list to ensure unique codes for testing
        field_not_present_warning(mock_fields, set(stash_list))
        
        # Calculate missing codes
        missing_codes = set(stash_list) - {item for array in fields for item in array.flatten()}
        
        # Check if the warning is triggered correctly
        if missing_codes:
            # Assert the warning was called with the expected message
            expected_warning = f"The following STASH codes are not found in the input file: {missing_codes}"
            
            # Sort both expected and actual warning messages to avoid order issues
            actual_warning = str(mock_warn.call_args[0][0])
            assert set(expected_warning.split(": ")[1].split(", ")) == set(actual_warning.split(": ")[1].split(", "))
        else:
            # If no codes are missing, check that warnings.warn was not called
            mock_warn.assert_not_called()

def test_include_fields():
    mock_field1 = MagicMock(lbuser4=1)
    mock_field2 = MagicMock(lbuser4=2)
    mock_field3 = MagicMock(lbuser4=3)
    fields = [mock_field1, mock_field2, mock_field3]
    stash_list = [1, 3]
    
    result = include_fields(fields, stash_list)
    assert len(result) == 2
    assert mock_field1.copy() in result
    assert mock_field3.copy() in result
    assert mock_field2.copy() not in result

def test_exclude_fields():
    mock_field1 = MagicMock(lbuser4=1)
    mock_field2 = MagicMock(lbuser4=2)
    mock_field3 = MagicMock(lbuser4=3)
    fields = [mock_field1, mock_field2, mock_field3]
    stash_list = [2]
    
    result = exclude_fields(fields, stash_list)
    assert len(result) == 2
    assert mock_field1.copy() in result
    assert mock_field3.copy() in result
    assert mock_field2.copy() not in result


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

                                                                                                  212,0-1       Bot


