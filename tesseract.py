#!/usr/bin/env python
'''
Python-tesseract is an optical character recognition (OCR) tool for python.
That is, it will recognize and "read" the text embedded in images.

Python-tesseract is a wrapper for google's Tesseract-OCR
( http://code.google.com/p/tesseract-ocr/ ).  It is also useful as a
stand-alone invocation script to tesseract, as it can read all image types
supported by the Python Imaging Library, including jpeg, png, gif, bmp, tiff,
and others, whereas tesseract-ocr by default only supports tiff and bmp.
Additionally, if used as a script, Python-tesseract will print the recognized
text in stead of writing it to a file. It also support bounding box data.
Support for confidence estimates is planned for future releases.


USAGE:
From the shell:
 $ ./tesseract.py test.png                  # prints recognized text in image
 $ ./tesseract.py -l fra test-european.jpg  # recognizes french text
In python:
 > import Image
 > from tesseract import image_to_string
 > print image_to_string(Image.open('test.png'))
 > print image_to_string(Image.open('test-european.jpg'), lang='fra')


INSTALLATION:
* Python-tesseract requires python 2.5 or later.
* You will need the Python Imaging Library (PIL).  Under Debian/Ubuntu, this is
  the package "python-imaging".
* Install google tesseract-ocr from http://code.google.com/p/tesseract-ocr/ .
  You must be able to invoke the tesseract command as "tesseract". If this
  isn't the case, for example because tesseract isn't in your PATH, you will
  have to change the "TESSERACT_CMD" variable at the top of 'tesseract.py'.


COPYRIGHT:
Python-tesseract is released under the GPL v3.
Copyright (c) Samuel Hoffstaetter, 2009
http://wiki.github.com/hoffstaetter/python-tesseract

'''

# CHANGE THIS IF TESSERACT IS NOT IN YOUR PATH, OR IS NAMED DIFFERENTLY
TESSERACT_CMD = 'tesseract'

import Image
import subprocess
import sys
import os
import glob

__all__ = ['image_to_string']

_convertname = lambda x : "tess_{}_tmp.bmp".format(x)
_outputname = lambda x : "tess_out_{}".format(x)
_imageOpen = lambda x : Image().open(x)
_makebmp = lambda x, y : _imageOpen(x).save(y)

_delete = lambda x : os.remove(x) if os.path.exists(x) else None

def _readFile(name):
    with open(name) as f:
        d = f.read()
    return d

def _runTesseract(input_filename, output_filename_base, lang=None,
                  boxes=False):
    '''
    runs the command:
        `TESSERACT_CMD` `input_filename` `output_filename_base`

    returns the exit status of tesseract, as well as tesseract's stderr output

    '''

    command = [TESSERACT_CMD, input_filename, output_filename_base]

    if lang is not None:
        command += ['-l', lang]

    if boxes:
        command += ['batch.nochop', 'makebox']

    proc = subprocess.Popen(command,
            stderr=subprocess.PIPE)
    # Beware that in some cases, tesseract may print more on stderr than
    # allowed by the buffer of subprocess.Popen.stderr. So we must read stderr
    # asap or Tesseract will remain stuck when trying to write again on stderr.
    # In the end, we just have to make sure that proc.stderr.read() is called
    # before proc.wait()
    errors = proc.stderr.read()
    return (proc.wait(), errors)

def get_errors(error_string):
    '''
    returns all lines in the error_string that start with the string "error"

    '''

    lines = error_string.splitlines()
    error_lines = tuple(line for line in lines if line.find('Error') >= 0)
    if len(error_lines) > 0:
        return '\n'.join(error_lines)
    else:
        return error_string.strip()

class TesseractError(Exception):
    """
    Exception raised when tesseract fails.
    """
    def __init__(self, status, message):
        Exception.__init__(self, message)
        self.status = status
        self.message = message
        self.args = (status, message)


class TesseractBox(object):
    """
    Tesseract Box: Tesserax boxes are rectangles around each individual
    character recognized in the image.
    """
    def __init__(self, char, position, page):
        """
        Instantiate a tesseract box

        Arguments:
            char --- character found in this box
            position --- the position of the box on the image. Given as a
                tuple of tuple:
                ((width_pt_x, height_pt_x), (width_pt_y, height_pt_y))
            page --- page number, as specified in the box file (usually 0)
        """
        self.char = char
        self.position = position
        self.page = page

    def __str__(self):
        return "%s %d %d %d %d %d" % (
            self.char,
            self.position[0][0],
            self.position[0][1],
            self.position[1][0],
            self.position[1][1],
            self.page
        )


def read_boxes(file_descriptor):
    """
    Extract of set of TesseractBox from the lines of 'file_descriptor'
    """
    boxes = []  # note that the order of the boxes may matter to the caller
    for line in file_descriptor.readlines():
        line = line.strip()
        if line == "":
            continue
        elements = line.split(" ")
        if len(elements) < 6:
            continue
        position = ((int(elements[1]), int(elements[2])),
                    (int(elements[3]), int(elements[4])))
        box = TesseractBox(unicode(elements[0]), position, int(elements[5]))
        boxes.append(box)
    return boxes


def _writeBoxFile(fileName, boxes):
    """
    Write boxes in a box file. Output is in the same format as tesseract.
    """
    with open(fileName) as f:
        for box in boxes:
            f.write(str(box) + "\n")


def _image2String(fileName, lang=None, boxes=False):
    '''
    Runs tesseract on the specified image. First, the image is written to disk,
    and then the tesseract command is run on the image. Tesseract's result is
    read, and the temporary files are erased.

    Returns:
        if boxes == False (default): the text as read from the image
        if boxes == True: an array of TesseractBox

    '''

    tempName = _convertname(fileName)
    outputBase = _outputname(fileName)
    _makebmp(fileName, tempName)
        
    (status, errors) = _runTesseract(tempName,
                                     outputBase,
                                     lang=lang,
                                     boxes=boxes)
    if status:
        raise TesseractError(status, errors)

    _delete(tempName)
    for outputFile in glob.iglob(outputBase):
        _delete(outputFile)


def main():
    """
    Main method: allow quick testing of the API
    """
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        try:
            _image2String(filename)
        except IOError:
            sys.stderr.write('ERROR: Could not open file "%s"\n'
                             % filename)
            exit(1)
    elif len(sys.argv) == 4 and sys.argv[1] == '-l':
        lang = sys.argv[2]
        filename = sys.argv[3]
        try:
            image = _image2String(filename,lang=lang)
        except IOError:
            sys.stderr.write('ERROR: Could not open file "%s"\n'
                             % filename)
            exit(1)
    else:
        sys.stderr.write(
            'Usage: python tesseract.py [-l language] input_file\n')
        exit(2)

if __name__ == '__main__':
    main()
