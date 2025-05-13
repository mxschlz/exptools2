import setuptools

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="exptools2",  # This is the name that will be used for pip install
    version="0.1.0",  # version number
    author="Max Schulz",
    author_email="schulz.max5@gmail.com",
    description="A Python-based platform for building trial-based experiments with PsychoPy", # A short description
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mxschlz/exptools2",  # Replace with your GitHub repo URL
    packages=setuptools.find_packages(), # Automatically find all packages
    # OR explicitly list them if find_packages() is too broad or you have a flat structure

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", # Choose your license
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha", # Or Beta, Production/Stable
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
    ],
    python_requires='>=3.10',  # Specify compatible Python versions
    install_requires=[
        'psychopy>=3.0.4',
        'pyyaml',
        'pandas>=0.23.0',
        'numpy>=1.14.3',
        'msgpack_numpy'
    ],
    # If you have data files that need to be included with your package:
    # package_data={
    #     'exptools2': ['data/*.csv', 'templates/*.html'],
    # },
    # include_package_data=True, # if you use MANIFEST.in for more complex data inclusion
)