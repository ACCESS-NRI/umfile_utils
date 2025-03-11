from copy import deepcopy
from unittest.mock import MagicMock, patch

import mule  # noqa: F401
import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as stnp
from numpy.random import PCG64, Generator, choice, default_rng

from umfile_utils.perturbIC import (
    TIMESERIES_LBCODES,
    AdditionOperator,
    create_default_outname,
    create_perturbation,
    create_random_generator,
    is_field_to_perturb,
    main,
    parse_args,
    remove_timeseries,
    void_validation,
)

# Hypothesis settings to reuse in multiple tests
ARRAY_SHAPES = stnp.array_shapes(min_dims=2, max_dims=2, min_side=1, max_side=200)
ARRAY_DTYPES = stnp.floating_dtypes(sizes=(32, 64))
# Set to avoid overflow
ARRAY_ELEMENTS = st.floats(
    min_value=-1e10,
    max_value=1e10,
    allow_nan=False,                # Disallow NaN
    allow_infinity=False,           # Disallow Infinity
    allow_subnormal=False,          # Disallow subnormal floats
    width=32                        # Ensure compatibility with float32 or float64
) 

# Set max examples for hypothesis globally
settings.register_profile("default", max_examples=30)
settings.load_profile("default")

@pytest.fixture
def create_mock_umfile():
    def _mock_umfile():
        """Factory function to create a mule UMfile mock object and initialize it with empty fields."""
        return MagicMock(fields=[])

    return _mock_umfile

#This section sets up the testing for the parse args
@pytest.fixture
def create_mock_field():
    """Factory function to create a mule field mock object."""

    def _create_field(lbcode=0):
        return MagicMock(
            lbcode=lbcode,
        )
    return _create_field


def test_parse_args_default_args():
    """Test with default arguments."""
    test_args = ["perturbIC", "test_input_file"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.ifile == "test_input_file"
        assert args.amplitude == 0.01
        assert args.seed is None
        assert not args.validate
        assert args.output_path is None


def test_parse_args_all_arguments():
    """Test with all arguments provided."""
    test_args = ["perturbIC", "test_input_2", "-a", "0.5", "-s", "123", "--validate", "-o", "test_output_1"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.ifile == "test_input_2"
        assert args.amplitude == 0.5
        assert args.seed == 123
        assert args.validate
        assert args.output_path == "test_output_1"


def test_create_random_generator_no_argument():
    """Test the random generator creation without a seed."""
    rng = create_random_generator()
    assert isinstance(rng, Generator)
    assert not np.all(rng.random(10) == Generator(PCG64(None)).random(10))


@given(seed=st.integers(min_value=0))
def test_create_random_generator_with_seed(seed):
    """Test the random generator creation with a positive seed."""
    rng = create_random_generator(seed)
    assert isinstance(rng, Generator)
    assert np.all(rng.random(10) == Generator(PCG64(seed)).random(10))


def test_create_random_generator_negative_seed():
    """Test that a negative seed raises a ValueError."""
    with pytest.raises(ValueError):
        create_random_generator(-1)


@pytest.mark.parametrize(
    # description of the arguments
    "init_fields_lbcodes, result_fields_indeces, result_fields_length",
    [
        # Case 1: UM file with mixed fields
        (
            [1, 2, choice(TIMESERIES_LBCODES), 3, choice(TIMESERIES_LBCODES), choice(TIMESERIES_LBCODES), 4],
            [0, 1, 3, 6],
            4,
        ),
        # Case 2: UM file with no timeseries fields
        (
            [1, 2, 3, 4, 5],
            [0, 1, 2, 3, 4],
            5,
        ),
        # Case 3: UM file with all timeseries fields
        ([choice(TIMESERIES_LBCODES) for _ in range(8)], [], 0),
        # Case 4: UM file with no fields
        ([], [], 0),
    ],
    ids=[
        "mixed",
        "no_timeseries",
        "all_timeseries",
        "no_fields",
    ],
)
def test_remove_timeseries_(
    init_fields_lbcodes, result_fields_indeces, result_fields_length, create_mock_umfile, create_mock_field
):
    """Test remove_timeseries function when the UM file has no timeseries fields."""
    mock_umfile = create_mock_umfile()
    mock_umfile.fields = [create_mock_field(lbcode) for lbcode in init_fields_lbcodes]
    result = remove_timeseries(mock_umfile)
    assert len(result.fields) == result_fields_length
    assert result.fields == [mock_umfile.fields[ind] for ind in result_fields_indeces]


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


@given(
    shape=ARRAY_SHAPES,
    amplitude=st.floats(min_value=0, max_value=1e300),  # max_value is set to avoid overflow
)
def test_create_perturbation(shape, amplitude):
    """Test create_perturbation."""
    rng = default_rng()
    perturbation = create_perturbation(amplitude, rng, shape)
    # Test that the created perturbation has the correct shape.
    assert perturbation.shape == shape
    # Test that the created perturbation is in the correct range.
    assert np.all(perturbation >= -amplitude)
    assert np.all(perturbation <= amplitude)
    # Test that nullify_poles is true and first and last row (north and south poles) are 0
    assert np.all(perturbation[0, :] == 0)
    assert np.all(perturbation[-1, :] == 0)


def test_create_perturbation_preserve_poles():
    """Test create_perturbation with nullify_poles=False."""
    shape = (10, 20)
    amplitude = 3.0
    rng = default_rng()
    perturbation = create_perturbation(amplitude, rng, shape, nullify_poles=False)
    # Test that the created perturbation has the correct shape.
    assert perturbation.shape == shape
    # Test that the created perturbation is in the correct range.
    assert np.all(perturbation >= -amplitude)
    assert np.all(perturbation <= amplitude)
    # Test that nullify_poles is false and first and last row are not all 0
    assert not np.all(perturbation[0, :] == 0)
    assert not np.all(perturbation[-1, :] == 0)


@settings(deadline=None)
@given(seed=st.integers(min_value=0))
def test_create_perturbation_deterministic(seed):
    """Test if the perturbation is deterministic with a fixed random seed."""
    amplitude = 1.0
    shape = (13, 7)
    rng1 = np.random.default_rng(seed)
    perturbation1 = create_perturbation(amplitude, rng1, shape)
    rng2 = np.random.default_rng(seed)
    perturbation2 = create_perturbation(amplitude, rng2, shape)
    # Test that the results are identical
    np.testing.assert_array_equal(perturbation1, perturbation2)


@given(lbuser4=st.integers(), stash_to_perturb=st.integers())
def test_is_field_to_perturb_hypothesis(lbuser4, stash_to_perturb):
    """
    Hypothesis test to check the behavior of is_field_to_perturb with various
    combinations of lbuser4 and stash_to_perturb.
    """
    # Create a mock mule.Field object
    mock_field = MagicMock()
    mock_field.lbuser4 = lbuser4

    # Check if the function returns True when values match, and False otherwise
    expected_result = lbuser4 == stash_to_perturb
    assert is_field_to_perturb(mock_field, stash_to_perturb) == expected_result


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


class TestAdditionOperator:
    """Test the AdditionOperator class."""
    @given(array=stnp.arrays(dtype=ARRAY_DTYPES, shape=ARRAY_SHAPES, elements=ARRAY_ELEMENTS))
    def test_addition_operator_init(self, array):
        """Test the initialization of the AdditionOperator class."""
        operator = AdditionOperator(array)
        assert operator.array.shape == array.shape
        np.testing.assert_array_equal(operator.array, array)

    def test_addition_operator_new_field(self, create_mock_field):
        """Test the new_field method of the AdditionOperator class."""
        array = np.array([1, 2, 3])
        operator = AdditionOperator(array)
        source_field = create_mock_field()
        # Mock the copy method to return the same source_field
        source_field.copy.return_value = source_field
        new_field = operator.new_field(source_field)  # noqa: F841
        # Ensure that the copy method was called on the source_field
        source_field.copy.assert_called_once()

    @given(
        array=stnp.arrays(
            dtype=st.shared(ARRAY_DTYPES, key="dtype"),
            shape=st.shared(ARRAY_SHAPES, key="shape"),
            elements=ARRAY_ELEMENTS,
        ),
        source_data=stnp.arrays(
            dtype=st.shared(ARRAY_DTYPES, key="dtype"),
            shape=st.shared(ARRAY_SHAPES, key="shape"),
            elements=ARRAY_ELEMENTS,
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_addition_operator_transform_valid_shapes(self, array, source_data, create_mock_field):
        """Test the transform method of the AdditionOperator class, with valid shapes."""

        operator = AdditionOperator(array)
        source_field = create_mock_field()
        source_field.get_data.return_value = source_data  # Mock the get_data method to return source_data
        new_field = create_mock_field()
        result = operator.transform(source_field, new_field)
        expected_result = source_data + array
        np.testing.assert_array_equal(result, expected_result)

    def test_addition_operator_transform_incompatible_shapes(self, create_mock_field):
        """Test the transform method of the AdditionOperator class, with incompatible shapes."""
        array = np.array([[1, 2, 3], [4, 5, 6]])  # Shape (2, 3)
        array_shape = array.shape
        operator = AdditionOperator(array)
        source_field = create_mock_field()
        source_data = np.array([[5, 6], [7, 8]])  # Shape (2, 2)
        field_shape = source_data.shape
        source_field.get_data.return_value = source_data
        with pytest.raises(ValueError) as excmsg:
            operator.transform(source_field, create_mock_field())
            assert (
                excmsg
                == f"Array and field could not be broadcast together with shapes {array_shape} and {field_shape}."
            )


@patch("umfile_utils.perturbIC.parse_args")
@patch("umfile_utils.perturbIC.create_default_outname")
@patch("umfile_utils.perturbIC.create_random_generator")
@patch("umfile_utils.perturbIC.void_validation")
@patch("mule.DumpFile.from_file")
@patch("umfile_utils.perturbIC.remove_timeseries")
@patch("umfile_utils.perturbIC.is_field_to_perturb")
@patch("umfile_utils.perturbIC.create_perturbation")
@patch("umfile_utils.perturbIC.AdditionOperator")
def test_main(
    mock_addition_operator,
    mock_create_perturbation,
    mock_is_field_to_perturb,
    mock_remove_timeseries,
    mock_mule_dumpfile_from_file,
    mock_void_validation,
    mock_create_random_generator,
    mock_create_default_outname,
    mock_parse_args,
    create_mock_umfile,
    create_mock_field,
):
    """Test the main function."""
    lbcode_to_perturb = 1234

    # Mock the return value of parse_args
    mock_args = MagicMock(
        ifile="test_input_file",
        amplitude=0.01,
        seed=123,
        validate=True,
        output_path=None,
    )
    mock_parse_args.return_value = mock_args

    # Mock the return value of mule.DumpFile.from_file
    mock_ff = create_mock_umfile()
    mock_ff.fields = [
        create_mock_field(lbcode=lbcode_to_perturb),
        create_mock_field(lbcode=1),
        create_mock_field(lbcode=2),
    ]
    test_data = np.array([[1, 2, 3], [4, 5, 6]])
    mock_ff.fields[0].get_data.return_value = test_data
    mock_mule_dumpfile_from_file.return_value = mock_ff

    # Mock the return value of remove_timeseries
    mock_remove_timeseries.return_value = mock_ff

    # Mock is_field_to_perturb
    mock_is_field_to_perturb.side_effect = lambda field, stash: field.lbcode == lbcode_to_perturb

    main()

    # Assertions
    mock_parse_args.assert_called_once()
    mock_create_default_outname.assert_called_once_with(mock_args.ifile)
    mock_create_random_generator.assert_called_once_with(mock_args.seed)
    mock_mule_dumpfile_from_file.assert_called_once_with(mock_args.ifile)
    mock_remove_timeseries.assert_called_once_with(mock_ff)
    mock_is_field_to_perturb.assert_called()
    mock_create_perturbation.assert_called_once_with(
        mock_args.amplitude,
        mock_create_random_generator.return_value,
        test_data.shape,
    )
    mock_addition_operator.assert_called_once_with(mock_create_perturbation.return_value)
    mock_ff.to_file.assert_called_once_with(mock_create_default_outname.return_value)
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
    assert mock_ff.validate == mock_void_validation
    mock_create_default_outname.assert_not_called()

