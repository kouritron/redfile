
import os
import sys

# this is for python 27, in py 3 this changed to tkinter i believe
import Tkinter as tkm
import tkFileDialog

from librf import arkivemanager

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
        # ------------------------------------------------------------------------------------------ make the action box
        action_group = tkm.LabelFrame(self.root, text="Action", padx=5, pady=5)

        # anchor is set to CENTER by default.
        #action_group.pack(padx=10, pady=10, anchor=tkm.CENTER)
        action_group.grid(row=0, column=0, padx=10, pady=10)

        # w = tkm.Entry(action_group)
        # w.grid()


        self.action_box_control_var = tkm.IntVar()
        self.last_action = None

        option1_text = "Recover original data from redundant file."
        option2_text = "Make a redundant file"

        xtract_radio_btn = tkm.Radiobutton(action_group, text=option1_text, variable=self.action_box_control_var,
                                           value=Action.XTRACT, command=self.action_changed_callback, padx=5, pady=5)
        xtract_radio_btn.pack(anchor=tkm.W)

        create_radio_btn = tkm.Radiobutton(action_group, text=option2_text, variable=self.action_box_control_var,
                                           value=Action.CREATE,
                                           command=self.action_changed_callback, padx=5, pady=5)
        create_radio_btn.pack(anchor=tkm.W)


        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------ file path box

        file_names_group = tkm.Frame(self.root, padx=5, pady=5)
        file_names_group.grid(row=0, column=1, padx=10, pady=10)

        self.source_file_control_var = tkm.StringVar()
        self.output_file_control_var = tkm.StringVar()

        tkm.Label(file_names_group, text='Source file').grid(row=0, column=0, padx=5, pady=1, sticky=tkm.W)
        tkm.Entry(file_names_group, textvariable=self.source_file_control_var).grid(row=1, column=0, padx=5, pady=1)
        tkm.Button(file_names_group, text='Browse', command=self.browse_source_file_btn_clicked).grid(row=1, column=1, padx=5, pady=1)

        tkm.Label(file_names_group, text='Output file').grid(row=2, column=0, padx=5, pady=1, sticky=tkm.W)
        tkm.Entry(file_names_group, textvariable=self.output_file_control_var).grid(row=3, column=0, padx=5, pady=1)
        tkm.Button(file_names_group, text='Browse', command=self.browse_output_file_btn_clicked).grid(row=3, column=1, padx=5, pady=1)


        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------- new redfile options box

        new_arkive_options_group = tkm.Frame(self.root, padx=5, pady=5)
        new_arkive_options_group.grid(row=1, column=0, padx=10, pady=10, sticky=tkm.W)

        # sticky='w' or sticky=tkm.W to make it west aligned with its master
        tkm.Label(new_arkive_options_group, text='replica count').grid(row=0, column=0, padx=5, pady=5, columnspan=2)
        tkm.Label(new_arkive_options_group, text='inc box here').grid(row=1, column=0, padx=5, pady=5)


        tkm.Label(new_arkive_options_group, text='layout manager').grid(row=2, column=0, padx=5, pady=5)
        tkm.Label(new_arkive_options_group, text='chooser here').grid(row=3, column=0, padx=5, pady=5)



        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------ go box
        go_group = tkm.Frame(self.root, padx=5, pady=5)
        go_group.grid(row=1, column=1, padx=10, pady=10)

        tkm.Button(go_group, text='Go', command=self.go_btn_clicked).grid(row=0, column=0, padx=5, pady=5)
        tkm.Label(go_group, text='progress bar coming soon :D').grid(row=1, column=0, padx=5, pady=5)





    def run_main_loop(self):
        self.root.mainloop()

    def action_changed_callback(self):
        print "action radio button callback called"

        selected_action = self.action_box_control_var.get()



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

        elif self.last_action == Action.XTRACT:
            print "recovering original data from arkive plz standby"



    def browse_source_file_btn_clicked(self):
        user_chosen_filename = tkFileDialog.askopenfilename()
        print "user chosen source filename: " + str(user_chosen_filename)
        self.source_file_control_var.set(user_chosen_filename)

    def browse_output_file_btn_clicked(self):
        user_chosen_filename = tkFileDialog.askopenfilename()
        print "user chosen output filename: " + str(user_chosen_filename)
        self.output_file_control_var.set(user_chosen_filename)


def _start_gui():

    app = RedFileGui()
    app.run_main_loop()


if __name__ == '__main__':



    _start_gui()



