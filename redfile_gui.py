
import os
import sys

# this is for python 27, in py 3 this changed to tkinter i believe
import Tkinter as tkm
import ttk as ttkm

import tkFileDialog
from librf import arkivemanager

# width is in chars
_ENTRY_BOX_DEFAULT_WIDTH = 40

_REPLICA_COUNT_POSSIBLE_VALUES = tuple(range(2,100)) + tuple(range(100, 1040, 10)) + tuple(range(1050, 15100, 100))

# width is in chars
_REPLICA_COUNT_BOX_DEFAULT_WIDTH = 10


def _get_current_version():

    version = None
    try:
        with open('./Version', 'r') as vf:
            version = vf.readline().strip()
    except:
        pass

    if not version:
        version = 'unknown'

    return version


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

        src_label = ttkm.Label(file_names_group, text='Source file')
        src_btn = ttkm.Button(file_names_group, text='Browse', command=self.browse_source_file_btn_clicked)
        src_entry = ttkm.Entry(file_names_group, textvariable=self.source_file_control_var, width=_ENTRY_BOX_DEFAULT_WIDTH)
        src_label.grid(row=0, column=0, padx=5, pady=5, sticky=tkm.W)
        src_btn.grid(row=0, column=1, padx=5, pady=5, sticky=tkm.W)
        src_entry.grid(row=1, column=0, padx=5, pady=1, columnspan=3)

        output_label = ttkm.Label(file_names_group, text='Output file')
        output_btn = ttkm.Button(file_names_group, text='Browse', command=self.browse_output_file_btn_clicked)
        auto_name_output_btn = ttkm.Button(file_names_group, text='Auto name output', command=self.auto_name_output_btn_clicked)
        output_entry = ttkm.Entry(file_names_group, textvariable=self.output_file_control_var, width=_ENTRY_BOX_DEFAULT_WIDTH)
        output_label.grid(row=2, column=0, padx=5, pady=(20, 5), sticky=tkm.W)
        output_btn.grid(row=2, column=1, padx=5, pady=(20, 5), sticky=tkm.W)
        auto_name_output_btn.grid(row=2, column=2, padx=5, pady=(20, 5), sticky=tkm.W)
        output_entry.grid(row=3, column=0, padx=5, pady=1, columnspan=3)


        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------- new redfile options box

        new_arkive_options_group = ttkm.Frame(self.root)
        new_arkive_options_group.grid(row=1, column=0, padx=10, pady=10, sticky=tkm.W)

        # sticky='w' or sticky=tkm.W to make it west aligned with its master
        replica_count_label = ttkm.Label(new_arkive_options_group, text='replica count')
        self.replica_count_spinbox = tkm.Spinbox(new_arkive_options_group, values= _REPLICA_COUNT_POSSIBLE_VALUES,
                                                  width=_REPLICA_COUNT_BOX_DEFAULT_WIDTH)

        self.replica_count_spinbox.delete(0, tkm.END)
        self.replica_count_spinbox.insert(0, 4)


        # u can pass css/html like color to foreground. i.e. #fff is white #ffffff is also white.
        replica_count_desc_label = ttkm.Label(new_arkive_options_group, text='Min: 2, recommended: 4 or more',
                                              foreground='#999')
        replica_count_label.grid(row=0, column=0, padx=5, pady=2, sticky=tkm.W)
        self.replica_count_spinbox.grid(row=0, column=1, padx=5, pady=2)
        replica_count_desc_label.grid(row=1, column=0, padx=5, pady=2, columnspan=2, sticky=tkm.W)



        ttkm.Label(new_arkive_options_group, text='layout manager').grid(row=2, column=0, padx=5, pady=(20, 5), sticky=tkm.W)
        ttkm.Label(new_arkive_options_group, text='chooser here').grid(row=2, column=1, padx=5, pady=(20, 5))



        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------ go box
        go_group = ttkm.Frame(self.root)
        go_group.grid(row=1, column=1, padx=10, pady=10)

        ttkm.Button(go_group, text='Go', command=self.go_btn_clicked).grid(row=0, column=0, padx=5, pady=5)
        ttkm.Label(go_group, text='progress bar coming soon :D').grid(row=1, column=0, padx=5, pady=5)





    def run_main_loop(self):
        self.root.mainloop()

    def action_changed_callback(self):
        print "action radio button callback called"

        selected_action = self.action_control_var.get()

        if (selected_action == Action.XTRACT) and (selected_action != self.last_action):
            print "user switched to xtract"


        if (selected_action == Action.CREATE) and (selected_action != self.last_action):
            print "user switched to create"



        # remember last action.
        self.last_action = selected_action

    def go_btn_clicked(self):

        if self.last_action is None:
            return

        elif self.last_action == Action.CREATE:
            print "creating new arkive plz standby"
            print "replica count is: " + str(self.replica_count_spinbox.get())


        elif self.last_action == Action.XTRACT:
            print "recovering original data from arkive plz standby"



    def browse_source_file_btn_clicked(self):
        user_chosen_filename = tkFileDialog.askopenfilename()
        print "user chosen source filename: " + str(user_chosen_filename)
        self.source_file_control_var.set(user_chosen_filename)

    def browse_output_file_btn_clicked(self):
        user_chosen_filename = tkFileDialog.asksaveasfilename()
        print "user chosen output filename: " + str(user_chosen_filename)
        self.output_file_control_var.set(user_chosen_filename)

    def auto_name_output_btn_clicked(self):
        """ """
        print "choosing output file name automatically from input"

        # TODO scan the dir for existing files and add -1 -2 -21 -2221 if need be.




def _start_gui():

    app = RedFileGui()
    app.run_main_loop()


if __name__ == '__main__':



    _start_gui()



