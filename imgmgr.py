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


def get_img_res(filepath=None):
    img = Image.open(filepath)
    return(img.size)


def getdhash(filename):
    # given a filename, return the dhash of the image
    with Image.open(filename) as img:
        # adjust size for senstivity. greater size==more senstivity
        return(dhash.dhash_int(img, size=8))


def sort_by_ratio(filelisting):
    for filepath in filelisting:
        filepath = filepath.strip()
        if os.path.isdir(filepath):
            continue

        try:
            res = get_img_res(filepath)
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
            if desired_dir not in pathdata:
                print('copying {} to {}'.format(filepath, cp_dest))
                shutil.copy2(filepath, cp_dest)
                if os.path.exists(cp_dest):  # success?
                    pass
                    # if success, perhaps os.unlink()?
                    # or perhaps move/compress?
                    # better leave that to user for safety, for now.

        except shutil.SameFileError:
            print(filepath + ' already exists. Continuing...')
            continue
        except PermissionError as e:
            print(filepath + e, file=sys.stderr)
            continue


def detect_dups(filelisting):
    # detect duplicates given a filelisting
    img_lookup = dict()
    dup_queue = set()  # record of dups for deletion

    for filename in filelisting:
        filename = filename.strip()
        if os.path.isdir(filename):
            continue

        img_dhash = getdhash(filename)
        res = get_img_res(filename)

        if img_dhash not in img_lookup.keys():
            img_lookup[img_dhash] = filename
        else:
            # we found a duplicate; we want to keep the one which
            # is of higher resolution, so do a comparison.
            other = img_lookup[img_dhash]
            other_res = get_img_res(img_lookup[img_dhash])
            print('Dup: {} vs {}'.format(filename, other))
            if other_res >= res:
                dup_queue.add(filename)
            else:
                dup_queue.add(other)
                img_lookup[img_dhash] = filename


if __name__ == '__main__':
    filelisting = set(sys.stdin)
    detect_dups(filelisting)
    # sort_by_ratio(filelisting)
