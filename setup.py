#!/usr/bin/env python
#originally forked from https://github.com/jflesch/python-tesseract.git

from distutils.core import setup

setup(name='python-tesseract',
      version='1.0',
      description='Python Tesseract Command Line Invoker',
      author='Christopher Piekarski',
      author_email='chris@cpiekarski.com',
      keywords=['tesseract','ocr'],
      classifiers=[
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License',
                   'Programming Language :: Python :: 2.7',
                   'Operating System :: OS Independent',
                   ],
      url='https://github.com/chris-piekarski/python-tesseract',
      py_modules=['tesseract'],
     )