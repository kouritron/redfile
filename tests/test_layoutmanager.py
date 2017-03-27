
# this fixes an issue with PyCharm IDE versions before 2017.1 (apparently 2017.1 fixed it)
from __future__ import absolute_import


import unittest
from rfutil.layoutmanager import *


class TestLayoutManager(unittest.TestCase):

    # This will run once for all tests in this class,
    @classmethod
    def setUpClass(cls):

        super(TestLayoutManager, cls).setUpClass()
        # cls.static_resource = get_some_resource()
        print "---------------------- setUpClass() called"


    @classmethod
    def tearDownClass(cls):
        super(TestLayoutManager, cls).tearDownClass()
        print "---------------------- tearDownClass() called"



    # setUp will run once before every testcase
    def setUp(self):
        pass

    # tearDown will run once after every testcase
    def tearDown(self):
        pass


    def test_1(self):

        print "testing"
        seq_mgr = SequentialLayoutManager()




## TODO: write these tests:
# for loop over 100 packet ids and make sure each page id gets replica count many offsets.
# make sure offsets are never re-used.
# make sure max offset isnt much later than total_size * replica count.
# make sure returned offsets are multiples of frame size (assuming base num was a multiple, otherwise take that out 1st)






if __name__ == '__main__':
    unittest.main()