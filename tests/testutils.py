
import hashlib
import os


def get_file_hash(filename):
    """ Return a str obj with the hex representation of the hash fingerprint
    of the file with the given filename. (assuming the file does exist and is readable. exception otherwise) 
    """

    READ_SIZE = 8192 * 4
    srcfile = open(filename, 'rb')
    hash_func = hashlib.sha256()
    buf = srcfile.read(READ_SIZE)
    while len(buf) > 0:
        hash_func.update(buf)
        buf = srcfile.read(READ_SIZE)
    return hash_func.hexdigest()


def make_file_with_random_content(filename, filesz):
    """ Create a binary file on disk filled with random content of filesz many bytes
    with the given filename
    """

    # fout = open(filename, 'wb')
    with open(filename, 'wb') as fout:
        fout.write(os.urandom(filesz))


def find_file_within_this_project(filename):

    # current working directory is either redfile/ or redfile/tests
    # so this is hopefully high enough point to start the search from
    begin_search_root = ".."
    result = None
    # root is a string ( just the prefix of the current directory) (i.e. "/home/u/redfile" )
    # directories a python list of all directories found within the current directory
    # files a python list of all files found within the current directory
    for root, directories, files in os.walk(begin_search_root):
        if filename in files:
            relative_path = os.path.join(root, filename)
            result = os.path.abspath(relative_path)
            print "Found absolute path to be: " + result
            break

    return result