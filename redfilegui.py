
import os
import sys

# this is for python 27, in py 3 this changed to tkinter i believe
import Tkinter as tkm
import ttk as ttkm

import tkFileDialog
import os
import threading
import time


from librf import arkivemanager


#-----------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------- global synced state

#rf_mutex = threading.BoundedSemaphore(value=1)
rf_mutex = threading.RLock()
rf_mutex_next_job = None

# rf_mutex_progress_pct can be a number between 0 and 100 to indicate percentage of current job done
# None to indicate no job is running right now
rf_mutex_progress_pct = None



#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------

# width is in chars
_ENTRY_BOX_DEFAULT_WIDTH = 60

_REPLICA_COUNT_POSSIBLE_VALUES = tuple(range(2,100)) + tuple(range(100, 1040, 10)) + tuple(range(1050, 15100, 100))

# width is in chars
_REPLICA_COUNT_BOX_DEFAULT_WIDTH = 10

_PHYSICAL_LAYOUTS = ("Distributed", "Sequential", "Random")

_BLOCK_SIZES = (256, 512, 1024, 2048, 4096, 8192, 16384, 32768)

_PROGRESS_BAR_UPDATE_PERIOD = 500


def _get_current_version():

    version = None
    try:
        import librf._version as vm
        version = vm.__version__
    except:
        pass

    if not version:
        version = 'unknown'

    return version


def _progress_report_callback(pct_complete=None):
    """ Given a number between 0 and 100, indicating percentage of progress done so far, 
     update the UIs progress state, if pct_complete was not supplied or was None do nothing. """

    #print "_progress_report_callback() called with: " + str(pct_complete)

    global rf_mutex
    global rf_mutex_progress_pct

    if None == pct_complete:
        return

    if not (isinstance(pct_complete, int) or isinstance(pct_complete, float) ):
        return

    if (pct_complete < 0) or (pct_complete > 100):
        return

    rf_mutex.acquire()
    rf_mutex_progress_pct = pct_complete
    rf_mutex.release()



def _worker_thread_entry():

    print "worker thread entry point called. "
    global rf_mutex
    global rf_mutex_next_job
    global rf_mutex_progress_pct

    while True:


        # sleep for some time, argument is in seconds. (0.5 == half a second)
        time.sleep(0.5)

        tmp_job = None

        rf_mutex.acquire()
        tmp_job = rf_mutex_next_job
        rf_mutex_next_job = None
        rf_mutex.release()


        # if tmp_job existed, process this job wait for it to finish (ok to block the worker thread) and then continue
        # if tmp job did not exist continue to the top of the loop right away

        if (tmp_job) and (isinstance(tmp_job, RFJob) ):

            print "worker thread found work"

            # UNPACK the job and call _make_arkive or _xtract_arkive
            if Action.CREATE == tmp_job.action:
                _make_arkive(src_filename=tmp_job.src_filename, out_filename=tmp_job.out_filename,
                             replica_count=tmp_job.replica_count)

            elif Action.XTRACT == tmp_job.action:
                _xtract_arkive(src_filename=tmp_job.src_filename, out_filename=tmp_job.out_filename)





            # wait for librf to finish (that is make or xtract returns)
            rf_mutex.acquire()
            rf_mutex_progress_pct = 100
            rf_mutex.release()



def _make_arkive(src_filename, out_filename, replica_count):
    """ Create a new redundant arkive. """

    print "------------------------------------------------------------------------------------------------------------"
    print "creating arkive, plz standby. "
    print "input file: " + str(src_filename)
    print "output file: " + str(out_filename)
    print "replica count: " + str(replica_count)

    #
    arkiver = arkivemanager.RFArkiver(src_filename=src_filename, replica_count=replica_count,
                                      progress_callback=_progress_report_callback)
    arkiver.redundantize_and_save(out_filename=out_filename)

    print "Done. librf arkiver returned."


def _xtract_arkive(src_filename, out_filename):
    print "------------------------------------------------------------------------------------------------------------"
    print "xtracting arkive, plz standby. "
    print "input file: " + str(src_filename)
    print "output file: " + str(out_filename)

    xtractor = arkivemanager.RFUnarkiver(src_filename=src_filename, progress_callback=_progress_report_callback)
    xtractor.recover_and_save(out_filename=out_filename)

    print "Done. librf xtractor returned."

class RFJob(object):
    """" a struct (as close to it as possible in python) to keep track of a job. """


    def __init__(self, action=None, src_filename=None, out_filename=None, replica_count=None,
                 physical_layout=None, block_size=None):
        super(RFJob, self).__init__()

        # TODO more error checking here, also figure out how to take out asserts in the pyinstaller version
        assert (action == Action.CREATE) or (action == Action.XTRACT)

        self.action = action
        self.src_filename = src_filename
        self.out_filename = out_filename
        self.replica_count = replica_count
        self.physical_layout = physical_layout
        self.block_size = block_size


class Action(object):
    """" Enumerate different modes of operation of the GUI. """

    CREATE = 1
    XTRACT = 2


class RedFileGui(object):

    def __init__(self):

        super(RedFileGui, self).__init__()
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -----------------------------------------------------------------------------------  create the worker thread
        print "main thread will now create the worker thread"
        self.rf_worker_thread = threading.Thread(target=_worker_thread_entry)
        self.rf_worker_thread.daemon = True
        self.rf_worker_thread.start()

        print "main thread has created worker thread successfully and started it."


        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------
        self.version = _get_current_version()
        self.root = tkm.Tk()
        self.root.title('redfile ' + self.version)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)



        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------  choose xtract/create
        action_group = ttkm.LabelFrame(self.root, text="Action")

        # anchor is set to CENTER by default.
        #action_group.pack(padx=10, pady=10, anchor=ttkm.CENTER)
        action_group.grid(row=0, column=0, padx=10, pady=10)

        # w = ttkm.Entry(action_group)
        # w.grid()


        self.action_control_var = tkm.IntVar()
        self.last_action = None

        option1_text = "Recover original data from redundant file."
        option2_text = "Make a redundant file"

        xtract_radio_btn = ttkm.Radiobutton(action_group, text=option1_text, variable=self.action_control_var,
                                            value=Action.XTRACT, command=self.action_changed_callback)
        xtract_radio_btn.pack(anchor=tkm.W)

        create_radio_btn = ttkm.Radiobutton(action_group, text=option2_text, variable=self.action_control_var,
                                            value=Action.CREATE, command=self.action_changed_callback)
        create_radio_btn.pack(anchor=tkm.W)


        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------ file path box

        file_names_group = ttkm.Frame(self.root)
        file_names_group.grid(row=0, column=1, padx=10, pady=10)

        self.source_file_control_var = tkm.StringVar()
        self.output_file_control_var = tkm.StringVar()
        self.autoname_checkbox_control_var = tkm.IntVar()

        src_label = ttkm.Label(file_names_group, text='Source file')
        src_btn = ttkm.Button(file_names_group, text='Browse', command=self.browse_source_file_btn_clicked)
        src_entry = ttkm.Entry(file_names_group, textvariable=self.source_file_control_var, width=_ENTRY_BOX_DEFAULT_WIDTH)


        output_label = ttkm.Label(file_names_group, text='Output file')
        self.browse_output_filename_btn = ttkm.Button(file_names_group, text='Browse', command=self.browse_output_file_btn_clicked)
        autoname_checkbox = ttkm.Checkbutton(file_names_group, var=self.autoname_checkbox_control_var,
                                                text='Auto name output', command=self.autoname_checkbox_clicked)
        self.output_filename_entry = ttkm.Entry(file_names_group, textvariable=self.output_file_control_var, width=_ENTRY_BOX_DEFAULT_WIDTH)


        src_label.grid(row=0, column=0, padx=5, pady=5, sticky=tkm.W)
        src_btn.grid(row=0, column=1, padx=5, pady=5, sticky=tkm.W)
        src_entry.grid(row=1, column=0, padx=5, pady=1, columnspan=3)

        output_label.grid(row=2, column=0, padx=5, pady=(20, 5), sticky=tkm.W)
        self.browse_output_filename_btn.grid(row=2, column=1, padx=5, pady=(20, 5), sticky=tkm.W)
        autoname_checkbox.grid(row=2, column=2, padx=5, pady=(20, 5), sticky=tkm.W)

        self.output_filename_entry.grid(row=3, column=0, padx=5, pady=1, columnspan=3)

        file_names_group.grid_columnconfigure(0, weight=1)
        file_names_group.grid_columnconfigure(1, weight=1)
        file_names_group.grid_columnconfigure(2, weight=5)


        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------- new redfile options box
        hint_color = '#999'
        new_arkive_options_group = ttkm.Frame(self.root)
        new_arkive_options_group.grid(row=1, column=0, padx=10, pady=10)

        # --------- replica count widgets

        # sticky='w' or sticky=tkm.W to make it west aligned with its master
        replica_count_label = ttkm.Label(new_arkive_options_group, text='Replica count')
        self.replica_count_spinbox = tkm.Spinbox(new_arkive_options_group, values= _REPLICA_COUNT_POSSIBLE_VALUES,
                                                  width=_REPLICA_COUNT_BOX_DEFAULT_WIDTH)

        self.replica_count_spinbox.delete(0, tkm.END)
        self.replica_count_spinbox.insert(0, 4)
        self.replica_count_spinbox.configure(state='readonly')

        # u can pass css/html like color to foreground. i.e. #fff is white #ffffff is also white.
        replica_count_desc_label = ttkm.Label(new_arkive_options_group, text='Min: 2, recommended: 4 or more',
                                              foreground=hint_color)

        # --------- physical layout widgets
        phy_layout_desc = ttkm.Label(new_arkive_options_group, text='Default: distributed', foreground=hint_color)
        phy_layout_desc2 = ttkm.Label(new_arkive_options_group, text='Random is not recommended', foreground=hint_color)
        phy_layout = ttkm.Label(new_arkive_options_group, text='Physical layout')
        self.phy_layout_combo = ttkm.Combobox(new_arkive_options_group, values=_PHYSICAL_LAYOUTS)
        self.phy_layout_combo.delete(0, tkm.END)
        self.phy_layout_combo.insert(0, _PHYSICAL_LAYOUTS[0])
        self.phy_layout_combo.configure(state='readonly')

        # --------- block size widgets

        block_size_desc = ttkm.Label(new_arkive_options_group, text='Default: 512 bytes', foreground=hint_color)
        block_size_label = ttkm.Label(new_arkive_options_group, text='Block Size')
        self.block_size_combo = ttkm.Combobox(new_arkive_options_group, values= _BLOCK_SIZES)
        self.block_size_combo.delete(0, tkm.END)
        self.block_size_combo.insert(0, _BLOCK_SIZES[1])



        # --------- position them all
        replica_count_label.grid(row=0, column=0, padx=5, pady=2, sticky=tkm.W)
        self.replica_count_spinbox.grid(row=0, column=1, padx=5, pady=2,  sticky=tkm.W)
        replica_count_desc_label.grid(row=1, column=0, padx=5, pady=2, columnspan=2, sticky=tkm.W)

        phy_layout.grid(row=2, column=0, padx=5, pady=(20, 5), sticky=tkm.W)
        self.phy_layout_combo.grid(row=2, column=1, padx=5, pady=(20, 5))
        phy_layout_desc.grid(row=3, column=0, padx=5, pady=(2, 1), columnspan=2, sticky=tkm.W)
        phy_layout_desc2.grid(row=4, column=0, padx=5, pady=(1, 5), columnspan=2, sticky=tkm.W)

        block_size_label.grid(row=5, column=0, padx=5, pady=5, sticky=tkm.W)
        self.block_size_combo.grid(row=5, column=1, padx=5, pady=5, sticky=tkm.W)
        block_size_desc.grid(row=6, column=0, padx=5, pady=5, columnspan=2, sticky=tkm.W)


        self.replica_count_spinbox.configure(state=tkm.DISABLED)
        self.phy_layout_combo.configure(state=tkm.DISABLED)
        self.block_size_combo.configure(state=tkm.DISABLED)


        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------ go box
        go_group = ttkm.Frame(self.root)
        go_group.grid(row=1, column=1, padx=10, pady=10)

        #ttkm.Label(go_group, text='progress bar coming soon :D')
        self.go_btn = ttkm.Button(go_group, text='Go', command=self.go_btn_clicked)

        self.progress_control_var = tkm.DoubleVar()
        self.progress_bar = ttkm.Progressbar(go_group, orient=tkm.HORIZONTAL, variable=self.progress_control_var,
                                        mode='determinate', maximum=100, length=250)
        self.progress_control_var.set(0)


        self.go_btn.grid(row=0, column=0, padx=5, pady=(5,10) )
        self.progress_bar.grid(row=1, column=0, padx=5, pady=(10,5) )

        # TODO remove this. should be done when some1 clicks go button.
        # or just schedule it to run once every while.
        self.progress_bar.after(ms=_PROGRESS_BAR_UPDATE_PERIOD, func=self.update_progress_bar)




    def update_progress_bar(self):
        """ Update the progress bar. Called by progress bar itself on the main loop to update itself. """

        global rf_mutex
        global rf_mutex_progress_pct

        rf_mutex.acquire()
        temp_progress = rf_mutex_progress_pct
        rf_mutex.release()

        if None == temp_progress:
            self.progress_control_var.set(0)
            self.go_btn.configure(state=tkm.NORMAL)
        else:
            self.progress_control_var.set( temp_progress )
            if 100 == temp_progress:
                self.go_btn.configure(state=tkm.NORMAL)


        # re-schedule another update
        self.progress_bar.after(ms=_PROGRESS_BAR_UPDATE_PERIOD, func=self.update_progress_bar)



    def run_main_loop(self):
        self.root.mainloop()

    def action_changed_callback(self):
        print "action radio button callback called"

        selected_action = self.action_control_var.get()

        if selected_action == Action.XTRACT:
            self.replica_count_spinbox.configure(state=tkm.DISABLED)
            self.phy_layout_combo.configure(state=tkm.DISABLED)
            self.block_size_combo.configure(state=tkm.DISABLED)

        elif selected_action == Action.CREATE:
            self.replica_count_spinbox.configure(state='readonly')
            self.phy_layout_combo.configure(state='readonly')
            self.block_size_combo.configure(state='readonly')


        if (selected_action == Action.XTRACT) and (selected_action != self.last_action):
            print "user switched to xtract"


        if (selected_action == Action.CREATE) and (selected_action != self.last_action):
            print "user switched to create"


        # remember last action.
        self.last_action = selected_action
        if self.autoname_checkbox_control_var.get():
            self._find_unused_output_name_if_possible()

    def go_btn_clicked(self):

        self.go_btn.configure(state=tkm.DISABLED)

        global rf_mutex
        global rf_mutex_next_job
        global rf_mutex_progress_pct

        src_filename = self.source_file_control_var.get()

        if None == self.last_action :

            # TODO maybe show the user why this go click is being ignored (i.e. ask them to choose action)
            print "last action does not exist returning."
            return

        if not os.path.isfile(src_filename):

            print "src file does not exist returning."
            return

        # now figure out the output filename
        output_filename = self.output_file_control_var.get()

        try:
            output_test = open(output_filename, 'w')
            output_test.close()
            os.remove(output_filename)
        except:
            print 'failed to open output filename for writing. '
            return

        if self.last_action == Action.CREATE:

            rc = None
            try:
                rc = int(self.replica_count_spinbox.get())
            except:
                pass

            block_size = None
            try:
                block_size = int(self.block_size_combo.get())
            except:
                pass

            phy_layout = self.phy_layout_combo.get()

            print "adding job to make a new arkive plz standby"
            print "replica count is: " + str(rc)
            print "src filename is: " + str(src_filename)
            print "output filename is: " + str(output_filename)
            print "physical layout is: " + str(self.phy_layout_combo.get())
            print "block size is: " + str(self.block_size_combo.get())
            # _make_arkive(src_filename=src_filename, out_filename=output_filename, replica_count=rc)

            rf_mutex.acquire()
            rf_mutex_next_job = RFJob(action=Action.CREATE, src_filename=src_filename, out_filename=output_filename,
                                      replica_count=rc, block_size=block_size, physical_layout=phy_layout)
            rf_mutex_progress_pct = 0
            rf_mutex.release()

        elif self.last_action == Action.XTRACT:

            print "adding job to recover original data from arkive plz standby"
            print "src filename is: " + str(src_filename)
            print "output filename is: " + str(output_filename)
            #_xtract_arkive(src_filename=src_filename, out_filename=output_filename)

            rf_mutex.acquire()
            rf_mutex_next_job = RFJob(action=Action.XTRACT, src_filename=src_filename, out_filename=output_filename)
            rf_mutex_progress_pct = 0
            rf_mutex.release()







    def browse_source_file_btn_clicked(self):
        user_chosen_filename = tkFileDialog.askopenfilename()
        print "user chosen source filename: " + str(user_chosen_filename)
        self.source_file_control_var.set(user_chosen_filename)
        if self.autoname_checkbox_control_var.get():
            self._find_unused_output_name_if_possible()

    def browse_output_file_btn_clicked(self):
        user_chosen_filename = tkFileDialog.asksaveasfilename()
        print "user chosen output filename: " + str(user_chosen_filename)
        self.output_file_control_var.set(user_chosen_filename)

    def autoname_checkbox_clicked(self):
        """ """
        print "autoname toggled. "
        print "autoname contorl var: " + str(self.autoname_checkbox_control_var.get())

        # TODO scan the dir for existing files and add -1 -2 -21 -2221 if need be.

        if self.autoname_checkbox_control_var.get():
            # autoname on, disable the filename chooser
            self.output_filename_entry.configure(state=tkm.DISABLED)
            self.browse_output_filename_btn.configure(state=tkm.DISABLED)
            self._find_unused_output_name_if_possible()
        else:
            # autoname off, enable the filename chooser
            self.output_filename_entry.configure(state=tkm.NORMAL)
            self.browse_output_filename_btn.configure(state=tkm.NORMAL)


    def _find_unused_output_name_if_possible(self):
        """ Find an unused filename for output if possible and set the corresponding control variable. """

        postfix = ''
        if self.last_action == Action.XTRACT:
            postfix = '.redfile_recovered'
        elif self.last_action == Action.CREATE:
            postfix = '.redfile'
        else:
            print "no action is selected yet. wont try to cmd name output file atm."
            return


        src_filename = self.source_file_control_var.get()
        if not os.path.isfile(src_filename):
            print "src path is not a file. cant generate output name atm."
            return

        candidate_name = src_filename + postfix
        if not os.path.isfile(candidate_name):
            self.output_file_control_var.set(candidate_name)
            return

        for i in range(2, 100):
            candidate_name = src_filename + '-' + str(i) + postfix
            if not os.path.isfile(candidate_name):
                self.output_file_control_var.set(candidate_name)
                return







def _start_gui():

    app = RedFileGui()
    app.run_main_loop()


if __name__ == '__main__':



    _start_gui()



