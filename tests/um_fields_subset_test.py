
import warnings
import pytest
from copy import deepcopy
from unittest.mock import patch, MagicMock
from hypothesis import HealthCheck, given, settings
from hypothesis.extra import numpy as stnp
from hypothesis import given, settings, strategies as st
from um_fields_subset_mule import (parse_args, field_not_present_warning, include_fields, exclude_fields, filter_fieldsfile, create_default_outname, PROGNOSTIC_STASH_CODES, void_validation)
from hypothesis import given, strategies as st
import numpy as np
from itertools import chain
PROGNOSTIC_STASH_CODES = tuple(chain(range(1,999+1), range(33001,34999+1)))

# Define strategy for creating fake STASH codes and fields to test the warning function.
stash_code_strategy = st.lists(st.integers(min_value=1, max_value=35000), min_size=1, max_size=10)
fields_strategy = st.lists(stnp.arrays(dtype=np.int32, shape=(10,)), min_size=1, max_size=5)

# Hypothesis-based test for field_not_present_warning.
@given(stash_list=stash_code_strategy, fields=fields_strategy)
@settings(suppress_health_check=[HealthCheck.filter_too_much])

def test_field_not_present_warning(stash_list, fields):
    """
    This function tests the warning function to issue a warning when a STASH code is not included in the file.
    """
    # Flatten each numpy array in the list of fields (not the list itself).
    mock_fields = [MagicMock(lbuser4=item) for array in fields for item in array.flatten()]

    # Set up mocking of the warnings.warn function.
    with patch("warnings.warn") as mock_warn:
        # Convert stash_list to a set for unique values.
        field_not_present_warning(mock_fields, set(stash_list))

        # Calculate missing stash codes.
        existing_codes = {item for array in fields for item in array.flatten()}
        missing_codes = set(stash_list) - existing_codes

        if missing_codes:
            # Expected warning message.
            expected_warning = f"The following STASH codes are not found in the input file: {sorted(missing_codes)}"

            # Capture actual warning message.
            actual_warning = str(mock_warn.call_args[0][0])

            # Normalize by stripping brackets and whitespace before comparing.
            expected_set = set(map(str, sorted(missing_codes)))
            actual_set = set(actual_warning.split(": ")[1].strip(" {}").split(", "))

            assert expected_set == actual_set, f"Expected: {expected_set}, Actual: {actual_set}"


# Define a consistent range of field values (1 to 40000). 
# Should have all the fields for this test not aiming to test the warning.
consistent_field_values = list(range(1, 40001))

# Define strategies for generating include/exclude lists.
include_strategy = st.lists(st.integers(min_value=1, max_value=40000), min_size=1, max_size=10)
exclude_strategy = st.lists(st.integers(min_value=1, max_value=40000), min_size=1, max_size=10)

# Define a simple mock field class to replace MagicMock.
class MockField:
    def __init__(self, lbuser4):
        self.lbuser4 = lbuser4

    def copy(self):  # Ensure copying works properly.
        return MockField(self.lbuser4)


#Test for include filter
@given(fields=st.lists(st.sampled_from(consistent_field_values), min_size=1, max_size=5), include_list=include_strategy)
def test_filter_fieldsfile_include(fields, include_list):
    """
    This function testing the fitlering when it is an include lsit and prognostic is False
    """
    # Create a mock file with mock fields.
    mock_file = MagicMock()
    mock_file.fields = [MockField(f) for f in fields]  # Fields now have proper lbuser4 values.

    # Call filter_fieldsfile with the include list
    filtered_file = filter_fieldsfile(mock_file, False, include_list=include_list, exclude_list=None)

    # Check that all included codes appear in the filtered file
    assert all(f.lbuser4 in include_list for f in filtered_file.fields)

    # Ensure that fields not in include_list are excluded
    for f in filtered_file.fields:
        assert f.lbuser4 in include_list
        

@given(fields=st.lists(st.sampled_from(consistent_field_values), min_size=1, max_size=5))
def test_filter_fieldsfile_prog(fields):
    """
    This function tests when the prognostic = True
    """
    # Create a mock file with mock fields.
    mock_file = MagicMock()
    mock_file.fields = [MockField(f) for f in fields]  # Fields now have proper lbuser4 values.

    # Call filter_fieldsfile with the include list.
    filtered_file = filter_fieldsfile(mock_file, True, include_list=None, exclude_list=None)

    # Check that all pronostic codes appear in the filtered file.
    assert all(f.lbuser4 in PROGNOSTIC_STASH_CODES for f in filtered_file.fields)

    # Ensure that fields are only prognostic.
    for f in filtered_file.fields:
        assert f.lbuser4 in PROGNOSTIC_STASH_CODES

@given(fields=st.lists(st.sampled_from(consistent_field_values), min_size=1, max_size=5), exclude_list=include_strategy)
def test_filter_fieldsfile_exclude(fields, exclude_list):
    """
    This function tests when filter fields function is using the exclude list. 
    """
    # Create a mock file with mock fields.
    mock_file = MagicMock()
    mock_file.fields = [MockField(f) for f in fields]  # Fields now have proper lbuser4 values.

    # Call filter_fieldsfile with the include list.
    filtered_file = filter_fieldsfile(mock_file, False, include_list=None, exclude_list=exclude_list)

    # Ensure that excluded codes do not appear in the filtered file/
    assert all(f.lbuser4 not in exclude_list for f in filtered_file.fields)

    # Ensure that only fields not in the exclude list remain.
    for f in filtered_file.fields:
        assert f.lbuser4 not in exclude_list


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


