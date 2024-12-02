import pytest
import sys
from perturbIC import parse_args, create_random_generator, remove_timeseries, is_field_to_perturb, create_default_outname, create_perturbation, AdditionOperator
from unittest.mock import patch, Mock, MagicMock
import numpy as np
import numpy.random as rs

#This section sets up the testing for the parse args
@pytest.fixture
def fake_args(monkeypatch):
    """
    Fixture to set fake command-line arguments.
    """
    def _fake_args(args):
        monkeypatch.setattr('sys.argv', args)
        return args
    return _fake_args


@pytest.mark.parametrize(
    "input_args, expected",
    [
        # Case 1: Test only essential arguments.
        (["script.py", "input_file"], {"ifile": "input_file", "amplitude": 0.01, "seed": None, "validate": False, "output_path": None}),
        # Case 2: Test the amplitude
        (["script.py", "input_file", "-a", "0.05"], {"ifile": "input_file", "amplitude": 0.05, "seed": None, "validate": False, "output_path": None}),
        # Case 3: Test the validate
        (["script.py", "input_file", "-s", "42", "--validate"], {"ifile": "input_file", "amplitude": 0.01, "seed": 42, "validate": True, "output_path": None}),
        # Case 4: Inclusion of the output file
        (["script.py", "input_file", "-o", "output_file"], {"ifile": "input_file", "amplitude": 0.01, "seed": None, "validate": False, "output_path": "output_file"}),
    ],
)
def test_parse_args(fake_args, input_args, expected):
    """
    Test parse_args function with test 4 cases if if the optional arguements are not included.
    """
    fake_args(input_args)
    args = parse_args()
    for key, value in expected.items():
        assert getattr(args, key) == value

#This section tests the output file creation. 
@pytest.mark.parametrize(
    # description of the arguments
    "existing_files, filename, expected_output",
    [
        # Case 1: Filename with suffix doesn't exist, return filename with suffix
        ([], "testfilename", "testfilename_perturbed"),
        # Case 2: Filename with suffix exists, returns filename with suffix appending 1
        (["testfilename_perturbed"], "testfilename", "testfilename_perturbed1"),
        # Case 3: Filename with suffix and a few numbered versions exist, returns 
        # filename with suffix and the first numbered version that doesn't exist
        (
            ["testfilename_perturbed", "testfilename_perturbed1", "testfilename_perturbed2"],
            "testfilename",
            "testfilename_perturbed3",
        ),
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

#This section of code tests the removal of the timeseries
class MockField:
    """
    Mock class to simulate a field with an lbcode attribute.
    """
    def __init__(self, lbcode):
        self.lbcode = lbcode

class MockDumpFile:
    """
    Mock class to simulate a mule DumpFile.
    """
    def __init__(self, fields):
        self.fields = fields

    def copy(self):
        """
        Simulate the copy method of a mule DumpFile.
        """
        return MockDumpFile(self.fields[:])

TIMESERIES_LBCODES = [31320]
@pytest.mark.parametrize(
    "input_fields, expected_codes",
    [   #Time series is the first field
        ([MockField(31320), MockField(1001)], [1001]),
        #If it is all timeseries
        ([MockField(31320), MockField(31320)], []),
        #If none are timeseries
        ([MockField(1001), MockField(2002)], [1001, 2002]),
        #If there are no files
        ([], []),
    ],
)
def test_remove_timeseries(input_fields, expected_codes):
    """
    Test the remove_timeseries function with various input scenarios.
    """
    mock_dumpfile = MockDumpFile(input_fields)
    result = remove_timeseries(mock_dumpfile)
    result_codes = [field.lbcode for field in result.fields]

    assert result_codes == expected_codes

@pytest.fixture
def mock_metadata():
    """
    This function create a callable um metadata

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


#This section tests creating the perturbation
@pytest.mark.parametrize(
    "amplitude, shape, nullify_poles, expected_shape",
    [
        (0.5, (10, 20), True, (10, 20)),
        (1.0, (5, 5), False, (5, 5)),
        (0.3, (3, 7), True, (3, 7)),
    ],
)

def test_create_perturbation(amplitude, shape, nullify_poles, expected_shape):
    """
    Test the create_perturbation function with different amplitudes, shapes, and nullify_poles settings.
    """
    random_seed = np.random.default_rng(43)
    # Create the perturbation
    perturbation = create_perturbation(amplitude, random_seed, shape, nullify_poles)

    # Check the shape of the perturbation
    assert perturbation.shape == expected_shape, "Perturbation shape does not match expected shape"

    # Check that values are within the range [-amplitude, amplitude]
    assert np.all(perturbation >= -amplitude) and np.all(perturbation <= amplitude), \
        "Perturbation values exceed specified amplitude range"

    # Check nullification of poles
    if nullify_poles:
        assert np.all(perturbation[0, :] == 0) and np.all(perturbation[-1, :] == 0), \
            "Perturbation poles were not nullified as expected"
    else:
        assert not (np.all(perturbation[0, :] == 0) and np.all(perturbation[-1, :] == 0)), \
            "Perturbation poles should not have been nullified"

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
                                                               
