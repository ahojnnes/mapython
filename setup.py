# coding: utf-8
import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
    
setup(
    name='mapython',
    version='0.5',
    license='MIT',
    
    description=('mapython is a map renderer for OpenStreetMap'),
    long_description=read('README'),
    keywords='OpenStreetMap render map',
    url='http://mapython.org/',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    author='Johannes Schönberger',
    author_email='johannes.schoenberger@tum.de',
    
    packages=['mapython'],
    scripts=['scripts/generate_tiles.py'],
    install_requires=[
        'shapely>=1.2.9',
        'sqlalchemy>=0.6',
        'geoalchemy>=0.5',
        'pyyaml>=3',
        'pyproj>=1.8',
        'pycairo>=1.8',
    ],
    package_data = {'mapython': ['styles/*']},
)

