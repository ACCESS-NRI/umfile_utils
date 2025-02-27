# UMfile_utils

UMfile_util is a Python library that provides specific tools to edit UM dump and field files.

# UMfile_utils Desciption

This package will include three abilities

### perturbIC.py 
If the simulation fails, this code allows for minor random perturbation of the input theta (surface termperature) in the restart files. 
Then the simulation can be rerun to avoid crashing. In the future functionality will be added to perturb other fields as well. 

### um_fields_subset.py

This code runs on a Dump file and allows the user to select a group of fields in the file to store 
in a new fields file or exclude a group of fields from the file. Both of these functionalities will 
create a new output file. 
NEED TO ADD USE CASES

### change_date.py
NEED TO ADD DESCRIPTION 


Currently these files only operate on Dump files and include a work around to deal with the river field grids.

## Installation
DICUSS AT SOME POINT

## Usage

```python
If the user wants to run perturbIC with a specific output filename
python perturbIC input_file_path -a 0.01 -s 2234 -o output_file_path

Otherwise it is optional perturbIC will create a filename from the input path
python perturbIC input_file_path -a 0.01 -s 2234

The amplitude and seed are also optional as well
python perturbIC input_file_path -a 0.01 -s 2234

To take a subset of field the user must provide a either a list of fields to exculde (-x)
python um_fields_subset.py input_file_path -x 155,156,3100,3101 

To take a subset of field the user must provide a either a list of fields to include (-v)
python um_fields_subset.py input_file_path -v 155,156,3100,3101

Or you can choose to have the program to only include pronostics -p
python um_fields_subset.py input_file_path -p

These three options must be run seperately

```

## Contributing



## License

NEED TO ADD THE LICENSE
