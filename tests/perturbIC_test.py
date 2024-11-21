import pytest
import sys
from perturbIC import parse_args, create_random_generator, remove_timeseries, is_field_to_perturb, create_default_outname, create_perturbation, AdditionOperator
from unittest.mock import Mock, MagicMock
import numpy as np
import numpy.random as rs


@pytest.fixture
def mock_command_line():
    """
    This function create a callable command line input
    
    Outputs
        list - Command line arguements
    """
    return ["perturbIC.py", "-a", "0.4", "-s", "23452",
            "~/example/path/to/the/file/restart_dump.astart"]

@pytest.fixture
def mock_perturbation():
    """
    This function create a callable perturbation dimensions
    
    Outputs
        nlon - int
        nlat - int
    """

    nlon = 192
    nlat = 145

    return nlon, nlat

@pytest.fixture
def mock_metadata():
    """
    This function create a callable metadata

    Outputs
        list - Command line arguements
    """

    # Mock fields with different lbuser4 values
    field_theta = MagicMock()
    field_not_theta = MagicMock()

    # Correctly set the lbuser4 attribute
    field_theta.lbuser4 = 4
    field_not_theta.lbuser4 = 56
    stash_code = 4

    return field_theta, field_not_theta, stash_code

def test_parse_args(monkeypatch, mock_command_line):
    """
    This function tests the parse_args function with the fake commandline arguments
    Inputs
       fixture - A class of helpful methods for mock data 
        fixture - A list of command line arguements
    Outputs 
        The results of assertion tests. 
    """

    monkeypatch.setattr(sys, "argv", mock_command_line)
    args = parse_args()
    assert args.amplitude == 0.4
    assert args.seed == 23452
    assert args.ifile == "~/example/path/to/the/file/restart_dump.astart"

def test_create_default_outname(monkeypatch, mock_command_line):
    """
    This function tests the creating the output file name
    Inputs 
        fixture - A list of command line arguements
    Outputs 
        The results of assertion tests. 
    """

    monkeypatch.setattr(sys, "argv", mock_command_line)
    args = parse_args()
    output_filename = create_default_outname(args.ifile)
    #asssert output_filename == "~/example/path/to/the/file/restart_dump_perturbed.astart"
    assert output_filename == "~/example/path/to/the/file/restart_dump.astart_perturbed"

def test_remove_timeseries():

    # Mock fields and their lbcode values
    field1 = MagicMock()
    field2 = MagicMock()
    field3 = MagicMock()
    field1.lbcode = 23
    field2.lbcode = 345
    field3.lbcode = 31320

    # Mock the fields file
    test_fields = MagicMock()
    test_fields.fields = [field1, field2, field3]

    # Mock the copy method to return a new object (to simulate deep copy behavior)
    copied_fields = MagicMock()
    copied_fields.fields = test_fields.fields.copy()
    test_fields.copy.return_value = copied_fields

    # Run the function
    out_fields = remove_timeseries(test_fields)

    # Assertions
    assert len(out_fields.fields) == 2
    assert field1 in out_fields.fields
    assert field2 in out_fields.fields
    assert field3 not in out_fields.fields


def test_create_perturbation(monkeypatch, mock_command_line, mock_perturbation):
    """
    This function tests the create_perturbation function with the fake commandline arguments
    Inputs
        fixture - A class of helpful methods for mock data 
        fixture - A list of command line arguements
    Outputs 
        The results of assertion tests. 
    """

    amplitude = 0.4
    seed = 123
    rs = create_random_generator(seed)
    nlon, nlat = mock_perturbation

    perturb = create_perturbation(amplitude, rs, [nlat, nlon])
    assert perturb.shape ==  (nlat,nlon)

def test_is_field_to_perturb(mock_metadata):

    """
    Tests the item code conditional

    Inputs
        fixture - A fake list of arrays and a fake index
    Outputs 
        The results of assertion tests. 
    """

    field_theta, field_not_theta, stash_code = mock_metadata

    # Assertions to verify the function's behavior
    assert is_field_to_perturb(field_theta, stash_code) == True, "field_theta should match the stash_code"
    assert is_field_to_perturb(field_not_theta, stash_code) == False, "field_not_theta should not match the stash_code"


def test_operator_initialization():
    """
    Test the addition operator..

    Outputs
        The results of testing if the peturbation intialize worked 

    """

    # Mock the source field
    source_field = MagicMock()
    source_field.get_data.return_value = np.array([[1, 2], [3, 4]])

    # Mock the new field
    new_field = MagicMock()

    # Array to add
    array_to_add = np.array([[10, 20], [30, 40]])
    
    # Create the operator
    operator = AdditionOperator(array_to_add)

    # Test transform method
    result = operator.transform(source_field, new_field)

    # Expected output
    expected = np.array([[11, 22], [33, 44]])

    # Assertions
    np.testing.assert_array_equal(result, expected)
                                                               
