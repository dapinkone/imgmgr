#!/usr/bin/python3
# copies images given on stdin to folders based on aspect ratio
# renames files to contain previous folder name as part of filename.
# so as not to lose tags/information in the process.
###
# TODO:
#  *auto-tagging
#  *duplicate detection
#  *walk the dir yourself, instead of using find . |
#     would be much more efficient.
from PIL import Image
import os
import sys
import shutil
import dhash
dhash.force_pil()  # force use PIL, not wand/imagemagick


def getimgres(filepath=None):
    img = Image.open(filepath)
    return(img.size)


def sortbyratio(filelisting):
    for filepath in filelisting:
        filepath = filepath.strip()
        if os.path.isdir(filepath):
            continue

        try:
            res = getimgres(filepath)
        except OSError:
            print(filepath + ' unknown filetype.', file=sys.stderr)
            continue

        # This loses a lot of precision on purpose.
        # we're looking for fuzzy matching, and it's pretty good.
        aspect = str(res[0]/res[1])[:3]

        # sort files by aspect ratio
        desired_dir = '{}~ aspect ratio'.format(aspect)

        # I'd like to throw the directory that the file is currently
        # in into the new file name, so we don't lose information
        # during the sort if they had any kind of sort prior.
        pathdata = filepath.split(os.path.sep)
        if len(pathdata) > 2 and ('aspect ratio' not in filepath):
            desired_name = '_'.join(pathdata[1:])
        else:
            desired_name = pathdata[-1]

        cp_dest = desired_dir + os.path.sep + desired_name

        if not os.path.exists(desired_dir):
            print(desired_dir + ' does not exist. Creating.')
            os.mkdir(desired_dir)
        if not os.path.isdir(desired_dir):
            raise('OSError', desired_dir + ' is not a directory.')

        try:
            if desired_dir in pathdata:
                # print(filepath + ' already sorted. Skipping...')
                pass
            else:
                print('copying {} to {}'.format(filepath, cp_dest))
                shutil.copy2(filepath, cp_dest)
                # if success, perhaps os.unlink()?
                # better leave that to user for safety, for now.
        except shutil.SameFileError:
            print(filepath + ' already exists. Continuing...')
            continue
        except PermissionError as e:
            print(filepath + e, file=sys.stderr)
            continue


if __name__ == '__main__':
    sortbyratio(sys.stdin)
