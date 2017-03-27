


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



    def test_no_crazy_range(self):

        # frame size, replica count, total page count, base frame number
        fs = 256
        rc = 4
        tpc = 100
        bfn = 0

        layout_managers = []
        layout_managers.append(SequentialLayoutManager(fs, rc, tpc, bfn))
        layout_managers.append(SequentialInterleavedLayoutManager(fs, rc, tpc, bfn))
        layout_managers.append(SequentialInterleavedDistributedBeginningsLayoutManager(fs, rc, tpc, bfn))

        # every returned should be strictly less than this
        max_offset = (fs * rc * tpc) + (bfn * fs) + 1

        for layout_manager in layout_managers:
            for pid in xrange(0, tpc):
                offsets = layout_manager.get_page_to_bytes_mappings(pid)

                for offset in offsets:
                    self.assertTrue(offset < max_offset)


    def test_enough_distinct_offsets_are_returned(self):

        # frame size, replica count, total page count, base frame number
        fs = 256
        rc = 4
        tpc = 100
        bfn = 0

        layout_managers = []
        layout_managers.append(SequentialLayoutManager(fs, rc, tpc, bfn))
        layout_managers.append(SequentialInterleavedLayoutManager(fs, rc, tpc, bfn))
        layout_managers.append(SequentialInterleavedDistributedBeginningsLayoutManager(fs, rc, tpc, bfn))


        for layout_manager in layout_managers:

            # make sure offsets are not re-used.
            used_offsets = set()

            for pid in xrange(0, tpc):
                offsets = layout_manager.get_page_to_bytes_mappings(pid)

                self.assertTrue( rc == len(offsets), "was expecting replica count many offsets" )

                for offset in offsets:
                    self.assertNotIn(offset, used_offsets, "offset used more than once.")
                    used_offsets.add(offset)



    def test_returned_offsets_are_frame_aligned(self):
        # frame size, replica count, total page count, base frame number
        fs = 256
        rc = 4
        tpc = 100
        bfn = 0

        layout_managers = []
        layout_managers.append(SequentialLayoutManager(fs, rc, tpc, bfn))
        layout_managers.append(SequentialInterleavedLayoutManager(fs, rc, tpc, bfn))
        layout_managers.append(SequentialInterleavedDistributedBeginningsLayoutManager(fs, rc, tpc, bfn))


        for layout_manager in layout_managers:
            for pid in xrange(0, tpc):
                offsets = layout_manager.get_page_to_bytes_mappings(pid)
                for offset in offsets:
                    print offset
                    self.assertTrue(0 == (offset % fs), "offsets are not frame aligned")






if __name__ == '__main__':
    unittest.main()