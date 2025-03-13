# UMfile_utils

UMfile_util is a Python library that provides specific tools to process [UM files](https://code.metoffice.gov.uk/doc/um/latest/papers/umdp_F03.pdf).

## List of functions

- [perturbIC](#perturbic)
- [um_fields_subset](#um-fields-subset)
- [change_date](#change-date)

### perturbIC
Apply a random perturbation to a restart file, with an optional seed to control the random generation.
This can be useful for simulations that fail due to random divergence or for generating multiple ensemble members in climate experiments.

Run `pertubIC --help` for detailed usage information.

### um_fields_subset

Subset a UM file to generate an output containing only selected fields. Options are available to include or exclude specific STASH variables.

Run `um_fields_subset --help` for detailed usage information.

### change_date
Change the time metadata of a UM restart file, without modifying its data content.

Run `change_date --help` for detailed usage information

## Installation
TO BE ADDED

## Contributing
TO BE ADDED

## License
TO BE ADDED
