import os
import glob
from setuptools import setup

datadir = 'data'
datafiles = [(datadir, [f for f in glob.glob(os.path.join(datadir, '*'))])]

setup(
    name='pymodoro',
    version='0.2',
    py_modules=['pymodoro', 'pymodoroi3'],
    data_files=datafiles,
    entry_points={"console_scripts": ["pymodoro = pymodoro:main", "pymodoroi3 = pymodoroi3:main"]},
)
