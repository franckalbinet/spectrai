from setuptools import setup, find_packages
from os import path

here = path.dirname(__file__)

with open(path.join(here, "requirements.txt")) as f:
    install_requires = f.read().splitlines()

setup(
    name='spectrai',
    version='0.0.3',
    description='Assessing the potential of AI for spectroscopy and MIR one in particular',
    author='Franck Albinet',
    author_email='franckalbinet@gmail.com',
    packages=find_packages(),
    install_requires=install_requires,
    )
