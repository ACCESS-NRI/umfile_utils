import pytest
import sys
from perturbIC import parse_args, set_seed, create_outfile, create_perturbation, is_end_of_file,do_perturb, SetAdditionOperator
from unittest.mock import Mock, MagicMock
import numpy as np
import numpy.random as rs


@pytest.fixture
def mock_command_line():
    """
    This function create a callable command line input.
    
    Returns
    __________
        list - Command line arguements
    """
    return ["perturbIC.py", "-a", "0.4", "-s", "23452",
            "~/example/path/to/the/file/restart_dump.astart"]

@pytest.fixture
def mock_perturbation():
    """
    This function create a callable perturbation dimensions.
    
    Returns
    __________
        nlon - int
        nlat - int
    """

    nlon = 192
    nlat = 145

    return nlon, nlat

@pytest.fixture
def mock_metadata():
    """
    This function create a callable metadata.

    Returns
    __________
        list - Command line arguements
    """

    metadata_index_false = 24
    metadata_index_true = -99

    end_of_data = -99

    return metadata_index_false,  metadata_index_true, end_of_data


def test_parse_args(monkeypatch, mock_command_line):
    """
    This function tests the parse_args function with the fake commandline arguments.
    
    Parameters
    __________
        fixture - A class of helpful methods for mock data 
        fixture - A list of command line arguements

    Returns
    __________
        The results of assertion tests. 
    """

    monkeypatch.setattr(sys, "argv", mock_command_line)
    args = parse_args()
    assert args.amplitude == 0.4
    assert args.seed == 23452
    assert args.ifile == '~/example/path/to/the/file/restart_dump.astart'

def test_creating_output_file(monkeypatch, mock_command_line):
    """
    This function tests the creating the output filename.
    
    Parameters
    __________
        fixture - A list of command line arguements
        
    Returns
    __________
        The results of assertion tests. 
    """

    monkeypatch.setattr(sys, "argv", mock_command_line)
    args = parse_args()
    output_filename = create_outfile(args)
    print(output_filename)
    assert output_filename == "~/example/path/to/the/file/restart_dump_perturbed.astart"

def test_create_perturbation(monkeypatch, mock_command_line, mock_perturbation):
    """
    This function tests the create_perturbation function with the fake commandline arguments
    Inputs
        fixture - A class of helpful methods for mock data 
        fixture - A list of command line arguements
    Outputs 
        The results of assertion tests. 
    """

    monkeypatch.setattr(sys, "argv", mock_command_line)
    args = parse_args()
    rs = set_seed(args)
    nlon, nlat = mock_perturbation

    perturb = create_perturbation(args, rs, nlon, nlat)
    assert perturb.shape ==  (nlat,nlon)

def test_is_end_of_file_keep_going(mock_metadata):
    """
    This function tests the detection of the edge of the data.
    
    Parameters
    __________
        fixture - A fake list of arrays and a fake index
        
    Returns
    __________
        The results of assertion tests. 
    """

    metadata_index_false, metadata_index_true,end_of_data =  mock_metadata
    assert is_end_of_file(metadata_index_false, end_of_data) == False
    assert is_end_of_file(metadata_index_true, end_of_data) == True



def test_finding_field(mock_perturbation):
    """
    This function in the perturbIC.py is written to both check the itemcode when 
    it finds the correct item code to read the field and add the perturbation.

    Parameters
    __________
        fixture - A fake list of arrays and a fake index
        
    Returns
    __________
        The results of assertion tests. 
    """
    field_theta = Mock()
    field_not_theta = Mock()

    # Set up the real item code and itemcode inputs to test the conditional
    stash_code = 4
    field_theta.lbuser4 = 4
    field_not_theta.lbuser4 = 3

    # Testing if the perturb conditional works correctly and triggers for the right field
    assert do_perturb(field_theta, stash_code) == True
    assert do_perturb(field_not_theta, stash_code) == False

def test_operator_initialization():
    """
    This function test that the operator initializes with the correct perturbation.

    Returns
    ________
        The results of testing if the peturbation intialize worked 

    """
    perturb = np.array([1, 2, 3])
    operator = SetAdditionOperator(perturb)
    assert np.array_equal(operator.perturbation, perturb)
    
def test_transform():
    """
    This function test the transform method of the SetAdditionOperator class
    It creates a fake perturbationm and fake source data array then it sets
    up the operator and performs the transformation

    Returns
    ________
     
        Assertion is True if the resulting array is what is expected
    
    """
    perturb = np.array([34, 213, 654])
    source_data = np.array([200,234,453])

    # Mock source_field
    source_field = MagicMock()
    source_field.get_data.return_value = source_data  # Mock get_data

    operator = SetAdditionOperator(perturb)
    result = operator.transform(source_field, None)

    source_field.get_data.assert_called_once()  # Ensure get_data is called
    expected_result = source_data + perturb

    assert np.array_equal(result, expected_result)

                                                               
