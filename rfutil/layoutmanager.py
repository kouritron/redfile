
# Layout managers figure out the mapping between frames and pages in a redfile arkive.
# f0 refers to the first frame of the .redfile arkive. f1 is the second frame. and so on. here we are talking about
# the first and second frame_size many bytes of the .redfile file on disk.
# pages are the data that we store on these frames. a layout manager may decide that page id == 0 should be stored
# at f32 and f87.
# each layout manager tries to give a mapping with the aim of spreading the replicas in such a way to make them best
# able to survive data corruption.






import abc


class LayoutManager(object):

    def __init__(self, frame_size, replica_count, total_page_count, base_frame_num=0):
        super(LayoutManager, self).__init__()

        assert replica_count >= 2
        assert base_frame_num >= 0
        assert total_page_count > 0

        # frame_size has to be positive, and really in practice has to be greater than 128 at least.
        # for testing its useful to pretend its smaller than 128
        assert frame_size > 4

        self.frame_size = frame_size
        self.replica_count = replica_count
        self.total_page_count = total_page_count
        self.base_frame_num = base_frame_num

    # abstract method must be overridden and implemented by subclasses. otherwise invoking it results in error
    # the abstract method here can have a implementation which is only invokable in the subclass using super().
    @abc.abstractmethod
    def get_page_to_frame_mappings(self, get_offsets_for_pageid):
        pass


    def get_page_to_bytes_mappings(self, pageid):

        frame_nums = self.get_page_to_frame_mappings(pageid=pageid)
        return [(self.frame_size * frame_num) for frame_num in frame_nums]



# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
class SequentialLayoutManager(LayoutManager):

    def get_page_to_frame_mappings(self, pageid):

        assert isinstance(pageid, int), "wrong type of id supplied."

        frame_numbers = []
        for which_replica in range(0, self.replica_count):
            frame_num_from_start =  pageid + (which_replica * self.total_page_count)
            new_frame_num = self.base_frame_num + frame_num_from_start
            frame_numbers.append( new_frame_num )



        return frame_numbers


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
class SequentialInterleavedLayoutManager(LayoutManager):

    def get_page_to_frame_mappings(self, pageid):

        assert isinstance(pageid, int), "wrong type of id supplied."

        frame_numbers = []
        for which_replica in range(0, self.replica_count):
            frame_num_from_start = (pageid * self.replica_count) + which_replica
            new_frame_num = self.base_frame_num + frame_num_from_start
            frame_numbers.append( new_frame_num )

        return frame_numbers

class SequentialInterleavedDistributedBeginningsLayoutManager(LayoutManager):

    def get_page_to_frame_mappings(self, pageid):

        assert isinstance(pageid, int), "wrong type of id supplied."


        frame_numbers = []
        for which_replica in range(0, self.replica_count):

            shift_unit = (self.total_page_count // self.replica_count)
            if 0 == shift_unit:
                # if replica count is greater than total pages, at least shift by a tiny bit
                shift_unit = 1

            shifted_pid = pageid + (shift_unit * which_replica)
            shifted_pid_wrapped = shifted_pid % self.total_page_count

            frame_num_from_start = (shifted_pid_wrapped * self.replica_count) + which_replica
            new_frame_num = self.base_frame_num + frame_num_from_start
            frame_numbers.append( new_frame_num )

        return frame_numbers



def test_1():

    fs = 8
    rc = 4
    tpc = 8
    bfn = 0
    fmt_str = ""


    for col in range(0, rc):
        fmt_str += "{:>12}"

    print "------------------------------------------- sequential  "

    header_items = ["replica" + str(replica) for replica in range(0, rc)]
    print "        " + fmt_str.format(*header_items)

    seq_mgr = SequentialLayoutManager(frame_size=fs, replica_count=rc, total_page_count=tpc, base_frame_num=bfn)
    for pid in range(0, tpc):
        print "page " + str(pid) + "  " + fmt_str.format(*seq_mgr.get_page_to_bytes_mappings(pid))

    print "------------------------------------------- seq interleaved "

    header_items = ["replica" + str(replica) for replica in range(0, rc)]
    print "        " + fmt_str.format(*header_items)

    seq_mgr = SequentialInterleavedLayoutManager(frame_size=fs, replica_count=rc, total_page_count=tpc,
                                                 base_frame_num=bfn)
    for pid in range(0, tpc):
        print "page " + str(pid) + "  " + fmt_str.format(*seq_mgr.get_page_to_bytes_mappings(pid))


    print "------------------------------------------- seq interleaved dist. beginnings"

    header_items = ["replica" + str(replica) for replica in range(0, rc)]
    print "        " + fmt_str.format(*header_items)

    seq_mgr = SequentialInterleavedDistributedBeginningsLayoutManager(frame_size=fs, replica_count=rc,
                                                                      total_page_count=tpc, base_frame_num=bfn)
    for pid in range(0, tpc):
        print "page " + str(pid) + "  " + fmt_str.format(*seq_mgr.get_page_to_bytes_mappings(pid))


def test_2():
    fs = 8
    rc = 2
    tpc = 4
    bfn = 2

    print "------------------------------------------- sequential  "
    seq_mgr = SequentialLayoutManager(frame_size=fs, replica_count=rc, total_page_count=tpc, base_frame_num=bfn)
    for pid in range(0, tpc):
        print seq_mgr.get_page_to_bytes_mappings(pid)

    print "------------------------------------------- seq interleaved "
    seq_mgr = SequentialInterleavedLayoutManager(frame_size=fs, replica_count=rc, total_page_count=tpc, base_frame_num=bfn)
    for pid in range(0, tpc):
        print seq_mgr.get_page_to_bytes_mappings(pid)


if "__main__" == __name__:

    test_1()






