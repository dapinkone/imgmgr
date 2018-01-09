#!/usr/bin/python3
# copies images given on stdin to folders based on aspect ratio
# renames files to contain previous folder name as part of filename.
# so as not to lose tags/information in the process.
###
# Completed:
#  * Duplicate detection
# TODO:
#  * auto-tagging
#  * walk the dir yourself, instead of using find . |
#     would be much more efficient.
#  * auto-move duplicates to ./duplicates
#  * consolidation of file names prior to move/deletion of dups?
#
from PIL import Image
import os
import sys
import shutil
import concurrent.futures
import dhash
dhash.force_pil()  # force use PIL, not wand/imagemagick


def get_img_res(filepath=None):
    img = Image.open(filepath)
    return(img.size)


def get_dhash(filename):
    # given a filename, return the dhash of the image
    with Image.open(filename) as img:
        # adjust size for senstivity. greater size==more senstivity
        # results of testing for dups on my collection:
        # 215 detected @ s=8; 160@16; 160@32;
        img_dhash = dhash.dhash_int(img, size=16)
        return(img_dhash)


def filter_dirs(filelisting):
    return {x for x in filelisting if not os.path.isdir(x)}


def sort_by_ratio(filelisting):
    for filepath in filelisting:
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
    hash_to_img = dict()
    img_to_hash = dict()
    dup_queue = set()  # record of dups for deletion

    # filter directories out
    filelisting = filter_dirs(filelisting)

    # thread out, get all the heavy image processing done at once
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures_to_data = {
            executor.submit(get_dhash, filename): filename
            for filename in filelisting
        }
        for future in concurrent.futures.as_completed(futures_to_data):
            filename = futures_to_data[future]
            try:
                img_dhash = future.result()
                img_to_hash[filename] = img_dhash
            except Exception as exc:
                print('Exception: {}'.format(exc))

    for filename, img_dhash in img_to_hash.items():
        if img_dhash not in hash_to_img.keys():
            hash_to_img[img_dhash] = filename
        else:
            # we found a duplicate; we want to keep the one which
            # is of higher resolution, so do a comparison.
            dup = None

            res = get_img_res(filename)
            other = hash_to_img[img_dhash]
            other_res = get_img_res(hash_to_img[img_dhash])

            if other_res >= res:
                dup = filename
            else:
                dup = other
                hash_to_img[img_dhash] = filename

            print('Dup: ' + dup)
            dup_queue.add(dup)
    print(len(dup_queue), ' Duplicates detected.')
    return dup_queue


if __name__ == '__main__':
    filelisting = (line.strip() for line in sys.stdin)
    if not os.path.exists('./duplicates'):
        os.mkdir('./duplicates')
    dups = detect_dups(filelisting)
    # sort_by_ratio(filelisting)
