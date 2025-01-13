import pytest
from um_fields_subset_mule import parse_arguments


@pytest.mark.parametrize(
    "args, expected",
    [
        (["-i", "input.um", "-o", "output.um", "-v", "1,2,3"],
         {"ifile": "input.um", "ofile": "output.um", "vlist": [1, 2, 3], "xlist": [], "nfields": 9999999999, "prognostic": False, "section": False, "validate": False}),
        (["-i", "input.um", "-o", "output.um", "-x", "4,5", "--validate"],
         {"ifile": "input.um", "ofile": "output.um", "vlist": [], "xlist": [4, 5], "nfields": 9999999999, "prognostic": False, "section": False, "validate": True}),
        (["-i", "input.um", "-o", "output.um", "-n", "10", "-p", "-s", "-x", "7,8"],
         {"ifile": "input.um", "ofile": "output.um", "vlist": [], "xlist": [7, 8], "nfields": 10, "prognostic": True, "section": True, "validate": False})
        ]
)



def test_parse_arguments_valid(args, expected, monkeypatch):
    """
    Test parse_arguments function with valid inputs.
    """
    monkeypatch.setattr("sys.argv", ["script_name"] + args)
    parsed_args = parse_arguments()
    for key, value in expected.items():
        assert getattr(parsed_args, key) == value



def test_parse_arguments_invalid_vlist_format(monkeypatch):
    """
    Test parse_arguments with improperly formatted -v argument.
    """
    monkeypatch.setattr("sys.argv", ["script_name", "-i", "input.um", "-o", "output.um", "-v", "1,a,3"])
    with pytest.raises(ValueError):
        parse_arguments()

