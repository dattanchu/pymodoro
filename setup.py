from setuptools import setup

setup(
    name='pymodoro',
    version='0.4',
    packages=['pymodoro'],
    package_data={'pymodoro': ['data/*']},
    entry_points={
        "console_scripts": [
            "pymodoro = pymodoro.pymodoro:main",
            "pymodoroi3 = pymodoro.pymodoroi3:main"
        ]
    },
)
