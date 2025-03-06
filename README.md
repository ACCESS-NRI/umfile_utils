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

If the user wants to run perturbIC with a specific output filename
```python
python perturbIC input_file_path -a 0.01 -s 2234 -o output_file_path
```
Otherwise it is optional perturbIC will create a filename from the input path
```python
python perturbIC input_file_path -a 0.01 -s 2234
```

The amplitude and seed are also optional as well
```python
python perturbIC input_file_path -a 0.01 -s 2234
```
### um_fields_subset.py

To take a subset of field the user must provide a either a list of fields to exculde (-x)
```python
python um_fields_subset.py input_file_path -x 155,156,3100,3101
```

To take a subset of field the user must provide a either a list of fields to include (-v)
```python
python um_fields_subset.py input_file_path -v 155,156,3100,3101
```

Or you can choose to have the program to only include pronostics -p
```python
python um_fields_subset.py input_file_path -p
```
These three options must be run seperately

### change_dump_date.py
User can either enter in a year, month, and day seperately (-y -m -d),
```python
python change_dump_date.py input_file_path -y 2025 -m 1 -d 22
```
or the user can enter in a date in the format of YYYYMMDD.
```python
python change_dump_date.py input_file_path -date 20250122
```
## Contributing
TO BE ADDED


## License
TO BE ADDED
