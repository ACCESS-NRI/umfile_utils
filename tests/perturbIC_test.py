import pytest
import sys
from perturbIC import parse_args, set_seed, create_perturbation, is_end_of_file,  if_perturb
from unittest.mock import Mock
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
            "-o", "restart_dump_copy_perturb.astart",
            "~/access-esm1.5/preindustrial+concentrations/archive/restart000/atmosphere/restart_dump_copy.astart"]

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

    metadata_index_false = 43
    metadata_index_true = -99
    end_of_data = -99

    return metadata_index_false,  metadata_index_true, end_of_data

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
    assert args.output == "restart_dump_copy_perturb.astart"

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
    This function tests the detection of the edge of the data
    Inputs
        fixture - A fake list of arrays and a fake index
    Outputs 
        The results of assertion tests. 
    """

    metadata_index_false, metadata_index_true,end_of_data =  mock_metadata
    assert is_end_of_file(metadata_index_false, end_of_data) == False
    assert is_end_of_file(metadata_index_true, end_of_data) == True

def test_applying_perturbation(mock_perturbation):
    """
    This function tests the addition of the perturbation to the correct field 
    This function in the perturbIC.py is written to both check the itemcode when 
    it finds the correct item code to read the field and add the perturbation.


    Inputs
        fixture - A fake list of arrays and a fake index
    Outputs 
        The results of assertion tests. 
    """

    #Create random perturbation
    nlon, nlat = mock_perturbation
    perturb = 0.5 * (2.*rs.random(nlon*nlat).reshape((nlat,nlon))-1.)
    perturb[0] = 0
    perturb[-1] = 0

    #Create a fake data array to simulate the numpy array that is 
    #To mock the method readfld that reads the field corresponding 
    #To the itemcode 
    shape = (nlat, nlon)  # Example shape of 3 rows and 4 columns
    mock_data = Mock()
    mock_data.readfld.return_value = np.ones(shape)
    metadata_index = 4
    surface_temp_item_code = 4
    endgame = 388
    k = 0

    #Run the fucntion to get the outputs
    is_perturb,a = if_perturb(metadata_index,k,mock_data,perturb,surface_temp_item_code,endgame)

    #Testing if the perturb conditional works and if the resulting array is correct
    testing_a = np.round((a - perturb) / np.ones(shape),0)
    assert is_perturb == True
    assert a.shape == (nlat, nlon)
    assert testing_a.all() == 1.
