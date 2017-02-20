




class CachingReader:
    """disk reader that has its own internal cache to prevent reading one byte at a time
    from disk. While allowing the user to pretend it is reading one byte at a time. """

    # class vars are share among all instances, 4 MB == 4194304 bytes
    _cache_size = 4194304

    def __init__(self, fname):
        self.fname = fname
        self.fhandle = open(fname, "rb")



if __name__ == '__main__':

    print "hello"
