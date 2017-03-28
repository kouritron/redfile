



import os
from librf import arkivemanager


def clean_up_sample_dir(orig_files):

    temp_files = []

    for fname in orig_files:
        temp_files.append(fname + ".redfile")
        temp_files.append(fname + ".redfile.recovered")

    for file in temp_files:
        try:
            os.remove(file)
        except OSError:
            pass




def debug_run1():

    base_dir = "./tests/sample_files/"

    files = []
    files.append(("test1", 2))
    files.append(("test2", 2))
    files.append(("test3", 2))
    files.append(("test4", 2))
    files.append(("test5", 2))
    files.append(("pic1.jpg", 3))
    files.append(("pic2.jpg", 2))
    files.append(("pic3.png", 2))


    for fname, count in files:
        fname_full = base_dir + fname
        ra = arkivemanager.RFArkiver(src_filename=fname_full, replica_count=count)
        ra.redundantize_and_save()
        ru = arkivemanager.RFUnarkiver(src_filename=fname_full + ".redfile")
        ru.recover_and_save()

    #clean_up_sample_dir( [base_dir + fname   for fname, ignore in files ]  )


if __name__ == '__main__':
    debug_run1()