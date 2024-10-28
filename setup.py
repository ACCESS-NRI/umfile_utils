from setuptools import setup, find_packages

setup(
    name="umfile_utils",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Add your dependencies here, e.g., "numpy", "requests", etc.
    ],
    entry_points={
        # Optional: Add command line scripts or other entry points here.
    },
)
