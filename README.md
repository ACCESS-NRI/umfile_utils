# UMfile_utils

UMfile_util is a Python library that provides specific tools to process [UM files](https://code.metoffice.gov.uk/doc/um/latest/papers/umdp_F03.pdf).

- [Installation](#installation)
- [List of functions](#list-of-functions)
  - [perturbIC](#perturbic)
  - [um\_fields\_subset](#um_fields_subset)
  - [change\_date](#change_date)
- [Contributing](#contributing)
  - [Development/Testing instructions](#developmenttesting-instructions)
  - [Clone/fork umfile\_utils GitHub repo](#clonefork-umfile_utils-github-repo)
  - [Create a micromamba/conda testing environment](#create-a-micromambaconda-testing-environment)
  - [Install umfile\_utils as a development package](#install-umfile_utils-as-a-development-package)
  - [Running the tests](#running-the-tests)
- [License](#license)

## Installation
`umfile_utils` is released as a `conda` package within the `accessnri` Anaconda.org channel. 
To install it, run:
```
conda install accessnri::umfile_utils
```

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

## Contributing
External contributions (not from ACCESS-NRI) are accepted in the form of issues and PRs from forked repos.

### Development/Testing instructions
For development/testing, it is recommended to install `umfile_utils` as a development package within a `micromamba`/`conda` testing environment.

### Clone/fork umfile_utils GitHub repo
> [!NOTE]
> If you are not part of the ACCESS-NRI, you can fork the repo instead.
```
git clone git@github.com:ACCESS-NRI/umfile_utils.git
```

### Create a micromamba/conda testing environment
> [!TIP]  
> In the following instructions `micromamba` can be replaced with `conda`.

```
cd umfile_utils
micromamba env create -n umfile_utils_dev --file .conda/env_dev.yml
micromamba activate umfile_utils_dev
```

### Install umfile_utils as a development package
```
pip install --no-deps --no-build-isolation -e .
```

### Running the tests

To manually run the tests, from the `umfile_utils` directory, you can:

1. Activate your [micromamba/conda testing environment](#create-a-micromamba-conda-testing-environment)
2. Run the following command:
   ```
   pytest
   ```

## License
[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)
