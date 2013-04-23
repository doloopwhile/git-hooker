#!/usr/bin/env python3
# coding: utf-8
from setuptools import setup
from io import open
import sys

setup(
    name='githooker',
    version='1.0',
    description='Yet another lightweight git hook manager',
    long_description=open('README.rst', encoding='utf-8').read(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
    ],
    keywords=[''],
    author='OMOTO Kenji',
    author_email='doloopwhile@gmail.com',
    license='MIT',

    py_modules=['githooker'],
)
