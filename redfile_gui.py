
import os
import sys

# this is for python 27, in py 3 this changed to tkinter i believe
import Tkinter as tkm
import ttk as ttkm

import tkFileDialog
import os


# width is in chars
_ENTRY_BOX_DEFAULT_WIDTH = 40

_REPLICA_COUNT_POSSIBLE_VALUES = tuple(range(2,100)) + tuple(range(100, 1040, 10)) + tuple(range(1050, 15100, 100))

# width is in chars
_REPLICA_COUNT_BOX_DEFAULT_WIDTH = 10

_PHYSICAL_LAYOUTS = ("Distributed", "Sequential", "Random")

_BLOCK_SIZES = (256, 512, 1024, 2048, 4096, 8192, 16384, 32768)


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



def _make_arkive(src_filename, out_filename, replica_count):
    """ Create a new redundant arkive. """

    from librf import arkivemanager
    print "------------------------------------------------------------------------------------------------------------"
    print "creating arkive, plz standby. "
    print "input file: " + str(src_filename)
    print "output file: " + str(out_filename)
    print "replica count: " + str(replica_count)

    #
    arkiver = arkivemanager.RFArkiver(src_filename=src_filename ,replica_count=replica_count)
    arkiver.redundantize_and_save(out_filename=out_filename)

    print "Done. librf arkiver returned."



class Action(object):
    """" Enumerate different modes of operation of the GUI. """

    CREATE = 1
    XTRACT = 2


class RedFileGui():

    def __init__(self):

        self.version = _get_current_version()
        self.root = tkm.Tk()
        self.root.title('redfile ' + self.version)


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


        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------- new redfile options box
        hint_color = '#999'
        new_arkive_options_group = ttkm.Frame(self.root)
        new_arkive_options_group.grid(row=1, column=0, padx=10, pady=10, sticky=tkm.W)

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
        go_btn = ttkm.Button(go_group, text='Go', command=self.go_btn_clicked)

        self.progress_control_var = tkm.DoubleVar()
        self.progress_bar = ttkm.Progressbar(go_group, orient=tkm.HORIZONTAL, variable=self.progress_control_var,
                                        mode='determinate', maximum=100, length=250)
        self.progress_control_var.set(0)


        go_btn.grid(row=0, column=0, padx=5, pady=(5,10) )
        self.progress_bar.grid(row=1, column=0, padx=5, pady=(10,5) )

        # TODO remove this. should be done when some1 clicks go button.
        self.progress_bar.after(ms=500, func=self.update_progress_bar)




    def update_progress_bar(self):
        """ Update the progress bar. Called by progress bar itself on the main loop to update itself. """

        if self.progress_control_var.get() <= 100:
            #self.progress_control_var.set( self.progress_control_var.get()+1 )
            self.progress_control_var.set( 10 )

        # re-schedule another update
        self.progress_bar.after(ms=500, func=self.update_progress_bar)



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

    def go_btn_clicked(self):

        src_filename = self.source_file_control_var.get()

        if None == self.last_action :

            # TODO maybe show the user why this go click is being ignored (i.e. ask them to choose action)
            print "last action does not exist returning."
            return

        if not os.path.isfile(src_filename):

            print "src file does not exist returning."
            return

        if self.last_action == Action.CREATE:

            rc = None
            try:
                rc = int(self.replica_count_spinbox.get())
            except:
                pass


            # now figure out the output filename
            output_filename = self.output_file_control_var.get()

            try:
                output_test = open(output_filename, 'w')
                output_test.close()
            except:
                print 'failed to open output filename for writing. '
                return


            print "creating new arkive plz standby"
            print "replica count is: " + str(rc)
            print "src filename is: " + str(src_filename)
            print "output filename is: " + str(output_filename)
            print "physical layout is: " + str(self.phy_layout_combo.get())
            print "block size is: " + str(self.block_size_combo.get())
            _make_arkive(src_filename=src_filename, out_filename=output_filename, replica_count=rc)




        if self.last_action == Action.XTRACT:
            print "recovering original data from arkive plz standby"



    def browse_source_file_btn_clicked(self):
        user_chosen_filename = tkFileDialog.askopenfilename()
        print "user chosen source filename: " + str(user_chosen_filename)
        self.source_file_control_var.set(user_chosen_filename)

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

        src_filename = self.source_file_control_var.get()
        if not os.path.isfile(src_filename):
            print "src path is not a file. cant generate output name atm. "
            return

        candidate_name = src_filename + '.redfile'
        if not os.path.isfile(candidate_name):
            self.output_file_control_var.set(candidate_name)
            return

        for i in range(2, 100):
            candidate_name = src_filename + '-' + str(i) + '.redfile'
            if not os.path.isfile(candidate_name):
                self.output_file_control_var.set(candidate_name)
                return







def _start_gui():

    app = RedFileGui()
    app.run_main_loop()


if __name__ == '__main__':



    _start_gui()



