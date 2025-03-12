# UMfile_utils

UMfile_util is a Python library that provides specific tools to process [UM files](https://code.metoffice.gov.uk/doc/um/latest/papers/umdp_F03.pdf).

## List of functions

- [perturbIC](#perturbic)
- [um_fields_subset](#um-fields-subset)
- [change_date](#change-date)

### perturbIC.py 
The `perturbIC` function applies a random perturbation to a restart file, with an optional seed to control the random generation. 
This can be useful for simulations that fail due to random divergence or for generating multiple ensemble members in climate experiments.

Run `pertubIC --help` for detailed usage information.

### um_fields_subset.py

This code runs on a Dump file and allows the user to select a group of fields in the file to store  in a new fields file or exclude a 
group of fields from the file. Both of these functionalities will create a new output file. 


### change_date.py
This code runs on any UM field file. It allows the user to change the timestamps (metadata) of a restart dump file, without modifying 
its data content. It changes the initial and valid date of the header and the header date of each field in the file.


Currently these programs include a work around to deal with the river field grids and need to be run without the mule validation. 
This is defualt to the programs. The validation can be included using --validate

## Installation


## Usage
### perturbIC.py 


## Contributing
TO BE ADDED


## License
TO BE ADDED
