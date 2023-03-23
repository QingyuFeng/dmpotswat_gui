# This program runs on a virtualenv.
# Create the virtual environment first and then run the program.

import tkinter
import os
import copy
import pathlib
import threading
import psutil
import pandas
import webbrowser

from tkinter import ttk, filedialog
from tkinter.messagebox import showinfo


from scripts.global_vars import global_vars, default_dmpotconf
from scripts.mod_swatutils import swat_utils
from scripts.mod_graphutils import get_outlet_in_reach
from scripts.mod_dmpotutil import *
from scripts.mod_bgprocess import *

SwatUtil = swat_utils()
GlobalVars = global_vars()

# Pipe must be global
pipe_process_to_gui = multiprocessing.Pipe()

# Setting up environment and import the GDAL lib
path_main_root = os.path.dirname(__file__)
os.environ['PROJ_LIB'] = os.path.join(
    path_main_root,
    "pyenv_dmpotswatgui\Lib\site-packages\pyproj\proj_dir\share\proj")
os.environ['GDAL_DATA'] = os.path.join(
    path_main_root,
    "pyenv_dmpotswatgui\Lib\site-packages\fiona\gdal_data")

class mainWindow(tkinter.Tk):

    def __init__(self):
        super().__init__()

        # Project data is a json structure variable
        # stores all variables related to user
        # project. It will be updated after the user
        # checked the txtinout file as
        self.proj_data = copy.deepcopy(default_dmpotconf)

        self.init_main_window()
        self.create_widgets()

        self.pipe_process_to_gui = multiprocessing.Pipe()
        # self.display_destination: set under which theme the program
        # is running. It will determine the destination of pipe output
        self.display_destination = ""
        # Initiate the daemon thread to wait for displaying the outputs
        self.threadFlushPipeToGui()
        # A class containing all background processes that need to
        # print output into the interface.
        # self.backProcess = backgroundProcesses(self.pipe_process_to_gui[0])

        # A flag to check the status of swat run
        self.flag_swat_run_status = "start"

    def flushPipeToTextbox(self):
        """
        keep receiving data from pipes and display pipe data in the
        target widgets.
        While true means while this thread is true, keep receiving
        and playing.
        We only initiate one pipe and daemon thread to receive the
        pipe output. But there are three tabs giving output:
        single run,
        sensitivity analysis run
        calibration run
        The data will be displayed at corresponding target depends on
        the run condition. This saves the number of threads and
        use one pipe efficiently.
        :return:
        """
        # TODO: To prevent change of display_destination while
        # there is one program running, the condition of
        # sending output need to be updated.
        while True:
            process_info = pipe_process_to_gui[1].recv()
            # process_info = bg_proc_pipe.get(0)
            if self.display_destination == "run_default":
                if process_info == "bgrundone":
                    self.button_run_dftmodel.config(state="normal")
                else:
                    self.textbox_default_output.insert(
                        "end",
                        """{}--{}""".format(current_time(), process_info))
                    self.textbox_default_output.see("end")
            elif self.display_destination == "run_calibration":
                if process_info == "bgrundone":
                    self.button_run_cali.config(state="normal")
                else:
                    self.textbox_cali_output.insert(
                        "end",
                        """{}--{}""".format(current_time(), process_info))
                    self.textbox_cali_output.see("end")
            elif self.display_destination == "run_best":
                if process_info == "bgrundone":
                    self.button_run_best_model.config(state="normal")
                else:
                    self.textbox_best_output.insert(
                        "end",
                        """{}--{}""".format(current_time(), process_info))
                    self.textbox_best_output.see("end")
            elif self.display_destination == "run_best_plot":
                if process_info == "bgrundone":
                    self.button_run_best_plot.config(state="normal")
                else:
                    self.textbox_best_output.insert(
                        "end",
                        """{}--{}""".format(current_time(), process_info))
                    self.textbox_best_output.see("end")
            elif self.display_destination == "run_sa":
                if process_info == "bgrundone":
                    self.button_run_sa.config(state="normal")
                else:
                    self.textbox_sa_output.insert(
                        "end",
                        """{}--{}""".format(current_time(), process_info))
                    self.textbox_sa_output.see("end")
            elif self.display_destination == "run_cali_plot":
                if process_info == "bgrundone":
                    self.button_run_cali_plot.config(state="normal")
                else:
                    self.textbox_plot_output.insert(
                        "end",
                        """{}--{}""".format(current_time(), process_info))
                    self.textbox_plot_output.see("end")
            elif self.display_destination == "run_uncertainty":
                if process_info == "bgrundone":
                    self.button_gene_uncertainty_plot.config(state="normal")
                else:
                    self.textbox_uncertainty_output.insert(
                        "end",
                        """{}--{}""".format(current_time(), process_info))
                    self.textbox_uncertainty_output.see("end")

    def threadFlushPipeToGui(self):
        """
        The funciton initiate an individual thread to avoid
        blocking the main gui. This thread is a daemon thread,
        and will keep alive as long as the main gui is alive.
        When the main gui is killed, this thread is killed.
        Daemon: background processes
        A python thread is a daemon thread, which means if
        its parent thread is end, it is also end.
        setDaemon == True: make a thread daemon thread.
        In order to use daemon thread correctly, you must know
        which thread is its parent thread.
        In this example, the target function is a new daemon thread,
        and it is created under this main.py, thus the main.py
        will be its parent thread.
        If setDaemon is set false, the daemon thread will continue
        even if the main thread is killed.
        :return:
        """
        tread_flushing = threading.Thread(target=self.flushPipeToTextbox)
        tread_flushing.daemon=True
        tread_flushing.start()

    def init_main_window(self):

        # Set window title:
        self.title('dmpotswat')
        # self.overrideredirect(True)
        # self.wm_title("dmpotswat")

        # set icon
        self.iconbitmap(GlobalVars.path_main_icon)

        self.window_width = 1050
        self.window_height = 700

        # get the screen dimension
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        # find the center point
        self.center_x = int(self.screen_width / 2 - self.window_width / 2)
        self.center_y = int(self.screen_height / 2 - self.window_height / 2)

        # set the position of the window to the center of the screen
        self.geometry(f'{self.window_width}x{self.window_height}+{self.center_x}+{self.center_y}')

        # Set the minimum width and size
        self.minsize(self.window_width, self.window_height)
        # set transparency
        # self.attributes('-alpha', 0.5)

        # set the window on top of others
        # master_page.attributes('-topmost', 1)

        # Change title bar background color
        # Make a frame for title bar
        # self.title_bar = tkinter.Frame(self, bg="white", relief="raised", bd=2)

    def create_widgets(self):

        # Add notebook
        self.main_notebook = ttk.Notebook(self, style="TNotebook")
        self.main_notebook.pack(padx=10, pady=10, expand=True, fill="both")

        # Add frames to the notebook
        self.frame_proj_setup_tab = ttk.Frame(self.main_notebook)
        self.frame_swat_info_tab = ttk.Frame(self.main_notebook)
        self.frame_default_run_tab = ttk.Frame(self.main_notebook)
        self.frame_parm_tab = ttk.Frame(self.main_notebook)
        self.frame_sa_tab = ttk.Frame(self.main_notebook)
        self.frame_cali_tab = ttk.Frame(self.main_notebook)
        self.frame_cali_plot_tab = ttk.Frame(self.main_notebook)
        self.frame_best_run_tab = ttk.Frame(self.main_notebook)
        self.frame_uncertainty_tab = ttk.Frame(self.main_notebook)
        self.frame_about_tab = ttk.Frame(self.main_notebook)

        # Display frames on the notebook
        self.frame_proj_setup_tab.pack(fill='both', expand=True)
        self.frame_swat_info_tab.pack(fill='both', expand=True)
        self.frame_default_run_tab.pack(fill='both', expand=True)
        self.frame_parm_tab.pack(fill='both', expand=True)
        self.frame_sa_tab.pack(fill='both', expand=True)
        self.frame_cali_tab.pack(fill='both', expand=True)
        self.frame_best_run_tab.pack(fill='both', expand=True)
        self.frame_cali_plot_tab.pack(fill='both', expand=True)
        self.frame_uncertainty_tab.pack(fill='both', expand=True)
        self.frame_about_tab.pack(fill='both', expand=True)

        # notebook status: normal, hidden, disabled
        self.main_notebook.add(self.frame_proj_setup_tab, text=' Projects ', state='normal')
        self.main_notebook.add(self.frame_swat_info_tab, text=' SWAT Model ', state='disable')
        self.main_notebook.add(self.frame_default_run_tab, text=' Evaluate Default Model ', state='disable')
        self.main_notebook.add(self.frame_parm_tab, text=' Parameter selection ', state='disable')
        self.main_notebook.add(self.frame_sa_tab, text=' Sensitivity Anslysis ', state='disable')
        self.main_notebook.add(self.frame_cali_tab, text=' Calibration ', state='disable')
        self.main_notebook.add(self.frame_cali_plot_tab, text=' Calibration Plotting ', state='disable')
        self.main_notebook.add(self.frame_best_run_tab, text=' Select Best Run ', state='disable')
        self.main_notebook.add(self.frame_uncertainty_tab, text=' Uncertainty ', state='disable')
        self.main_notebook.add(self.frame_about_tab, text=' About ', state='normal')

        # Define frame styles
        self.define_widget_styles()

        # Define project frame
        self.gui_project_setup()

        # Define swatmodel info frame
        self.gui_swat_info()

        # Define swatmodel info frame
        self.gui_default_run()

        # configure parameter tab
        self.gui_parm_select()

        # configure sensitivity analysis gui
        self.gui_sa_run()

        # Configure the calibration gui
        self.gui_cali_run()

        # Configure the single run gui
        self.gui_best_run()

        # Configure the plotting gui
        self.gui_cali_plot()

        # Configure the uncertainty gui
        self.gui_uncertainty()

        # Configure the uncertainty gui
        self.gui_about()

    def define_widget_styles(self):
        """
        Define styles of widgets
        :return:
        """
        self.style_notebook = ttk.Style()
        self.style_notebook.configure("TNotebook", font=('Microsoft YaHei', 12, 'normal'))
        self.style_frame = ttk.Style()
        self.style_frame.configure("TFrame")
        self.style_info_label = ttk.Style()
        self.style_info_label.configure("TLabel", font=('Microsoft YaHei', 12, 'normal'))
        self.style_button = ttk.Style()
        self.style_button.configure('TButton', font=('Microsoft YaHei', 12, 'normal'))
        self.style_checkbutton = ttk.Style()
        self.style_checkbutton.configure('TCheckbutton', font=('Microsoft YaHei', 12, 'normal'))
        self.style_entry = ttk.Style()
        self.style_entry.configure('TEntry', font=('Microsoft YaHei', 12, 'normal'))
        self.style_radiobutton = ttk.Style()
        self.style_radiobutton.configure('TRadiobutton', font=('Microsoft YaHei', 12, 'normal'))

    def gui_project_setup(self):
        """
        Draw the interface for project setup frames
        :return:
        """
        # Configure setup project frame
        self.frame_setup_btns = ttk.Frame(self.frame_proj_setup_tab, style="TFrame")

        # Add buttons to the setup project frame
        self.btn_new_proj = ttk.Button(self.frame_setup_btns,
                                       style="TButton",
                                       text="Create New Project",
                                       command=self.new_proj)
        self.btn_save_proj = ttk.Button(self.frame_setup_btns,
                                        style="TButton",
                                        text="Save Project",
                                        command=self.save_proj)
        self.btn_open_proj = ttk.Button(self.frame_setup_btns,
                                        style="TButton",
                                        text="Open Existing Project",
                                        command=self.open_proj)

        # Configure project check frame
        self.frame_check_proj = ttk.Frame(self.frame_proj_setup_tab, style="TFrame")

        self.input_checked_txtinout = tkinter.StringVar()
        self.input_checked_txtinout.set("false")
        # Add checkbutton to ask users to setup the folder properly
        self.ckbtn_copy_txtinout = ttk.Checkbutton(
            self.frame_check_proj,
            style="TCheckbutton",
            text="""Please copy all files in the \"TxtInOut\" folder to the \"txtinout\" folder under your \"project\" folder""",
            onvalue="true",
            offvalue="false",
            variable=self.input_checked_txtinout,
            state='disabled',
            command=self.is_checked_txtinout)

        # Ask users to put the reach shapefile under the project folder
        self.input_checked_reach = tkinter.StringVar()
        self.input_checked_reach.set("false")
        self.ckbtn_copy_reachshp = ttk.Checkbutton(
            self.frame_check_proj,
            style="TCheckbutton",
            text="""Please copy your reach shapefile to the \"reachshapefile\" folder under your \"project\" folder""",
            onvalue="true",
            offvalue="false",
            variable=self.input_checked_reach,
            state='disabled',
            command=self.is_checked_reachshp)

        # Label information variables
        self.frame_setup_confirm = ttk.Frame(self.frame_proj_setup_tab, style="TFrame")
        self.scrollbar_setup_confirm = ttk.Scrollbar(self.frame_setup_confirm)
        self.textbox_setup_confirm = tkinter.Listbox(self.frame_setup_confirm,
                                                     font=('Microsoft YaHei', 12, 'normal'),
                                                     yscrollcommand=self.scrollbar_setup_confirm.set)
        self.scrollbar_setup_confirm.config(command=self.textbox_setup_confirm.yview)

        self.textbox_setup_confirm.insert("end", "Welcome to use the dmpotswat package!")
        self.textbox_setup_confirm.insert("end", "To get started, please either create a new project,")
        self.textbox_setup_confirm.insert("end", "or open an existing project!")

        # Display widgets on the project frame
        padx_val = 15
        pady_val = 15
        ipadx_val = 5
        ipady_val = 5

        self.frame_setup_btns.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="false", fill="both", side="top")
        self.btn_new_proj.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", side="left")
        self.btn_save_proj.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", side="left")
        self.btn_open_proj.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", side="left")

        self.frame_check_proj.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="both", side="top")
        self.ckbtn_copy_txtinout.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="false", fill="none", side="top", anchor="center")
        self.ckbtn_copy_reachshp.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="false", fill="none", side="top", anchor="center")

        self.frame_setup_confirm.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="both", side="top")
        self.textbox_setup_confirm.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="both", side="left")
        self.scrollbar_setup_confirm.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="false", fill="y", side="right")

    def new_proj(self):
        """
        This new project performs the following actions:
        1. Open a directory
        2. Show the path under the button
        3. Copy the json file into the
        4. Create a project file, containing the default options
        and parameter files to be shown on the gui. The project
        name will be the folder name.
        :return: None
        """

        # Check current status, if still working on a project, ask whether to save
        # the current project and create a new one
        create_new = True
        if self.proj_data["gui_status"]["newproject"] == "True":
            user_save_not = tkinter.messagebox.askyesno(
                "Warning",
                "Do you want to save current project and continue with a new project?")

            if user_save_not == False:
                create_new = False
                return
            else:
                # Call save project data function
                self.save_proj()
                showinfo("Confirmation",
                         "Existing project saved !")
                create_new = True

        if create_new == True:
            # get a directory path by user
            user_proj_path = filedialog.askdirectory(
                initialdir=r""""C:\"""",
                title="Please select a folder for your project:")

            # Assign the project to global variables
            proj_name = os.path.basename(user_proj_path)
            path_proj_file = os.path.join(user_proj_path, "{}.dmp".format(proj_name))

            # Check the project name to be longer than 1 charactor:
            if len(proj_name) <= 1:
                showinfo("Warning",
                         "Please choose a longer name than 1 charactor")
                return

            if os.path.isfile(path_proj_file):
                user_replace_existing = tkinter.messagebox.askyesno("Warning",
                        "Do you want to delete the current project and continue with a new project?")

                if user_replace_existing == False:
                    create_new = False
                    return

            # Create project folder structure
            path_txtinout = os.path.join(user_proj_path, "txtinout")
            if not os.path.isdir(path_txtinout):
                os.mkdir(path_txtinout)

            path_reach = os.path.join(user_proj_path, "reachshapefile")
            if not os.path.isdir(path_reach):
                os.mkdir(path_reach)

            path_observed = os.path.join(user_proj_path, "observeddata")
            if not os.path.isdir(path_observed):
                os.mkdir(path_observed)

            # Folder for running the model
            path_workingdir = os.path.join(user_proj_path, "workingdir")
            if not os.path.isdir(path_workingdir):
                os.mkdir(path_workingdir)

            # Folder for storing output files the model
            path_dds_output = os.path.join(user_proj_path, "outfiles_dds")
            if not os.path.isdir(path_dds_output):
                os.mkdir(path_dds_output)

            # Folder for storing output files the model
            path_output_sa = os.path.join(user_proj_path, "outfiles_sa")
            if not os.path.isdir(path_output_sa):
                os.mkdir(path_output_sa)

            # # Folder for storing output files the model
            # path_output_plots = os.path.join(user_proj_path, "outfiles_ddsplots")
            # if not os.path.isdir(path_output_plots):
            #     os.mkdir(path_output_plots)

            # Update the information in the project.json files
            # Load the project file into json
            # Reset the project data to the default status
            self.proj_data = copy.deepcopy(default_dmpotconf)

            # Update project specific information
            self.proj_data["gui_status"]["proj_path"] = user_proj_path
            self.proj_data["gui_status"]["newproject"] = "true"
            self.proj_data["gui_status"]["projectname"] = proj_name

            # Define gui status
            # Enable the check box for ongoing steps
            self.ckbtn_copy_txtinout.config(state="active")
            self.ckbtn_copy_reachshp.config(state="active")

            # Enable other tabs
            # self.main_notebook.tab(tab_id=1, state="normal")

            # Update the json file information
            # path_proj_file = os.path.join(user_proj_path, "{}.dmp".format(proj_name))
            self.proj_data["gui_status"]["proj_file"] = path_proj_file
            if os.path.isfile(path_proj_file):
                os.remove(path_proj_file)

            # Save it to the project file
            write_pickle_file(self.proj_data, path_proj_file)

            # Reset all input values to update the appearance of the interface
            self.input_checked_txtinout.set("false")
            self.input_checked_reach.set("false")

            # Swat Model Tab specifications
            self.input_copy_observed.set("false")

            # Evaluate default model specifications

            # Parameter selection specifications

            # Sensitivity Analysis

            # Calibration specifications
            self.input_cali_mode.set("dist")
            self.input_dds_initval.set("random")
            self.input_dds_pertub.set("0.2")
            self.input_dds_restart.set("restart")
            self.input_dds_totalno.set("100")

            # Select best run specifications

            # Plotting specifications

            # Uncertainty specifications

            # Display the path in the gui
            self.textbox_setup_confirm.insert("end",
                                              """{}--New project setup successfully!\n""".format(
                                                  current_time()))
            self.textbox_setup_confirm.insert("end",
                                              """{}--Project folder: {}\n""".format(
                                                  current_time(), user_proj_path))

    def save_proj(self):
        """
        saving the status of the gui.
        When saving projects, the status of the gui are determined by
        several properties:
        1. projectname
        2. project json file
        3.
        :return:
        """
        # Update necessary gui status data
        # When saved, new project is set True, and load project is set false
        if self.input_checked_txtinout.get() == "false" or self.input_checked_reach.get() == "false":
            showinfo("Warning", """Please check the txtinout and reachshapefile checkbox to proceed!""")

            return

        self.proj_data["gui_status"]["newproject"] = "true"
        self.proj_data["gui_status"]["loadporject"] = "false"

        # This function will be used multiple times, so, it will include all
        # information to be updated. This will be the opposite direction
        # for initializing gui data, by putting guidata back to project data.
        self.proj_data["gui_status"]["checktxtinout"] = self.input_checked_txtinout.get()
        self.proj_data["gui_status"]["checkreach"] = self.input_checked_reach.get()
        self.proj_data["gui_status"]["saveporject"] = "true"
        # Save project data into files
        write_pickle_file(self.proj_data, self.proj_data["gui_status"]["proj_file"])

        # Display the path in the gui
        self.textbox_setup_confirm.insert("end",
                                          """{}--Projects saved successfully!\n""".format(
                                              current_time()))
        self.textbox_setup_confirm.see("end")
        self.textbox_setup_confirm.insert("end",
                                          """{}--Project file: {}\n""".format(
                                              current_time(),
                                              self.proj_data["gui_status"]["proj_file"]))
        self.textbox_setup_confirm.see("end")

        # Set the title to include the user project name
        self.title('dmpotswat {}.dmp'.format(
            self.proj_data["gui_status"]["projectname"]))

        # Enable the swat model tab
        self.main_notebook.tab(tab_id=1, state="normal")

    def open_proj(self):
        """
        Open existing projects and restore status of the gui.
        :return:
        """

        # Check current status, if still working on a project, ask whether to save
        # the current project and create a new one
        open_existing = True
        if self.proj_data["gui_status"]["newproject"] == "true":
            user_save_not = tkinter.messagebox.askyesno("Warning",
                                                        "Do you want to save current project and continue with a new project?")

            if user_save_not == False:
                open_existing = False
                return
            else:
                # pop save confirmation and open existing
                # This function will be used multiple times, so, it will include all
                # information to be updated. This will be the opposite direction
                # for initializing gui data, by putting guidata back to project data.
                write_pickle_file(
                    self.proj_data,
                    self.proj_data["gui_status"]["proj_file"])
                showinfo("Confirmation", "Existing project saved saved")
                open_existing = True

        if open_existing == True:
            filetypes = (
                ('text files', '*.dmp'),
                ('All files', '*.*')
            )

            path_proj_file = filedialog.askopenfilename(
                title='Open dmpotswat project file, .dmp ',
                initialdir='C:',
                filetypes=filetypes)

            if not os.path.isfile(path_proj_file):
                showinfo("Warning", "Please select a valid project file with suffix of .dmp")
                return
            else:

                # Open the data from pickle
                self.proj_data = read_pickle_file(path_proj_file)
                self.proj_data["gui_status"]["proj_path"] = pathlib.Path(path_proj_file).parent.absolute()
                self.proj_data["gui_status"]["proj_file"] = path_proj_file
                # Reset all input values to update the appearance of the interface
                # Update gui status based on the project progress
                if self.proj_data["gui_status"]["newproject"] == "true":
                    self.ckbtn_copy_txtinout.config(state="active")
                    self.ckbtn_copy_reachshp.config(state="active")

                if self.proj_data["gui_status"]["checktxtinout"] == "true":
                    self.input_checked_txtinout.set("true")
                    # Update the variable values
                    self.input_start_date.set(self.proj_data["cali_options"]["simstartdate"])
                    self.input_end_date.set(self.proj_data["cali_options"]["simenddate"])
                    self.input_warmup.set(str(self.proj_data["cali_options"]["warmupyrs"]))
                    self.input_print_code.set(self.proj_data["cali_options"]["iprint"])

                if self.proj_data["gui_status"]["checkreach"] == "true":
                    self.input_checked_reach.set("true")
                    path_reachshp = os.path.join(self.proj_data["gui_status"]["proj_path"],
                                                 "reachshapefile",
                                                 "reach.shp")
                    # Get the outlet number list from the shapefile
                    self.proj_data["cali_options"]["all_outlets_reach"] = get_outlet_in_reach(path_reachshp)

                    # Enable the swat model tab
                    self.main_notebook.tab(tab_id=1, state="normal")

                if self.proj_data["gui_status"]["copy_observed_data"] == "true":
                    self.input_copy_observed.set("true")

                if self.proj_data["gui_status"]["definebtnclick"] == "true":
                    # Display the table
                    self.input_outlet_var_no.set(self.proj_data["cali_options"]["total_outlet_vars"])
                    # Initialize gui values for outlet details.
                    self.define_outlet_details()
                    for ovid in range(int(self.proj_data["cali_options"]["total_outlet_vars"])):
                        ovkey = "{}".format(ovid)
                        for dtlkey in self.outlet_var_detail[ovkey].keys():
                            self.outlet_var_detail[ovkey][dtlkey].set(
                                self.proj_data["cali_options"]["outlet_details"][ovkey][dtlkey])

                if self.proj_data["gui_status"]["setParm"] == "true":
                    # Initialize the project parameter settings
                    for oneparm in self.input_parms.keys():
                        for colid in self.input_parms[oneparm].keys():
                            self.input_parms[oneparm][colid].set(self.proj_data["parms"][oneparm][colid])

                # Evaluate default model specifications
                if self.proj_data["gui_status"]["set_swat_model"] == "true":
                    # Enable the evaluate default model/parameter
                    # selection/sensitivityanalysis/calibration tab
                    self.main_notebook.tab(tab_id=2, state="normal")
                    self.main_notebook.tab(tab_id=3, state="normal")
                    self.main_notebook.tab(tab_id=4, state="normal")
                    self.main_notebook.tab(tab_id=5, state="normal")
                    self.main_notebook.tab(tab_id=6, state="normal")
                    self.main_notebook.tab(tab_id=7, state="normal")
                    self.main_notebook.tab(tab_id=8, state="normal")

                if self.proj_data["gui_status"]["copy_observed_data"] == "true":
                    self.button_run_dftmodel.configure(state="normal")

                if self.proj_data["gui_status"]["setSA"] == "true":
                    # Initialize the project parameter settings
                    self.input_sa_method.set(self.proj_data["sa_method_parm"]["method"])
                    if self.proj_data["sa_method_parm"]["method"] == "sobol":
                        self.input_sobol_n.set(self.proj_data["sa_method_parm"]["sobol_n"])
                        self.entry_sobol_n.config(state="normal")
                        self.entry_morris_n.config(state="disable")
                        self.entry_fast_n.config(state="disable")
                    elif self.proj_data["sa_method_parm"]["method"] == "morris":
                        self.input_morris_n.set(self.proj_data["sa_method_parm"]["morris_n"])
                        self.entry_sobol_n.config(state="disable")
                        self.entry_morris_n.config(state="normal")
                        self.entry_fast_n.config(state="disable")

                    elif self.proj_data["sa_method_parm"]["method"] == "fast":
                        self.input_fast_n.set(self.proj_data["sa_method_parm"]["fast_n"])
                        self.entry_sobol_n.config(state="disable")
                        self.entry_morris_n.config(state="disable")
                        self.entry_fast_n.config(state="normal")
                    self.button_run_sa.configure(state="normal")

                if self.proj_data["gui_status"]["setCali"] == "true":
                    self.input_cali_mode.set(self.proj_data["cali_options"]["cali_mode"])
                    self.input_dds_pertub.set(self.proj_data["cali_dds"]["pertubfactor"])
                    self.input_dds_totalno.set(self.proj_data["cali_dds"]["totalsimno"])
                    self.input_dds_initval.set(self.proj_data["cali_dds"]["initparaidx"])
                    self.input_dds_restart.set(self.proj_data["cali_dds"]["restartmech"])

                    if self.proj_data["gui_status"]["copy_observed_data"] == "true":
                        self.button_run_cali.configure(state="normal")

                self.proj_data["gui_status"]["loadporject"] = "true"

                # Display the path in the gui
                self.textbox_setup_confirm.insert("end",
                                                  """{}--Existing project loaded successfully!\n""".format(
                                                      current_time(),
                                                      self.proj_data["gui_status"]["proj_file"]))
                self.textbox_setup_confirm.insert("end",
                                                  """{}--Project folder: {}\n""".format(
                                                      current_time(),
                                                      self.proj_data["gui_status"]["proj_path"]))

                # Set the title to include the user project name
                self.proj_data["gui_status"]["projectname"] = os.path.split(path_proj_file)[-1]
                self.title('dmpotswat {}'.format(
                    self.proj_data["gui_status"]["projectname"]))


            # Select best run specifications

            # Plotting specifications

            # Uncertainty specifications

    def is_checked_txtinout(self):
        """
        Check the contents in the txtinout folder
        makesure that file.cio, hru, bsn, sol, gw, exist.
        :return:
        """
        path_txtinout = os.path.join(self.proj_data["gui_status"]["proj_path"],
                                     "txtinout")

        error_msg = []
        content_in_txtinout = []
        path_file_cio = ""

        if self.input_checked_txtinout.get() == "true":
            if not os.path.isdir(path_txtinout):
                showinfo("Warning", """The "txtinout" folder is not in the project folder!""")
                self.proj_data["gui_status"]["checktxtinout"] = "false"
                self.ckbtn_copy_txtinout.set("false")
                return
            else:
                content_in_txtinout = os.listdir(path_txtinout)
                path_file_cio = os.path.join(path_txtinout, "file.cio")
                if len(content_in_txtinout) <= 0:
                    showinfo("Warning","""The "txtinout" folder is empty""")
                    self.proj_data["gui_status"]["checktxtinout"] = "false"
                    self.input_checked_txtinout.set("false")
                    return
                elif not os.path.isfile(path_file_cio):
                    if not os.path.isfile(path_file_cio):
                        showinfo("Warning", """The file.cio file is not in the "txtinout" folder""")
                        self.proj_data["gui_status"]["checktxtinout"] = "false"
                        self.input_checked_txtinout.set("false")
                        return
                else:
                    # Update master progress
                    self.proj_data["gui_status"]["checktxtinout"] = "true"
                    swat_file_cio = SwatUtil.read_file_cio(self.proj_data["gui_status"]["proj_path"])
                    self.proj_data["cali_options"]["simstartdate"] = swat_file_cio["startdate"]
                    self.proj_data["cali_options"]["simenddate"] = swat_file_cio["enddate"]
                    self.proj_data["cali_options"]["warmupyrs"] = str(swat_file_cio["warmup"])
                    self.proj_data["cali_options"]["iprint"] = swat_file_cio["iprint"]

                    # Update the variable values
                    self.input_start_date.set(self.proj_data["cali_options"]["simstartdate"])
                    self.input_end_date.set(self.proj_data["cali_options"]["simenddate"])
                    self.input_warmup.set(str(self.proj_data["cali_options"]["warmupyrs"]))
                    self.input_print_code.set(self.proj_data["cali_options"]["iprint"])

                    # Display the path in the gui
                    self.textbox_setup_confirm.insert("end",
                                                      """{}--The "txtinout" folder is properly setup!\n""".format(
                                                          current_time()))

    def is_checked_reachshp(self):
        """
        Check the contents in the reach folder
        makesure that file.cio, hru, bsn, sol, gw, exist.
        :return:
        """
        path_reachshp = os.path.join(self.proj_data["gui_status"]["proj_path"],
                                     "reachshapefile",
                                     "reach.shp")

        if self.input_checked_reach.get() == "true":
            if not os.path.isfile(path_reachshp):
                self.proj_data["gui_status"]["checkreach"] = "false"
                self.input_checked_reach.set("false")
                showinfo("Warning",
                      """Warning: The reach file is not in the "reachshapefile" folder!""")
                return
            else:
                # Display the path in the gui
                self.textbox_setup_confirm.insert(
                    "end",
                      """{}--The "reachshapefile" folder is properly setup!!\n""".format(
                          current_time()))
                # Update master progress
                self.proj_data["gui_status"]["checkreach"] = "true"

                # Get the outlet number list from the shapefile
                self.proj_data["cali_options"]["all_outlets_reach"] = get_outlet_in_reach(path_reachshp)

    def gui_swat_info(self):
        """
        Draw the interface for project setup frames
        :return:
        """
        # Setup the calibration option page
        # There will be several frames
        self.frame_swat_period = ttk.Frame(self.frame_swat_info_tab, style="TFrame")

        # Add SWAT information
        self.label_datestart = ttk.Label(self.frame_swat_period, text="Simulation start date (mm/dd/yyyy):", style="TLabel")
        self.label_dateend = ttk.Label(self.frame_swat_period, text="End date (mm/dd/yyyy):", style="TLabel")
        self.label_warmup = ttk.Label(self.frame_swat_period, text="Warmup period:", style="TLabel")

        # Get default swat info from the file.cio file
        self.input_start_date = tkinter.StringVar()
        self.input_end_date = tkinter.StringVar()
        self.input_warmup = tkinter.StringVar()

        # Initialize the some values before the project is created
        self.input_start_date.set("{}/{}/{}".format(get_today_date()[1],
                                                    get_today_date()[2],
                                                    get_today_date()[0]))
        self.input_end_date.set("{}/{}/{}".format(get_today_date()[1],
                                                  get_today_date()[2],
                                                  get_today_date()[0]))
        self.input_warmup.set("0")
        self.entry_date_start = ttk.Entry(self.frame_swat_period, width=10, style="TEntry",
                                          textvariable=self.input_start_date,
                                          justify="center")
        self.entry_date_end = ttk.Entry(self.frame_swat_period, width=10, style="TEntry",
                                        textvariable=self.input_end_date,
                                        justify="center")
        self.entry_year_warmup = ttk.Entry(self.frame_swat_period,
                                           width=5, style="TEntry",
                                           textvariable=self.input_warmup,
                                           justify="center")

        padx_val = 2
        pady_val = 2
        ipadx_val = 2
        ipady_val = 1

        # Display swat dates
        self.frame_swat_period.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipady_val, expand=False, fill="none", side="top")
        self.label_datestart.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipady_val, expand=False, fill="none", side="left")
        self.entry_date_start.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                   ipady=ipady_val, expand=False, fill="none", side="left")
        self.label_dateend.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                ipady=ipady_val, expand=False, fill="none", side="left")
        self.entry_date_end.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                 ipady=ipady_val, expand=False, fill="none", side="left")
        self.entry_year_warmup.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipady_val, expand=False, fill="none", side="right")
        self.label_warmup.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                               ipady=ipady_val, expand=False, fill="none", side="right")

        # Setup the print code of the model
        self.frame_freq_outlet = ttk.Frame(self.frame_swat_info_tab, style="TFrame")
        self.label_printcode = ttk.Label(self.frame_freq_outlet, style="TLabel",
                                         text="Time frequency:")

        self.input_print_code = tkinter.StringVar()
        self.radiobtn_pday = ttk.Radiobutton(self.frame_freq_outlet, style="TRadiobutton",
                                             variable=self.input_print_code,
                                             value="daily",
                                             text="Daily")
        self.radiobtn_pmon = ttk.Radiobutton(self.frame_freq_outlet, style="TRadiobutton",
                                             variable=self.input_print_code,
                                             value="monthly",
                                             text="Monthly")
        self.radiobtn_pyr = ttk.Radiobutton(self.frame_freq_outlet, style="TRadiobutton",
                                            variable=self.input_print_code,
                                            value="annual",
                                            text="Annual")
        self.label_outlet_var_no = ttk.Label(self.frame_freq_outlet, style="TLabel",
                                             text="Total No of outlet_variable:")
        self.input_outlet_var_no = tkinter.StringVar()
        self.input_outlet_var_no.set("1")
        self.entry_outlet_var_no = ttk.Entry(self.frame_freq_outlet,
                                             width=5, style="TEntry",
                                             textvariable=self.input_outlet_var_no,
                                             justify="center")

        # Display freq and outlets
        self.frame_freq_outlet.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipadx_val, expand=False, fill="none", side="top")
        self.label_printcode.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipadx_val, expand=False, fill="none", side="left")
        self.radiobtn_pday.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                ipady=ipadx_val, expand=False, fill="none", side="left")
        self.radiobtn_pmon.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                ipady=ipadx_val, expand=False, fill="none", side="left")
        self.radiobtn_pyr.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                               ipady=ipadx_val, expand=False, fill="none", side="left")
        self.entry_outlet_var_no.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                      ipady=ipadx_val, expand=False, fill="none", side="right")
        self.label_outlet_var_no.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                      ipady=ipadx_val, expand=False, fill="none", side="right")

        # Define outlet numbers
        # Configure outlets to be simulated
        self.frame_btns_detail_save = ttk.Frame(
            self.frame_swat_info_tab,
            style="TFrame")
        self.btn_outlet_details = ttk.Button(
            self.frame_btns_detail_save,
            style="TButton",
            text="Define details",
            command=self.define_outlet_details)
        self.btn_save_details = ttk.Button(
            self.frame_btns_detail_save,
            style="TButton",
            text="Save details",
            command=self.save_swat_config)
        self.btn_clear_details = ttk.Button(
            self.frame_btns_detail_save,
            style="TButton",
            text="Clear table",
            command=self.clear_detail_frame)

        self.input_copy_observed = tkinter.StringVar()
        self.input_copy_observed.set("false")
        self.ckbtn_copy_observed = ttk.Checkbutton(
            self.frame_btns_detail_save,
            style="TCheckbutton",
            text="""Please copy observed data to \"observeddata\" folder""",
            onvalue="true",
            offvalue="false",
            variable=self.input_copy_observed,
            state='normal',
            command=self.is_checked_observed)

        # Added Nov 27 by Qingyu Feng to generate split shapefiles
        self.btn_create_subws_shp = ttk.Button(
            self.frame_btns_detail_save,
            style="TButton",
            text="Create Sub-watershed Shp",
            command=self.createSubWatershedShapefile,
            state="disable")
        # Finished Add Nov 27 by Qingyu Feng to generate split shapefiles

        # Display calibration option frame
        self.frame_btns_detail_save.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                         ipady=ipadx_val, expand=False, fill="none", side="top")
        self.btn_outlet_details.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                     ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_save_details.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                   ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_clear_details.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipadx_val, expand=False, fill="none", side="left")
        self.ckbtn_copy_observed.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                      ipady=ipadx_val, expand=False, fill="none", side="left")
        # self.btn_save_options.pack(padx= padx_val, pady = pady_val, ipadx = ipadx_val,
        #                            ipady = ipadx_val, expand=False, fill="none", side="right")

        # Added Nov 27 by Qingyu Feng to generate split shapefiles
        self.btn_create_subws_shp.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                      ipady=ipadx_val, expand=False, fill="none", side="left")
        # Finished Add Nov 27 by Qingyu Feng to generate split shapefiles

        # Configure outlets details
        self.frame_outlet_details = ttk.Frame(self.frame_swat_info_tab, style="TFrame")
        self.frame_outlet_details.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                       ipady=ipadx_val, expand=False, fill="x", side="top")

        # Configure information to show response to users
        self.frame_variablelist = ttk.Frame(self.frame_swat_info_tab, style="TFrame")
        self.frame_variablelist.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                     ipady=ipadx_val, expand=True, fill="x", side="top")

    def clear_detail_frame(self):
        """
        This function clear the outlet detail frame
        :return:
        """
        # Create a frame that can put widgets for all outlets, for
        # Clear the frame before drawing
        for widgets in self.frame_outlet_details.winfo_children():
            widgets.destroy()

        for widgets in self.frame_variablelist.winfo_children():
            widgets.destroy()

        self.proj_data["gui_status"]["definebtnclick"] = "false"


    def define_outlet_details(self):
        """
        This function get the outlet number value and draw a table
        determining the outlet calibration details.
        :return:
        """
        new_olt_var_no = int(self.input_outlet_var_no.get())

        if new_olt_var_no <= 0:
            showinfo("Warning",
                     "Please enter at least 1 outlet for calibration!")
            return
        # Create several widgets for each outlet within self.frame_outlet_details
        # Add a row as label
        elif new_olt_var_no > 15:
            self.clear_detail_frame()
            showinfo("Warning", "Please choose less than 15 outlet variables!")
            return
        else:
            # Update the project data if the user updated the outlet nos
            if self.proj_data["gui_status"]["definebtnclick"] == "true":
                if not self.proj_data["cali_options"]["total_outlet_vars"] == new_olt_var_no:
                    self.proj_data["gui_status"]["definebtnclick"] = "false"
                elif self.proj_data["gui_status"]["loadporject"] == "true":
                    self.proj_data["gui_status"]["definebtnclick"] = "false"
                else:
                    return

            if self.proj_data["gui_status"]["definebtnclick"] == "false":

                self.clear_detail_frame()

                self.proj_data["cali_options"]["total_outlet_vars"] = self.input_outlet_var_no.get()
                self.outlet_var_detail = dict()
                self.frame_detail_rep = dict()
                # Create variables for each item to be connected with the gui
                for ovid in range(int(self.proj_data["cali_options"]["total_outlet_vars"])):
                    ovkey = "{}".format(ovid)
                    self.outlet_var_detail[ovkey] = copy.deepcopy(
                        self.proj_data["outlet_details_template"]["outlet_var"])

                    for dtlkey in self.outlet_var_detail[ovkey].keys():
                        self.outlet_var_detail[ovkey][dtlkey] = tkinter.StringVar()
                        self.outlet_var_detail[ovkey]["orderno"].set("{}".format(ovid + 1))
                        if "weight" in dtlkey:
                            self.outlet_var_detail[ovkey][dtlkey].set("1")
                        elif "select" in dtlkey:
                            self.outlet_var_detail[ovkey][dtlkey].set("0")
                        elif "value" in dtlkey:
                            self.outlet_var_detail[ovkey][dtlkey].set("-999.0")
                        elif dtlkey == "best_obj_dist":
                            self.outlet_var_detail[ovkey][dtlkey].set("10000.0")
                        elif dtlkey == "test_obj_dist":
                            self.outlet_var_detail[ovkey][dtlkey].set("10000.0")

                # Set the define_plot_target to be true to prevent interface conflict.
                self.proj_data["gui_status"]["definebtnclick"] = "true"

                # defining outlet id, variables to be calibrated, outlet weights,
                self.frame_detail_labels = ttk.Frame(self.frame_outlet_details, style="TFrame")
                self.label_order_no = ttk.Label(self.frame_detail_labels, style="TLabel", text="Order No")
                self.label_outlet_id = ttk.Label(self.frame_detail_labels, style="TLabel", text="Outlet ID")
                self.label_outlet_weight = ttk.Label(self.frame_detail_labels, style="TLabel", text="Outlet Weight")
                self.label_variable = ttk.Label(self.frame_detail_labels, style="TLabel", text="Variable")
                self.label_nse_select = ttk.Label(self.frame_detail_labels, style="TLabel", text="Nash Coefficient")
                self.label_nse_weight = ttk.Label(self.frame_detail_labels, style="TLabel", text="Nash Weight")
                self.label_r2_select = ttk.Label(self.frame_detail_labels, style="TLabel", text="R^2")
                self.label_r2_weight = ttk.Label(self.frame_detail_labels, style="TLabel", text="R^2 Weight")
                self.label_pbias_select = ttk.Label(self.frame_detail_labels, style="TLabel", text="PBias")
                self.label_pbias_weight = ttk.Label(self.frame_detail_labels, style="TLabel", text="PBias Weight")
                self.label_mse_select = ttk.Label(self.frame_detail_labels, style="TLabel", text="MSE")
                self.label_mse_weight = ttk.Label(self.frame_detail_labels, style="TLabel", text="MSE Weight")
                self.label_rmse_select = ttk.Label(self.frame_detail_labels, style="TLabel", text="RMSE")
                self.label_rmse_weight = ttk.Label(self.frame_detail_labels, style="TLabel", text="RMSE Weight")

                padx_val = 2
                pady_val = 2
                ipadx_val = 0
                ipady_val = 0

                self.frame_detail_labels.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                              ipady=ipadx_val, expand="false", fill="none", side="left")
                self.label_order_no.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                         ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_outlet_id.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                          ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_variable.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                         ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_outlet_weight.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                              ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_nse_select.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                           ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_nse_weight.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                           ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_r2_select.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                          ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_r2_weight.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                          ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_pbias_select.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                             ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_pbias_weight.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                             ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_mse_select.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                           ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_mse_weight.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                           ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_rmse_select.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                            ipady=ipadx_val, expand="false", fill="none", side="top")
                self.label_rmse_weight.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                            ipady=ipadx_val, expand="false", fill="none", side="top")

                # Create variables for each item to be connected with the gui
                for ovkey in self.outlet_var_detail.keys():
                    # Create a frame to contain the widgets for one outlet variable combination
                    self.frame_detail_rep[ovkey] = dict()
                    self.frame_detail_rep[ovkey]["column_frame"] = ttk.Frame(self.frame_outlet_details, style="TFrame")
                    self.frame_detail_rep[ovkey]["column_frame"].pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                                                      ipady=ipadx_val, expand="false", fill="none",
                                                                      side="left")
                    self.frame_detail_rep[ovkey]["items"] = {}

                    self.frame_detail_rep[ovkey]["items"]["orderno"] = ttk.Label(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        style="TLabel",
                        textvariable=self.outlet_var_detail[ovkey]["orderno"])

                    self.frame_detail_rep[ovkey]["items"]["outletid"] = ttk.Entry(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.outlet_var_detail[ovkey]["outletid"],
                        justify="center")

                    self.frame_detail_rep[ovkey]["items"]["variableid"] = ttk.Entry(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.outlet_var_detail[ovkey]["variableid"],
                        justify="center")

                    self.frame_detail_rep[ovkey]["items"]["varweight"] = ttk.Entry(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.outlet_var_detail[ovkey]["varweight"],
                        justify="center")

                    self.frame_detail_rep[ovkey]["items"]["r2_select"] = ttk.Checkbutton(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        style="TCheckbutton",
                        onvalue="1",
                        offvalue="0",
                        variable=self.outlet_var_detail[ovkey]["r2_select"])

                    self.frame_detail_rep[ovkey]["items"]["r2_weight"] = ttk.Entry(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.outlet_var_detail[ovkey]["r2_weight"],
                        justify="center")

                    self.frame_detail_rep[ovkey]["items"]["nse_select"] = ttk.Checkbutton(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        style="TCheckbutton",
                        onvalue="1",
                        offvalue="0",
                        variable=self.outlet_var_detail[ovkey]["nse_select"])

                    self.frame_detail_rep[ovkey]["items"]["nse_weight"] = ttk.Entry(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.outlet_var_detail[ovkey]["nse_weight"],
                        justify="center")

                    self.frame_detail_rep[ovkey]["items"]["pbias_select"] = ttk.Checkbutton(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        style="TCheckbutton",
                        onvalue="1",
                        offvalue="0",
                        variable=self.outlet_var_detail[ovkey]["pbias_select"])
                    self.frame_detail_rep[ovkey]["items"]["pbias_weight"] = ttk.Entry(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.outlet_var_detail[ovkey]["pbias_weight"],
                        justify="center")

                    self.frame_detail_rep[ovkey]["items"]["mse_select"] = ttk.Checkbutton(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        style="TCheckbutton",
                        onvalue="1",
                        offvalue="0",
                        variable=self.outlet_var_detail[ovkey]["mse_select"])
                    self.frame_detail_rep[ovkey]["items"]["mse_weight"] = ttk.Entry(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.outlet_var_detail[ovkey]["mse_weight"],
                        justify="center")

                    self.frame_detail_rep[ovkey]["items"]["rmse_select"] = ttk.Checkbutton(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        style="TCheckbutton",
                        onvalue="1",
                        offvalue="0",
                        variable=self.outlet_var_detail[ovkey]["rmse_select"])
                    self.frame_detail_rep[ovkey]["items"]["rmse_weight"] = ttk.Entry(
                        self.frame_detail_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.outlet_var_detail[ovkey]["rmse_weight"],
                        justify="center")

                    self.frame_detail_rep[ovkey]["items"]["orderno"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["outletid"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["variableid"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["varweight"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["nse_select"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["nse_weight"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["r2_select"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["r2_weight"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["pbias_select"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["pbias_weight"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["mse_select"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["mse_weight"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["rmse_select"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")
                    self.frame_detail_rep[ovkey]["items"]["rmse_weight"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                        expand="false", fill="none", side="top")

                self.variable_id_names = ["{}-{}".format(vidkey, GlobalVars.pair_varid_obs_header[vidkey])
                                          for vidkey in GlobalVars.pair_varid_obs_header.keys()]

                self.label_variablelist = ttk.Label(
                    self.frame_variablelist, style="TLabel",
                    text="Variable no: {}".format(
                        ",  ".join(self.variable_id_names)),
                    wraplength=890,
                    justify="center")

                self.label_variablelist.pack(
                    padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
                    expand="true", fill="y", side="bottom")



    def save_swat_config(self):
        """
        save the user entered outlet data into the proj data and update the project file
        :return:
        """
        user_outlet_detail = {}
        self.proj_data["cali_options"]["total_outlet_vars"] = self.input_outlet_var_no.get()
        for ovid in range(int(self.proj_data["cali_options"]["total_outlet_vars"])):
            ovkey = "{}".format(ovid)
            user_outlet_detail[ovkey] = {}
            error_stat = 0
            error_outlet = []
            for dtlkey in self.outlet_var_detail[ovkey].keys():
                user_outlet_detail[ovkey][dtlkey] = self.outlet_var_detail[ovkey][dtlkey].get()
                if dtlkey == "outletid":
                    # Check the input information
                    if not user_outlet_detail[ovkey][dtlkey] in self.proj_data["cali_options"]["all_outlets_reach"]:
                        error_outlet.append(user_outlet_detail[ovkey][dtlkey])

                if "select" in dtlkey:
                    if user_outlet_detail[ovkey][dtlkey] == "0" or user_outlet_detail[ovkey][dtlkey] == "":
                        error_stat = error_stat + 1
            if len(error_outlet) > 0:
                showinfo(
                    title='Warning',
                    message="""Outlet no "{}" is not found in the reach shapefile.""".format(
                        ", ".join(error_outlet)))
                break

            elif error_stat == 5:
                showinfo(
                    title='Warning',
                    message="Please select at least one stat for outlet {}".format(
                        user_outlet_detail[ovkey]["outletid"]
                    ))
                break

        self.proj_data["gui_status"]["set_swat_model"] = "true"
        self.proj_data["cali_options"]["outlet_details"] = copy.deepcopy(user_outlet_detail)
        self.proj_data["cali_options"]["simstartdate"] = self.input_start_date.get()
        self.proj_data["cali_options"]["simenddate"] = self.input_end_date.get()
        self.proj_data["cali_options"]["warmupyrs"] = self.input_warmup.get()
        self.proj_data["cali_options"]["iprint"] = self.input_print_code.get()

        write_pickle_file(self.proj_data, self.proj_data["gui_status"]["proj_file"])
        showinfo("Confirmation", "SWAT model specifications saved!")

        self.btn_create_subws_shp.configure(state="normal")

        # Enable the evaluate default model/parameter selection/sensitivityanalysis/calibration tab
        self.main_notebook.tab(tab_id=2, state="normal")
        self.main_notebook.tab(tab_id=3, state="normal")
        self.main_notebook.tab(tab_id=4, state="normal")
        self.main_notebook.tab(tab_id=5, state="normal")
        self.main_notebook.tab(tab_id=6, state="normal")
        self.main_notebook.tab(tab_id=7, state="normal")
        self.main_notebook.tab(tab_id=8, state="normal")


    def createSubWatershedShapefile(self):
        """
        collect the parameters and run sa
        :return:
        """
        # Set the destination of displaying
        # proc.join() is not used since it will suspend the main thread,
        # here, the gui.
        self.btn_create_subws_shp.config(state="disable")
        # self.display_destination = "run_calibration"
        self.proc_run_createshapes = threading.Thread(
            target=runCreateSubwatershedShapefile,
            args=(self.proj_data["cali_options"],
                  self.proj_data["gui_status"]["proj_path"],))

        self.proc_run_createshapes.daemon = True
        self.proc_run_createshapes.start()


    def gui_default_run(self):
        """
        Generate runs to get default statistics
        :return:
        """

        # Row Calibration mode, distributed or lumped
        self.frame_dft_run = ttk.Frame(self.frame_default_run_tab, style="TFrame")

        self.button_run_dftmodel = ttk.Button(self.frame_dft_run,
                                              text="Run Default Model",
                                              command=self.processRunDefaultSWAT)

        padx_val = 2
        pady_val = 5
        ipadx_val = 2
        ipady_val = 2

        # Display calibration mode widgets
        self.frame_dft_run.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                expand="false", fill="x", side="top")
        self.button_run_dftmodel.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                      expand="true", fill="none", side="right")

        # TODO: Add function to read the objective function of all outlets, and display sorted best
        # variables in a tree view. Add a scrollbar for display
        # Also, add calibration and validation options. It will be easier here.
        # TODO: Add button to plot the default results

        # Print output of command in to textbox with scrollbar
        self.frame_default_output = ttk.Frame(self.frame_default_run_tab, style="TFrame")
        self.scrollbar_default_output = ttk.Scrollbar(self.frame_default_output)
        self.textbox_default_output = tkinter.Listbox(self.frame_default_output,
                                                      font=('Microsoft YaHei', 12, 'normal'),
                                                      yscrollcommand=self.scrollbar_default_output.set)
        self.scrollbar_default_output.config(command=self.textbox_default_output.yview)

        self.frame_default_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                       ipady=ipady_val, expand="true", fill="both", side="top")
        self.textbox_default_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                         ipady=ipady_val, expand="true", fill="both", side="left")
        self.scrollbar_default_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                           ipady=ipady_val, expand="false", fill="y", side="right")

    def gui_parm_select(self):
        """
        Generate the parameter panel
        :return:
        """

        # Generate variables to connect input to gui
        self.input_parms = copy.deepcopy(self.proj_data["parms"])

        for oneparm in self.input_parms.keys():
            for colid in self.input_parms[oneparm].keys():
                self.input_parms[oneparm][colid] = tkinter.StringVar()
                self.input_parms[oneparm][colid].set(self.proj_data["parms"][oneparm][colid])

        # Generate a treeview with scrollbar and update values
        self.canvas_parm_list = tkinter.Canvas(
            self.frame_parm_tab
        )
        self.frame_parm_list = ttk.Frame(self.canvas_parm_list)
        self.scrollbar_parm_list = ttk.Scrollbar(self.frame_parm_tab, orient="vertical",
                                                 command=self.canvas_parm_list.yview)
        self.canvas_parm_list.configure(yscrollcommand=self.scrollbar_parm_list.set,
                                        scrollregion=self.canvas_parm_list.bbox("all"))

        padx_val = 2
        pady_val = 0
        ipadx_val = 2
        ipady_val = 0

        self.canvas_parm_list.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
            side="left", expand="true", fill="both")
        self.frame_parm_list.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipadx_val,
            side="top", expand="true", fill="none")
        self.scrollbar_parm_list.pack(side="right", fill="y", expand="false")
        # Binding scrollbar to mouthwheel
        self.canvas_parm_list.bind_all("<MouseWheel>", self.on_mouse_wheel)

        # Defining number of columns
        self.canvas_parm_list.create_window(
            (self.winfo_width() + 100, self.winfo_height() + 1300),
            window=self.frame_parm_list)
        self.frame_parm_list.bind("<Configure>", self.OnFrameConfigure)

        # For flow parm create one frame to store the two buttons
        # Save button save all parameters
        self.frame_parm_row1 = ttk.Frame(self.frame_parm_list)
        self.label_parameter_cols = ttk.Label(self.frame_parm_row1, style="TLabel",
                                              text="Parameter selection")
        self.btn_save_parms = ttk.Button(self.frame_parm_row1, style="TButton",
                                         text="Save Parm Selection",
                                         command=self.save_parm_selection)

        self.frame_parm_row2 = ttk.Frame(self.frame_parm_list)
        self.btn_select_allflow = ttk.Button(self.frame_parm_row2,
                                             style="TButton",
                                             text="Select all Flow Parm",
                                             command=self.select_all_flowparm)
        self.btn_select_allsedi = ttk.Button(self.frame_parm_row2,
                                             style="TButton",
                                             text="Select all Sediment Parm",
                                             command=self.select_all_sediparm)
        self.btn_select_alln = ttk.Button(self.frame_parm_row2,
                                          style="TButton",
                                          text="Select all N Parm",
                                          command=self.select_all_nparm)
        self.btn_select_allp = ttk.Button(self.frame_parm_row2,
                                          style="TButton",
                                          text="Select all P Parm",
                                          command=self.select_all_pparm)

        self.frame_parm_row3 = ttk.Frame(self.frame_parm_list)
        self.btn_deselect_allflow = ttk.Button(self.frame_parm_row3,
                                               style="TButton",
                                               text="Deselect all Flow Parm",
                                               command=self.deselect_all_flowparm)
        self.btn_deselect_allsedi = ttk.Button(self.frame_parm_row3,
                                               style="TButton",
                                               text="Deselect all Sediment Parm",
                                               command=self.deselect_all_sediparm)
        self.btn_deselect_alln = ttk.Button(self.frame_parm_row3,
                                            style="TButton",
                                            text="Deselect all N Parm",
                                            command=self.deselect_all_nparm)
        self.btn_deselect_allp = ttk.Button(self.frame_parm_row3,
                                            style="TButton",
                                            text="Deselect all P Parm",
                                            command=self.deselect_all_pparm)

        self.frame_parm_row1.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipadx_val, expand=False, fill="none", side="top")
        self.label_parameter_cols.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                       ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_save_parms.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                 ipady=ipadx_val, expand=False, fill="none", side="left")

        self.frame_parm_row2.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipadx_val, expand=False, fill="none", side="top")
        self.btn_select_allflow.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                     ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_select_allsedi.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                     ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_select_alln.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_select_allp.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipadx_val, expand=False, fill="none", side="left")

        self.frame_parm_row3.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipadx_val, expand=False, fill="none", side="top")
        self.btn_deselect_allflow.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                       ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_deselect_allsedi.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                       ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_deselect_alln.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipadx_val, expand=False, fill="none", side="left")
        self.btn_deselect_allp.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipadx_val, expand=False, fill="none", side="left")

        # Generate frame for each parameter
        self.frame_allparm = {}
        self.frame_allparm["colnm"] = {}
        self.frame_allparm["colnm"]["colFrame"] = ttk.Frame(self.frame_parm_list, style="TFrame")
        self.frame_allparm["colnm"]["ObjectID"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=5,
            text="ID")
        self.frame_allparm["colnm"]["Symbol"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=15,
            text="Parameter")
        self.frame_allparm["colnm"]["File"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=5,
            text="File")
        self.frame_allparm["colnm"]["Unit"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=15,
            text="Unit")
        self.frame_allparm["colnm"]["InitVal"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=15,
            text="Initial Value")
        self.frame_allparm["colnm"]["selectFlag"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=6,
            text="Select")
        self.frame_allparm["colnm"]["LowerBound"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=7,
            text="Min")
        self.frame_allparm["colnm"]["UpperBound"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=7,
            text="Max")
        # self.frame_allparm["colnm"]["ChangeType"] = ttk.Label(
        #     self.frame_allparm["colnm"]["colFrame"],
        #     style="TLabel",
        #     width=5,
        #     justify = "center",
        #     text="Change")
        self.frame_allparm["colnm"]["ForVariable"] = ttk.Label(
            self.frame_allparm["colnm"]["colFrame"],
            style="TLabel",
            width=10,
            text="Variable")

        for oneparm in self.input_parms.keys():
            self.frame_allparm[oneparm] = {}
            self.frame_allparm[oneparm]["colFrame"] = ttk.Frame(self.frame_parm_list, style="TFrame")

            self.frame_allparm[oneparm]["ObjectID"] = ttk.Label(
                self.frame_allparm[oneparm]["colFrame"],
                style="TLabel",
                width=5,
                textvariable=self.input_parms[oneparm]["ObjectID"])

            self.frame_allparm[oneparm]["Symbol"] = ttk.Label(
                self.frame_allparm[oneparm]["colFrame"],
                style="TLabel",
                width=14,
                textvariable=self.input_parms[oneparm]["Symbol"])

            self.frame_allparm[oneparm]["File"] = ttk.Label(
                self.frame_allparm[oneparm]["colFrame"],
                style="TLabel",
                width=5,
                textvariable=self.input_parms[oneparm]["File"])

            self.frame_allparm[oneparm]["Unit"] = ttk.Label(
                self.frame_allparm[oneparm]["colFrame"],
                style="TLabel",
                width=15,
                textvariable=self.input_parms[oneparm]["Unit"])

            self.frame_allparm[oneparm]["InitVal"] = ttk.Entry(
                self.frame_allparm[oneparm]["colFrame"],
                style="TEntry",
                width=15,
                justify="center",
                textvariable=self.input_parms[oneparm]["InitVal"])

            self.frame_allparm[oneparm]["selectFlag"] = ttk.Checkbutton(
                self.frame_allparm[oneparm]["colFrame"],
                style="TCheckbutton",
                onvalue="1",
                offvalue="0",
                width=6,
                variable=self.input_parms[oneparm]["selectFlag"])

            self.frame_allparm[oneparm]["LowerBound"] = ttk.Entry(
                self.frame_allparm[oneparm]["colFrame"],
                width=7, style="TEntry",
                textvariable=self.input_parms[oneparm]["LowerBound"],
                justify="center")

            self.frame_allparm[oneparm]["UpperBound"] = ttk.Entry(
                self.frame_allparm[oneparm]["colFrame"],
                width=7, style="TEntry",
                textvariable=self.input_parms[oneparm]["UpperBound"],
                justify="center")

            # self.frame_allparm[oneparm]["ChangeType"] = ttk.Label(
            #     self.frame_allparm[oneparm]["colFrame"],
            #     style="TLabel",
            #     width= 10,
            #     justify = "center",
            #     textvariable=self.input_parms[oneparm]["ChangeType"])

            self.frame_allparm[oneparm]["ForVariable"] = ttk.Label(
                self.frame_allparm[oneparm]["colFrame"],
                style="TLabel",
                width=12,
                justify="center",
                textvariable=self.input_parms[oneparm]["ForVariable"])

        # Display these widgets
        widgetlist = ["ObjectID", "Symbol", "File", "Unit", "InitVal", "selectFlag",
                      "LowerBound", "UpperBound", "ForVariable"]
        for fapkey in self.frame_allparm.keys():
            self.frame_allparm[fapkey]["colFrame"].pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                                        ipady=ipadx_val, expand=True, fill="x", side="top")
            # Display subwidgets
            for widgets in widgetlist:
                self.frame_allparm[fapkey][widgets].pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                                         ipady=ipadx_val, expand=True, fill="x", side="left")

    def on_mouse_wheel(self, event):
        """
        response to mouse wheel
        :return:
        """
        self.canvas_parm_list.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def OnFrameConfigure(self, event):
        """
        Reset the scroll region to encompass the inner frame
        :return:
        """
        self.canvas_parm_list.configure(scrollregion=self.canvas_parm_list.bbox("all"))

    def save_parm_selection(self):
        """
        save the user determined parameter selection
        Before saving, check whether required parameters are selected.
        :return:
        """

        user_editable_pro = ["InitVal", "selectFlag", "LowerBound", "UpperBound"]
        for oneparm in self.input_parms.keys():
            for colid in user_editable_pro:
                self.proj_data["parms"][oneparm][colid] = self.input_parms[oneparm][colid].get()

        parm_set_full = pandas.DataFrame.from_dict(self.proj_data["parms"], orient="index")
        # Remove those non selected parameters
        parm_selected = parm_set_full.loc[parm_set_full['selectFlag'] == "1"].copy(deep=True)
        parm_selected_variables = parm_selected["ForVariable"].unique()
        # Get variables selected
        user_variables = []
        outlet_details = self.proj_data["cali_options"]["outlet_details"]
        for oltkey in outlet_details.keys():
            if outlet_details[oltkey]["variableid"] not in user_variables:
                user_variables.append(outlet_details[oltkey]["variableid"])

        # Check whether the selected parameters corresponds to the variables
        for varid in user_variables:
            # 1, for flow
            if varid == "1":
                if "Flow" not in parm_selected_variables:
                    showinfo("Warning",
                             """You would like to calibrate "flow", but parameters for flow were\
                             not selected, please check !""")
                    return
            # 2 for sediment
            elif varid in "2":
                if "Sediment" not in parm_selected_variables:
                    showinfo("Warning",
                             """You would like to calibrate "sediment", but related parameters were\
                             not selected, please check !""")
                    return
            elif varid in ["3", "5", "6", "7", "12"]:
                if "Nitrogen" not in parm_selected_variables:
                    showinfo("Warning",
                             """You would like to calibrate "nitrogen", but related parameters were\
                             not selected, please check !""")
                    return
            elif varid in ["4", "8", "9", "10", "11", "13"]:
                if "Phosphorus" not in parm_selected_variables:
                    showinfo("Warning",
                             """You would like to calibrate "phosphorus", but related parameters were\
                             not selected, please check !""")
                    return

        self.proj_data["gui_status"]["setParm"] = "true"
        # Update the json file information
        write_pickle_file(self.proj_data, self.proj_data["gui_status"]["proj_file"])
        showinfo("Confirmation",
                 "Parameter edits saved!")

    def select_all_flowparm(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        for oneparm in self.proj_data["parms"].keys():
            if self.proj_data["parms"][oneparm]["ForVariable"] == "Flow":
                self.input_parms[oneparm]["selectFlag"].set("1")

    def select_all_sediparm(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        for oneparm in self.proj_data["parms"].keys():
            if self.proj_data["parms"][oneparm]["ForVariable"] == "Sediment":
                self.input_parms[oneparm]["selectFlag"].set("1")

    def select_all_nparm(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        for oneparm in self.proj_data["parms"].keys():
            if self.proj_data["parms"][oneparm]["ForVariable"] == "Nitrogen":
                self.input_parms[oneparm]["selectFlag"].set("1")

    def select_all_pparm(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        for oneparm in self.proj_data["parms"].keys():
            if self.proj_data["parms"][oneparm]["ForVariable"] == "Phosphorus":
                self.input_parms[oneparm]["selectFlag"].set("1")

    def deselect_all_flowparm(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        for oneparm in self.proj_data["parms"].keys():
            if self.proj_data["parms"][oneparm]["ForVariable"] == "Flow":
                self.input_parms[oneparm]["selectFlag"].set("0")

    def deselect_all_sediparm(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        for oneparm in self.proj_data["parms"].keys():
            if self.proj_data["parms"][oneparm]["ForVariable"] == "Sediment":
                self.input_parms[oneparm]["selectFlag"].set("0")

    def deselect_all_nparm(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        for oneparm in self.proj_data["parms"].keys():
            if self.proj_data["parms"][oneparm]["ForVariable"] == "Nitrogen":
                self.input_parms[oneparm]["selectFlag"].set("0")

    def deselect_all_pparm(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        for oneparm in self.proj_data["parms"].keys():
            if self.proj_data["parms"][oneparm]["ForVariable"] == "Phosphorus":
                self.input_parms[oneparm]["selectFlag"].set("0")

    def gui_sa_run(self):
        """
        save the user determined parameter selection , "selectFlag", "ForVariable"
        :return:
        """
        # Create input variables
        # 1 for sobol, 2 for morris, 3 for Fast
        self.input_sa_method = tkinter.StringVar()
        self.input_sa_method.set("sobol")
        # frame_sa_tab
        # There will be 5 rows, method specification,
        # parameter for sobol, morris, and fast, method
        self.frame_sa_method = ttk.Frame(self.frame_sa_tab, style="TFrame")
        self.label_sa_method = ttk.Label(self.frame_sa_method, style="TLabel",
                                         text="Sensitivity analysis method:")
        self.radiobutton_sobol = ttk.Radiobutton(self.frame_sa_method, style="TRadiobutton",
                                                 variable=self.input_sa_method,
                                                 value="sobol",
                                                 text="SOBOL",
                                                 command=self.enable_sa_n)
        self.radiobutton_morris = ttk.Radiobutton(self.frame_sa_method, style="TRadiobutton",
                                                  variable=self.input_sa_method,
                                                  value="morris",
                                                  text="MORRIS",
                                                  command=self.enable_sa_n)
        self.radiobutton_fast = ttk.Radiobutton(self.frame_sa_method, style="TRadiobutton",
                                                variable=self.input_sa_method,
                                                value="fast",
                                                text="FAST",
                                                command=self.enable_sa_n)

        padx_val = 2
        pady_val = 5
        ipadx_val = 2
        ipady_val = 0

        # self.frame_sa_mode.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
        #                           ipady=ipady_val, side="top", expand="false", fill="x")
        # self.label_sa_mode.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
        #                           ipady=ipady_val, side="left", expand="false", fill="both")
        # self.radiobtn_dist_mode_sa.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
        #                             ipady=ipady_val, side="left", expand="false", fill="both")
        # self.radiobtn_lump_mode_sa.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
        #                              ipady=ipady_val, side="left", expand="false", fill="both")

        self.frame_sa_method.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipady_val, side="top", expand="false", fill="x")
        self.label_sa_method.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipady_val, side="left", expand="false", fill="both")
        self.radiobutton_sobol.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipady_val, side="left", expand="false", fill="both")
        self.radiobutton_morris.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                     ipady=ipady_val, side="left", expand="false", fill="both")
        self.radiobutton_fast.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                   ipady=ipady_val, side="left", expand="false", fill="both")

        # Sobol row
        self.frame_sobol_parm = ttk.Frame(self.frame_sa_tab, style="TFrame")
        self.label_sobol_n = ttk.Label(self.frame_sobol_parm, style="TLabel",
                                       text="Sobol sampling number: N = 2^n, for example, 2, 4, 8, 16, 64, etc.")
        self.input_sobol_n = tkinter.StringVar()
        self.input_sobol_n.set("8")
        self.entry_sobol_n = ttk.Entry(self.frame_sobol_parm, width=5, style="TEntry",
                                       textvariable=self.input_sobol_n,
                                       justify="center",
                                       state="normal")
        self.frame_sobol_parm.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                   ipady=ipady_val, side="top", expand="false", fill="x")
        self.label_sobol_n.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                ipady=ipady_val, side="left", expand="false", fill="none")
        self.entry_sobol_n.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                ipady=ipady_val, side="left", expand="false", fill="none")

        # Morris row
        self.frame_morris_parm = ttk.Frame(self.frame_sa_tab, style="TFrame")
        self.label_morris_n = ttk.Label(self.frame_morris_parm, style="TLabel",
                                        text="Morris resamble number, for example, 10, 50, 100, etc.")
        self.input_morris_n = tkinter.StringVar()
        self.input_morris_n.set("20")
        self.entry_morris_n = ttk.Entry(self.frame_morris_parm, width=5, style="TEntry",
                                        textvariable=self.input_morris_n,
                                        justify="center",
                                        state="disable")
        self.frame_morris_parm.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipady_val, side="top", expand="false", fill="x")
        self.label_morris_n.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                 ipady=ipady_val, side="left", expand="false", fill="none")
        self.entry_morris_n.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                 ipady=ipady_val, side="left", expand="false", fill="none")

        # FAST row
        self.frame_fast_parm = ttk.Frame(self.frame_sa_tab, style="TFrame")
        self.label_fast_n = ttk.Label(self.frame_fast_parm, style="TLabel",
                                      text="Fast sampling number, > 4*M^2 (M = 4 by default), for example, > 65, etc.")
        self.input_fast_n = tkinter.StringVar()
        self.input_fast_n.set("70")
        self.entry_fast_n = ttk.Entry(self.frame_fast_parm, width=5, style="TEntry",
                                      textvariable=self.input_fast_n,
                                      justify="center",
                                      state="disable")

        self.frame_fast_parm.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipady_val, side="top", expand="false", fill="x")
        self.label_fast_n.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                               ipady=ipady_val, side="left", expand="false", fill="none")
        self.entry_fast_n.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                               ipady=ipady_val, side="left", expand="false", fill="none")

        # Save and run row
        self.frame_run_sa = ttk.Frame(self.frame_sa_tab, style="TFrame")

        self.label_run_sa = ttk.Label(self.frame_run_sa, style="TLabel",
                                      text="Please save the settings, and then run to start the procedure.")
        self.button_save_sa = ttk.Button(self.frame_run_sa, text="Save SA setting", command=self.save_sa_setting)
        self.button_run_sa = ttk.Button(self.frame_run_sa, text="Run SA", command=self.processRunSensitivityAnalysis,
                                        state="disable")

        self.frame_run_sa.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                               ipady=ipady_val, side="top", expand="false", fill="x")
        self.label_run_sa.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                               ipady=ipady_val, side="left", expand="false", fill="none")
        self.button_save_sa.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                 ipady=ipady_val, side="left", expand="false", fill="none")
        self.button_run_sa.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                ipady=ipady_val, side="left", expand="false", fill="none")

        # Print output of command in to textbox with scrollbar
        self.frame_sa_output = ttk.Frame(self.frame_sa_tab, style="TFrame")
        self.scrollbar_sa_output = ttk.Scrollbar(self.frame_sa_output)
        self.textbox_sa_output = tkinter.Listbox(self.frame_sa_output,
                                                 font=('Microsoft YaHei', 12, 'normal'),
                                                 yscrollcommand=self.scrollbar_sa_output.set)
        self.scrollbar_sa_output.config(command=self.textbox_sa_output.yview)

        self.frame_sa_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                  ipady=ipady_val, expand="true", fill="both", side="top")
        self.textbox_sa_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipady_val, expand="true", fill="both", side="left")
        self.scrollbar_sa_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                      ipady=ipady_val, expand="false", fill="y", side="right")

        # for line in range(100):
        #     self.textbox_sa_output.insert("end", "This is line number " + str(line))

    def enable_sa_n(self):
        """
        change state of sample number entry
        :return:
        """
        if self.input_sa_method.get() == "sobol":
            self.entry_sobol_n.configure(state="normal")
            self.entry_morris_n.configure(state="disable")
            self.entry_fast_n.configure(state="disable")
        elif self.input_sa_method.get() == "morris":
            self.entry_sobol_n.configure(state="disable")
            self.entry_morris_n.configure(state="normal")
            self.entry_fast_n.configure(state="disable")
        elif self.input_sa_method.get() == "fast":
            self.entry_sobol_n.configure(state="disable")
            self.entry_morris_n.configure(state="disable")
            self.entry_fast_n.configure(state="normal")

    def save_sa_setting(self):
        """
        save the user selected parameters for SA and udpate the proj_data
        :return:
        """
        # self.proj_data["sa_method_parm"]["sa_mode"] = self.input_sa_mode.get()
        self.proj_data["sa_method_parm"]["method"] = self.input_sa_method.get()
        if self.input_sa_method.get() == "sobol":
            self.proj_data["sa_method_parm"]["sobol_n"] = self.input_sobol_n.get()
        elif self.input_sa_method.get() == "morris":
            self.proj_data["sa_method_parm"]["morris_n"] = self.input_morris_n.get()
        elif self.input_sa_method.get() == "fast":
            self.proj_data["sa_method_parm"]["fast_n"] = self.input_fast_n.get()

        # Enable the run button
        self.button_run_sa.configure(state="normal")

        # Set the setSA to true
        self.proj_data["gui_status"]["setSA"] = "true"

        # Update the json file information
        write_pickle_file(self.proj_data, self.proj_data["gui_status"]["proj_file"])
        self.textbox_sa_output.insert("end",
                                      """{}--Confirmation: Sensitivity analysis setting saved!\n""".format(
                                          current_time()))

    def gui_cali_run(self):
        """
        Develop the calibration gui
        main frame: frame_cali_tab
        :return:
        """
        # # Configure DDS options
        # Row Calibration mode, distributed or lumped
        self.frame_cal_mode = ttk.Frame(self.frame_cali_tab, style="TFrame")
        self.label_cali_mod = ttk.Label(self.frame_cal_mode, style="TLabel",
                                        text="Calibration mode:")
        self.input_cali_mode = tkinter.StringVar()
        self.input_cali_mode.set(self.proj_data["cali_options"]["cali_mode"])
        self.radiobtn_dist_mode = ttk.Radiobutton(self.frame_cal_mode, style="TRadiobutton",
                                                  variable=self.input_cali_mode,
                                                  value="dist",
                                                  text="Distributed")
        self.radiobtn_lump_mode = ttk.Radiobutton(self.frame_cal_mode, style="TRadiobutton",
                                                  variable=self.input_cali_mode,
                                                  value="lump",
                                                  text="Lumped ")

        self.label_dds_initval = ttk.Label(self.frame_cal_mode, style="TLabel",
                                           text="Initial parameter values:")
        self.input_dds_initval = tkinter.StringVar()
        self.input_dds_initval.set(self.proj_data["cali_dds"]["initparaidx"])
        self.radiobtn_random_initval = ttk.Radiobutton(self.frame_cal_mode, style="TRadiobutton",
                                                       variable=self.input_dds_initval,
                                                       value="random", text="Random")
        self.radiobtn_default_initval = ttk.Radiobutton(self.frame_cal_mode, style="TRadiobutton",
                                                        variable=self.input_dds_initval,
                                                        value="initial", text="Initial")

        padx_val = 2
        pady_val = 3
        ipadx_val = 2
        ipady_val = 1

        # Display calibration mode widgets
        self.frame_cal_mode.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="false", fill="x", side="top")
        self.label_cali_mod.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                 expand="false", fill="none", side="left")
        self.radiobtn_dist_mode.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                     expand="false", fill="none", side="left")
        self.radiobtn_lump_mode.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                     expand="false", fill="none", side="left")

        self.radiobtn_default_initval.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="right")
        self.radiobtn_random_initval.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="right")
        self.label_dds_initval.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="right")

        # Row pertubation factor
        self.frame_dds_detail = ttk.Frame(self.frame_cali_tab, style="TFrame")
        self.label_dds_pertub = ttk.Label(self.frame_dds_detail, style="TLabel",
                                          text="Pertubation factor:")
        self.input_dds_pertub = tkinter.StringVar()
        self.input_dds_pertub.set(self.proj_data["cali_dds"]["pertubfactor"])
        self.entry_dds_pertub = ttk.Entry(self.frame_dds_detail, width=5, style="TEntry",
                                          textvariable=self.input_dds_pertub,
                                          justify="center",
                                          state="normal")

        self.label_dds_totalno = ttk.Label(self.frame_dds_detail, style="TLabel",
                                           text="Total iterations:")
        self.input_dds_totalno = tkinter.StringVar()
        self.input_dds_totalno.set(self.proj_data["cali_dds"]["totalsimno"])
        self.entry_dds_totalno = ttk.Entry(self.frame_dds_detail, width=5, style="TEntry",
                                           textvariable=self.input_dds_totalno,
                                           justify="center",
                                           state="normal")

        # Row restart
        self.label_dds_restart = ttk.Label(self.frame_dds_detail, style="TLabel",
                                           text="Restart mode:")
        self.input_dds_restart = tkinter.StringVar()
        self.input_dds_restart.set(self.proj_data["cali_dds"]["restartmech"])
        self.radiobtn_random_restart = ttk.Radiobutton(self.frame_dds_detail, style="TRadiobutton",
                                                       variable=self.input_dds_restart,
                                                       value="restart", text="New run")
        self.radiobtn_default_restart = ttk.Radiobutton(self.frame_dds_detail, style="TRadiobutton",
                                                        variable=self.input_dds_restart,
                                                        value="continue", text="Continue")

        # Display widgets
        self.frame_dds_detail.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="false", fill="x", side="top")
        self.label_dds_pertub.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="false", fill="none", side="left")
        self.entry_dds_pertub.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="false", fill="none", side="left")

        self.label_dds_totalno.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="false", fill="none", side="left")
        self.entry_dds_totalno.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="false", fill="none", side="left")

        self.radiobtn_default_restart.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="right")
        self.radiobtn_random_restart.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="right")
        self.label_dds_restart.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="right")

        # Row Soft data
        self.frame_dds_softdata = ttk.Frame(self.frame_cali_tab, style="TFrame")
        self.frame_softdata_label = ttk.Frame(self.frame_dds_softdata, style="TFrame")
        self.label_softdata_name = ttk.Label(
            self.frame_softdata_label, style="TLabel", text="Constraints", justify="center")
        self.label_softdata_check = ttk.Label(
            self.frame_softdata_label, style="TLabel", text="Select", justify="center")
        self.label_softdata_lower = ttk.Label(
            self.frame_softdata_label, style="TLabel", text="Min", justify="center")
        self.label_softdata_upper = ttk.Label(
            self.frame_softdata_label, style="TLabel", text="Max", justify="center")

        self.frame_dds_softdata.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="x", side="top")
        self.frame_softdata_label.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="left")
        self.label_softdata_name.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="top")
        self.label_softdata_check.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="top")
        self.label_softdata_lower.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="top")
        self.label_softdata_upper.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand=False, fill="none", side="top")

        self.input_softdata = copy.deepcopy(self.proj_data["soft_data"])
        self.frame_soft_varcol = {}

        for sfkey in self.input_softdata.keys():
            self.frame_soft_varcol[sfkey] = {}
            for sfvar in self.input_softdata[sfkey].keys():
                self.input_softdata[sfkey][sfvar] = tkinter.StringVar()
                self.input_softdata[sfkey][sfvar].set(self.proj_data["soft_data"][sfkey][sfvar])
            self.frame_soft_varcol[sfkey]["colFrame"] = ttk.Frame(self.frame_dds_softdata, style="TFrame")
            self.frame_soft_varcol[sfkey]["label"] = ttk.Label(
                self.frame_soft_varcol[sfkey]["colFrame"],
                style="TLabel",
                text=sfkey)

            self.frame_soft_varcol[sfkey]["select"] = ttk.Checkbutton(
                self.frame_soft_varcol[sfkey]["colFrame"],
                style="TCheckbutton",
                onvalue="checked",
                offvalue="unchecked",
                variable=self.input_softdata[sfkey]["select"],
                state="disable")

            self.frame_soft_varcol[sfkey]["lower"] = ttk.Entry(
                self.frame_soft_varcol[sfkey]["colFrame"],
                width=5, style="TEntry",
                textvariable=self.input_softdata[sfkey]["lower"],
                justify="center",
                state="disable")

            self.frame_soft_varcol[sfkey]["upper"] = ttk.Entry(
                self.frame_soft_varcol[sfkey]["colFrame"],
                width=5, style="TEntry",
                textvariable=self.input_softdata[sfkey]["upper"],
                justify="center",
                state="disable")

            self.frame_soft_varcol[sfkey]["colFrame"].pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val,
                                                           pady=pady_val,
                                                           expand=False, fill="none", side="left")
            self.frame_soft_varcol[sfkey]["label"].pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                                        expand=False, fill="none", side="top")
            self.frame_soft_varcol[sfkey]["select"].pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                                         expand=False, fill="none", side="top")
            self.frame_soft_varcol[sfkey]["lower"].pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                                        expand=False, fill="none", side="top")
            self.frame_soft_varcol[sfkey]["upper"].pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                                        expand=False, fill="none", side="top")

        # Row measurement uncertainty
        # TODO: Add measurement uncertainty

        # Row run
        self.frame_run_cali = ttk.Frame(self.frame_cali_tab, style="TFrame")

        self.button_save_cali = ttk.Button(self.frame_run_cali, text="Save Calibration setting",
                                           command=self.save_cali_setting)


        self.button_run_cali = ttk.Button(self.frame_run_cali, text="Run Calibration",
                                          command=self.processRunCalibration, state="disable")

        # Display widgets
        self.frame_run_cali.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                 expand=False, fill="x", side="top")
        # self.label_no_multicores.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady = pady_val,
        #                            expand=False, fill="none", side="left")
        # self.entry_no_multicores.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
        #                               expand=False, fill="none", side="left")
        self.button_save_cali.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                   expand="true", fill="none", side="left")

        self.button_run_cali.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                  expand="true", fill="none", side="left")

        # Print output of command in to textbox with scrollbar
        self.frame_cali_output = ttk.Frame(self.frame_cali_tab, style="TFrame")
        self.scrollbar_cali_output = ttk.Scrollbar(self.frame_cali_output)
        self.textbox_cali_output = tkinter.Listbox(self.frame_cali_output,
                                                   font=('Microsoft YaHei', 12, 'normal'),
                                                   yscrollcommand=self.scrollbar_cali_output.set)
        self.scrollbar_cali_output.config(command=self.textbox_cali_output.yview)

        self.frame_cali_output.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                    expand="true", fill="both", side="top")
        self.textbox_cali_output.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                      expand="true", fill="both", side="left")
        self.scrollbar_cali_output.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                        expand="false", fill="y", side="right")

    def save_cali_setting(self):
        """
        save the user selected parameters for SA and udpate the proj_data
        :return:
        """
        if self.input_copy_observed.get() == "false":
            showinfo("Warning",
                     """Please copy the observed data into the \"observeddata\" folder !""")
            return

        else:
            self.proj_data["cali_options"]["cali_mode"] = self.input_cali_mode.get()
            self.proj_data["cali_dds"]["pertubfactor"] = self.input_dds_pertub.get()
            self.proj_data["cali_dds"]["totalsimno"] = self.input_dds_totalno.get()
            self.proj_data["cali_dds"]["initparaidx"] = self.input_dds_initval.get()
            self.proj_data["cali_dds"]["restartmech"] = self.input_dds_restart.get()

            self.proj_data["gui_status"]["setCali"] = "true"

            for sfkey in self.proj_data["soft_data"].keys():
                for sfvar in self.input_softdata[sfkey].keys():
                    self.proj_data["soft_data"][sfkey][sfvar] = self.input_softdata[sfkey][sfvar].get()

            # Update the json file information
            write_pickle_file(self.proj_data, self.proj_data["gui_status"]["proj_file"])
            # Add the confirmation to the information box
            self.textbox_cali_output.insert("end",
                                            """{}--Confirmation:　Calibration setting saved!""".format(
                                                current_time()))
            # Enable the run button
            if self.proj_data["gui_status"]["copy_observed_data"] == "false":
                self.button_run_cali.configure(state="disable")
                showinfo("Warning",
                         """Please remember to check the \" Please copy observed data \" checkbox in the SWAT model tab""")
                return
            elif self.proj_data["gui_status"]["copy_observed_data"] == "true":
                self.button_run_cali.configure(state="normal")


    def is_checked_observed(self):
        """
        Check whether the observed value is put properly into the folder
        :return:
        """
        outlet_nos = []

        if self.input_copy_observed.get() == "true":
            if self.proj_data["cali_options"]["outlet_details"] == "dummy":
                self.input_copy_observed.set("false")
                showinfo("Warning",
                         "Please specify the outlet details first before check this option!")
                return
            else:
                for oltkeys in self.proj_data["cali_options"]["outlet_details"].keys():
                    outlet_nos.append(self.proj_data["cali_options"]["outlet_details"][oltkeys]["outletid"])

                # Check the existence of observed data for each variable
                # 0: monthly, 1: daily, 2: annual
                freq = ""
                if self.proj_data["cali_options"]["iprint"] == "monthly":
                    freq = "monthly"
                elif self.proj_data["cali_options"]["iprint"] == "daily":
                    freq = "daily"
                elif self.proj_data["cali_options"]["iprint"] == "annual":
                    freq = "annual"

                # print(self.proj_data["cali_options"]["outlet_details"])
                checked_outlet_no = []
                for odkey, odvalue in self.proj_data["cali_options"]["outlet_details"].items():
                    ck_outlet_id = odvalue["outletid"]
                    ck_variableid = odvalue["variableid"]
                    fn_observed = "obs_{}{}.prn".format(freq, ck_outlet_id)
                    path_observed = os.path.join(self.proj_data["gui_status"]["proj_path"],
                                             "observeddata",
                                             fn_observed)

                    if not os.path.isfile(path_observed):
                        self.input_copy_observed.set("false")
                        showinfo("Warning",
                                 "Observed data for outlet {} does not exist".format(path_observed))
                        return
                    else:
                        # Read the observed data and check the length of observed data
                        dataframe_observed = pandas.read_table(
                            path_observed,
                            names=GlobalVars.obs_data_header,
                            skiprows=1)
                        # Get the interested columns from the whole data frame
                        var_col_names = GlobalVars.pair_varid_obs_header[ck_variableid]
                        obs_list = dataframe_observed[var_col_names].to_list()
                        obs_no_missing = []

                        # Get the no missing list
                        for obsidx in range(len(obs_list)):
                            obs_val = obs_list[obsidx]
                            if not int(obs_val) == -99:
                                obs_no_missing.append(obs_val)
                        if len(obs_no_missing) < len(obs_list)/2:
                            self.input_copy_observed.set("false")
                            showinfo("Warning",
                                     "Variable values for variable {} in {} has over 50% missing values. Please double check!".format(
                                         var_col_names, fn_observed))
                            return
                        else:
                            showinfo("Confirmation",
                                     """{}--File {} exists in the \"observeddata\" folder !\n""".format(
                                         current_time(), fn_observed))

                # for oltid in outlet_nos:
                #     fn_observed = "obs_{}{}.prn".format(freq, oltid)
                #     path_observed = os.path.join(self.proj_data["gui_status"]["proj_path"],
                #                                  "observeddata",
                #                                  fn_observed)
                #     if not os.path.isfile(path_observed):
                #         self.input_copy_observed.set("false")
                #         showinfo("Warning",
                #                  "Observed data for outlet {} does not exist".format(path_observed))
                #         return
                #     else:
                #         showinfo("Confirmation",
                #                  """{}--File {} exists in the \"observeddata\" folder !\n""".format(
                #                      current_time(), fn_observed))

                self.proj_data["gui_status"]["copy_observed_data"] = "true"
                # enable the running default model button
                self.button_run_dftmodel.configure(state="normal")


    def gui_best_run(self):
        """
        Generate runs to get default statistics
        :return:
        """

        # Row Calibration mode, distributed or lumped
        self.frame_best_run_options = ttk.Frame(self.frame_best_run_tab, style="TFrame")

        # default or best run, default indicates deafult run
        self.input_dft_best = tkinter.StringVar()
        self.input_dft_best.set(self.proj_data["cali_options"]["default_best_run"])

        self.button_define_best_runno = ttk.Button(self.frame_best_run_options,
                                                   text="Select Best Parameter Set",
                                                   command=self.select_best_parameter_set)

        self.label_bestrun_purpose = ttk.Label(self.frame_best_run_options, style="TLabel",
                                               text="Best run purpose:")

        self.input_bestrun_purpose = tkinter.StringVar()
        self.input_bestrun_purpose.set("calibration")
        self.radiobutton_calibration = ttk.Radiobutton(self.frame_best_run_options, style="TRadiobutton",
                                                       variable=self.input_bestrun_purpose,
                                                       value="calibration",
                                                       text="Calibration")
        self.radiobutton_validation = ttk.Radiobutton(self.frame_best_run_options, style="TRadiobutton",
                                                      variable=self.input_bestrun_purpose,
                                                      value="validation",
                                                      text="Validation")

        self.frame_best_parms = ttk.Frame(self.frame_best_run_tab, style="TFrame")
        self.scrollbar_best_parms = ttk.Scrollbar(self.frame_best_parms)
        self.treeview_best_parms = ttk.Treeview(self.frame_best_parms,
                                                selectmode="browse",
                                                yscrollcommand=self.scrollbar_best_parms.set)
        self.scrollbar_best_parms.config(command=self.treeview_best_parms.yview)
        # self.treeview_best_parms.bind("<ButtonRelease-1>", self.save_best_parameter_set)

        self.frame_best_run_buttons = ttk.Frame(self.frame_best_run_tab, style="TFrame")
        self.button_save_best_runno = ttk.Button(self.frame_best_run_buttons,
                                                 text="Save Best Parameter Set",
                                                 state="disable",
                                                 command=self.save_best_parameter_set)
        self.button_run_best_model = ttk.Button(self.frame_best_run_buttons,
                                                text="Run with Best Parameter Set",
                                                state="disable",
                                                command=self.processRunSWATBestParmSet)
        self.button_run_best_plot = ttk.Button(self.frame_best_run_buttons,
                                                text="Plot Best Run",
                                                state="disable",
                                                command=self.processPlotBestParmOut)


        padx_val = 2
        pady_val = 5
        ipadx_val = 2
        ipady_val = 2

        # Display calibration mode widgets
        self.frame_best_run_options.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="false", fill="x", side="top")

        self.button_define_best_runno.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="true", fill="none", side="left")
        self.radiobutton_validation.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="true", fill="none", side="right")
        self.radiobutton_calibration.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="true", fill="none", side="right")
        self.label_bestrun_purpose.pack(
            ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
            expand="true", fill="none", side="right")

        self.frame_best_parms.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                   ipady=ipady_val, expand="false", fill="x", side="top")
        self.treeview_best_parms.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                      ipady=ipady_val, expand="true", fill="both", side="left")
        self.scrollbar_best_parms.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                       ipady=ipady_val, expand="false", fill="y", side="right")

        # Display calibration mode widgets
        self.frame_best_run_buttons.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                         expand="false", fill="x", side="top")
        self.button_save_best_runno.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                         expand="true", fill="none", side="left")
        self.button_run_best_model.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                        expand="true", fill="none", side="left")
        self.button_run_best_plot.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                        expand="true", fill="none", side="left")

        # Print output of command in to textbox with scrollbar
        self.frame_best_output = ttk.Frame(self.frame_best_run_tab, style="TFrame")
        self.scrollbar_best_output = ttk.Scrollbar(self.frame_best_output)
        self.textbox_best_output = tkinter.Listbox(self.frame_best_output,
                                                   font=('Microsoft YaHei', 12, 'normal'),
                                                   yscrollcommand=self.scrollbar_best_output.set)
        self.scrollbar_best_output.config(command=self.textbox_best_output.yview)

        self.frame_best_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipady_val, expand="true", fill="both", side="bottom")
        self.textbox_best_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                      ipady=ipady_val, expand="true", fill="both", side="left")
        self.scrollbar_best_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                        ipady=ipady_val, expand="false", fill="y", side="right")

    def select_best_parameter_set(self):
        """
        Setup a tree view and display the objective function values of the best 10 runs
        :return:
        """
        all_outlet_detail = copy.deepcopy(self.proj_data["cali_options"]["outlet_details"])

        path_output = os.path.join(
            self.proj_data["gui_status"]["proj_path"],
            "outfiles_dds")

        cali_mode = self.proj_data["cali_options"]["cali_mode"]

        # Before defining the treeview contents, clear it to prevent adding new contents.
        # Clear the treeview list items
        for item in self.treeview_best_parms.get_children():
            self.treeview_best_parms.delete(item)

        treeview_columns = ["IterationNo"]
        treeview_data = {}
        treeview_row_number = []

        # Reading the objective function values from the output files and display in the tree view.
        for olt_var_key, outlet_detail in all_outlet_detail.items():
            if olt_var_key != "not_grouped_subareas":
                outlet_id = outlet_detail["outletid"]
                variable_id = outlet_detail["variableid"]
                var_name = GlobalVars.pair_varid_obs_header[variable_id].split("(")[0]
                fnp_objective_functions = os.path.join(
                    path_output,
                    "DMPOT_ObjFun_{}{}_{}.out".format(
                        outlet_id, var_name, cali_mode))

                data_key = "ObjValue{}{}".format(outlet_id, var_name)
                treeview_columns.append(data_key)
                treeview_data[data_key] = pandas.read_csv(fnp_objective_functions)
                treeview_row_number.append(treeview_data[data_key].shape[0])

        treeview_row_number = min(treeview_row_number)

        # Defining number of columns
        self.treeview_best_parms["columns"] = tuple(treeview_columns)

        # Defining heading
        self.treeview_best_parms['show'] = 'headings'

        # Assigning the width, anchor, and heading to the respective columns
        for colidx in treeview_columns:
            self.treeview_best_parms.column(colidx, width=90, anchor='center')
            self.treeview_best_parms.heading(colidx, text=colidx)

        # Inserting the items and their features to the columns built
        for run_index in range(treeview_row_number):
            insert_values = ["{}".format(run_index + 1)]
            for tree_col in treeview_columns[1:]:
                insert_values.append(treeview_data[tree_col].loc[run_index, "TestOF"])
            self.treeview_best_parms.insert("", 'end', text="L{}".format(run_index + 1),
                                            values=tuple(insert_values))

        # Enable save button
        self.button_save_best_runno.config(state="normal")

    def save_best_parameter_set(self):
        """
        Get the selected run no and save it to the best_run_no parameter.
        :return:
        """
        selected_item = self.treeview_best_parms.focus()
        # The selected_parm_set is a dictionary
        # {'text': 'L2', 'image': '', 'values': [2, '0.493', '0.058', '0.333'], 'open': 0, 'tags': ''}
        # Get the values and save it to the proj_data
        selected_values = self.treeview_best_parms.item(selected_item)["values"]

        if len(selected_values) <= 0:
            showinfo("Warning", "Please click on the table and select one row to save!")
            # Disable the run best model button
            self.button_run_best_model.config(state="disable")
            return
        else:
            self.proj_data["cali_options"]["best_run_no"] = "{}".format(selected_values[0])
            self.proj_data["cali_options"]["bestrun_purpose"] = self.input_bestrun_purpose.get()
            self.input_bestrun_no.set(self.proj_data["cali_options"]["best_run_no"])
            write_pickle_file(self.proj_data, self.proj_data["gui_status"]["proj_file"])

            process_info = "Iterations for best parameter sets saved: {}".format(
                self.proj_data["cali_options"]["best_run_no"])
            self.textbox_best_output.insert("end",
                                            """{}--{}""".format(current_time(), process_info))
            self.textbox_best_output.see("end")

            # Enable the run best model button
            self.button_run_best_model.config(state="normal")
            self.button_run_best_plot.config(state="normal")

    def processRunDefaultSWAT(self):
        """
        Initiate the running SWAT model with an individual thread instead of
        running with the mainloop, which will not be able to get the function
        to run in serial
        :return:
        """
        # Set the destination of displaying
        # proc.join() is not used since it will suspend the main thread,
        # here, the gui.
        self.button_run_dftmodel.config(state="disable")
        self.display_destination = "run_default"
        self.proc_run_default = threading.Thread(
            target=runDefaultSWAT,
            args=(self.proj_data["cali_options"],
                  self.proj_data["gui_status"]["proj_path"],
                  pipe_process_to_gui[0],
                  ))

        self.proc_run_default.daemon = True
        self.proc_run_default.start()

    def processRunSWATBestParmSet(self):
        """
        Initiate the running SWAT model with an individual thread instead of
        running with the mainloop, which will not be able to get the function
        to run in serial
        :return:
        """
        # Set the destination of displaying
        # proc.join() is not used since it will suspend the main thread,
        # here, the gui.

        self.button_run_best_model.config(state="disable")
        self.display_destination = "run_best"
        self.proc_run_best = threading.Thread(target=runSWATBestParmSet,
                                              args=(pipe_process_to_gui[0],
                                                    self.proj_data["cali_options"],
                                                    self.proj_data["gui_status"]["proj_path"],
                                                    self.proj_data["parms"],
                                                    ))
        self.proc_run_best.daemon = True
        self.proc_run_best.start()


    def processPlotBestParmOut(self):
        """
        Initiate the running SWAT model with an individual thread instead of
        running with the mainloop, which will not be able to get the function
        to run in serial
        :return:
        """
        # Set the destination of displaying
        # proc.join() is not used since it will suspend the main thread,
        # here, the gui.

        self.button_run_best_plot.config(state="disable")
        self.display_destination = "run_best_plot"
        self.proc_run_best_plot = threading.Thread(target=runPlotBestParmOut,
                                              args=(pipe_process_to_gui[0],
                                                    self.proj_data["cali_options"],
                                                    self.proj_data["gui_status"]["proj_path"],
                                                    ))
        self.proc_run_best_plot.daemon = True
        self.proc_run_best_plot.start()


    def processRunCalibration(self):
        """
        collect the parameters and run sa
        :return:
        """
        # Set the destination of displaying
        # proc.join() is not used since it will suspend the main thread,
        # here, the gui.
        self.button_run_cali.config(state="disable")
        self.display_destination = "run_calibration"
        self.proc_run_calibration = threading.Thread(
            target=runCalibration,
            args=(pipe_process_to_gui[0],
                  self.proj_data["cali_options"],
                  self.proj_data["gui_status"]["proj_path"],
                  self.proj_data["parms"],
                  self.proj_data["cali_dds"],))

        self.proc_run_calibration.daemon = True
        self.proc_run_calibration.start()


    def processRunSensitivityAnalysis(self):
        """
        Initiate the running SWAT model with an individual thread instead of
        running with the mainloop, which will not be able to get the function
        to run in serial
        :return:
        """
        # Set the destination of displaying
        # proc.join() is not used since it will suspend the main thread,
        # here, the gui. This is because join will give more cpu resources to the thread
        # instead of the main gui
        # Disable the run button while it is running
        self.button_run_sa.config(state="disable")
        self.display_destination = "run_sa"

        self.proc_run_sa = threading.Thread(
            target=runSensitivityAnalysis,
            args=(pipe_process_to_gui[0],
                  self.proj_data["sa_method_parm"],
                  self.proj_data["cali_options"],
                  self.proj_data["gui_status"]["proj_path"],
                  self.proj_data["parms"],))

        self.proc_run_sa.daemon = True
        self.proc_run_sa.start()

    def gui_cali_plot(self):
        """
        Interface for plotting. The interface will allow users
        to generate different types of plots including:
        1. time series plots
        2. uncertainty analysis plots
        3. flow duration curve
        Users need to select the outlet, var, run no, and plot type.
        These plots will be saved in the output_plots folder and displayed in the
        interface.
        :return:
        """

        # Row Calibration mode, distributed or lumped
        self.frame_plot_details_buttons = ttk.Frame(self.frame_cali_plot_tab, style="TFrame")

        self.btn_define_plot_details = ttk.Button(self.frame_plot_details_buttons,
                                                  style="TButton",
                                                  text="Define plot details",
                                                  command=self.define_plot_details)
        self.btn_save_plot_details = ttk.Button(self.frame_plot_details_buttons,
                                                style="TButton",
                                                text="Save plot details",
                                                command=self.save_plot_details)
        self.button_run_cali_plot = ttk.Button(self.frame_plot_details_buttons,
                                          style="TButton",
                                          text="Create plots",
                                          state="disable",
                                          command=self.processRunCaliPlot)
        #
        # self.input_plot_timeseries = tkinter.StringVar()
        # self.input_plot_timeseries.set("false")
        # self.ckbtn_plot_timeseries = ttk.Checkbutton(
        #     self.frame_plot_type,
        #     style="TCheckbutton",
        #     text="""Time series plot""",
        #     onvalue="true",
        #     offvalue="false",
        #     variable=self.input_plot_timeseries,
        #     state='normal',
        #     command=self.define_plot_target
        # )
        # 
        # self.input_plot_fdc = tkinter.StringVar()
        # self.input_plot_fdc.set("false")
        # self.ckbtn_plot_fdc = ttk.Checkbutton(
        #     self.frame_plot_type,
        #     style="TCheckbutton",
        #     text="""Duration curve""",
        #     onvalue="true",
        #     offvalue="false",
        #     variable=self.input_plot_fdc,
        #     state='normal',
        #     command=self.define_plot_target
        # )

        padx_val = 2
        pady_val = 5
        ipadx_val = 2
        ipady_val = 2

        # Display calibration mode widgets
        self.frame_plot_details_buttons.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                             expand="false", fill="x", side="top")
        self.btn_define_plot_details.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                          expand="true", fill="none", side="left")
        self.btn_save_plot_details.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                        expand="true", fill="none", side="left")
        self.button_run_cali_plot.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                  expand="true", fill="none", side="left")

        self.frame_plot_details = ttk.Frame(self.frame_cali_plot_tab, style="TFrame")
        self.frame_plot_details.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                     ipady=ipadx_val, expand=False, fill="x", side="top")

        # self.ckbtn_plot_timeseries.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
        #                            expand="false", fill="none", side="left")
        # self.ckbtn_plot_fdc.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
        #                               expand="true", fill="none", side="right")
        #

        # TODO: Add function to read the objective function of all outlets, and display sorted best
        # variables in a tree view. Add a scrollbar for display
        # Also, add calibration and validation options. It will be easier here.

        # Print output of command in to textbox with scrollbar
        self.frame_plot_output = ttk.Frame(self.frame_cali_plot_tab, style="TFrame")
        self.scrollbar_plot_output = ttk.Scrollbar(self.frame_plot_output)
        self.textbox_plot_output = tkinter.Listbox(self.frame_plot_output,
                                                   font=('Microsoft YaHei', 12, 'normal'),
                                                   yscrollcommand=self.scrollbar_plot_output.set)
        self.scrollbar_plot_output.config(command=self.textbox_plot_output.yview)

        self.frame_plot_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                    ipady=ipady_val, expand="true", fill="both", side="top")
        self.textbox_plot_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                      ipady=ipady_val, expand="true", fill="both", side="left")
        self.scrollbar_plot_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                        ipady=ipady_val, expand="false", fill="y", side="right")

    def define_plot_details(self):
        """
        Define the outlet, variable, and run number for plotting
        :return:
        """

        padx_val = 2
        pady_val = 2
        ipadx_val = 0
        ipady_val = 0

        if self.proj_data["gui_status"]["define_plot_target"] == "false":

            self.plot_target_details = dict()
            self.frame_plot_target_rep = dict()

            # defining outlet id, variables to be calibrated, outlet weights,
            self.frame_plot_target_labels = ttk.Frame(self.frame_plot_details, style="TFrame")
            self.label_order_no_plot = ttk.Label(self.frame_plot_target_labels, style="TLabel", text="Order No")
            self.label_outlet_id_plot = ttk.Label(self.frame_plot_target_labels, style="TLabel", text="Outlet ID")
            self.label_variable_plot = ttk.Label(self.frame_plot_target_labels, style="TLabel", text="Variable")
            self.label_plot_timeseries = ttk.Label(self.frame_plot_target_labels, style="TLabel",
                                                   text="Plot time series")
            self.label_plot_fdc = ttk.Label(self.frame_plot_target_labels, style="TLabel", text="Plot duration curve")
            self.label_plot_runno = ttk.Label(self.frame_plot_target_labels, style="TLabel", text="Plot Run No")

            self.frame_plot_target_labels.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                               ipady=ipadx_val, expand="false", fill="none", side="left")
            self.label_order_no_plot.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                          ipady=ipadx_val, expand="false", fill="none", side="top")
            self.label_outlet_id_plot.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                           ipady=ipadx_val, expand="false", fill="none", side="top")
            self.label_variable_plot.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                          ipady=ipadx_val, expand="false", fill="none", side="top")
            self.label_plot_timeseries.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                            ipady=ipadx_val, expand="false", fill="none", side="top")
            self.label_plot_fdc.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                     ipady=ipadx_val, expand="false", fill="none", side="top")
            self.label_plot_runno.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                       ipady=ipadx_val, expand="false", fill="none", side="top")

            for outlet_key, outlet_detail in self.proj_data["cali_options"]["outlet_details"].items():
                if not outlet_detail["outletid"] == "not_grouped_subareas":
                    ovkey = "{}".format(outlet_key)
                    self.plot_target_details[ovkey] = dict()
                    self.plot_target_details[ovkey]["orderno"] = tkinter.StringVar()
                    self.plot_target_details[ovkey]["outletid"] = tkinter.StringVar()
                    self.plot_target_details[ovkey]["variableid"] = tkinter.StringVar()
                    self.plot_target_details[ovkey]["plot_time_series"] = tkinter.StringVar()
                    self.plot_target_details[ovkey]["plot_duration_curve"] = tkinter.StringVar()
                    self.plot_target_details[ovkey]["plot_runno"] = tkinter.StringVar()

                    self.plot_target_details[ovkey]["orderno"].set(ovkey)
                    self.plot_target_details[ovkey]["outletid"].set(
                        self.proj_data["cali_options"]["outlet_details"][ovkey]["outletid"]
                    )
                    self.plot_target_details[ovkey]["variableid"].set(
                        self.proj_data["cali_options"]["outlet_details"][ovkey]["variableid"]
                    )
                    self.plot_target_details[ovkey]["plot_time_series"].set(
                        self.proj_data["cali_options"]["outlet_details"][ovkey]["plot_time_series"]
                    )
                    self.plot_target_details[ovkey]["plot_duration_curve"].set(
                        self.proj_data["cali_options"]["outlet_details"][ovkey]["plot_duration_curve"]
                    )
                    self.plot_target_details[ovkey]["plot_runno"].set(
                        self.proj_data["cali_options"]["outlet_details"][ovkey]["plot_runno"]
                    )

                    self.frame_plot_target_rep[ovkey] = dict()
                    self.frame_plot_target_rep[ovkey]["column_frame"] = ttk.Frame(
                        self.frame_plot_details, style="TFrame")
                    self.frame_plot_target_rep[ovkey]["column_frame"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                        ipady=ipadx_val, expand="false", fill="none",
                        side="left")

                    self.frame_plot_target_rep[ovkey]["items"] = dict()

                    self.frame_plot_target_rep[ovkey]["items"]["orderno"] = ttk.Label(
                        self.frame_plot_target_rep[ovkey]["column_frame"],
                        style="TLabel",
                        textvariable=self.plot_target_details[ovkey]["orderno"])

                    self.frame_plot_target_rep[ovkey]["items"]["outletid"] = ttk.Label(
                        self.frame_plot_target_rep[ovkey]["column_frame"],
                        style="TLabel",
                        textvariable=self.plot_target_details[ovkey]["outletid"])

                    self.frame_plot_target_rep[ovkey]["items"]["variableid"] = ttk.Label(
                        self.frame_plot_target_rep[ovkey]["column_frame"],
                        style="TLabel",
                        textvariable=self.plot_target_details[ovkey]["variableid"])

                    self.frame_plot_target_rep[ovkey]["items"]["plot_time_series"] = ttk.Checkbutton(
                        self.frame_plot_target_rep[ovkey]["column_frame"],
                        style="TCheckbutton",
                        onvalue="true",
                        offvalue="false",
                        variable=self.plot_target_details[ovkey]["plot_time_series"])

                    self.frame_plot_target_rep[ovkey]["items"]["plot_duration_curve"] = ttk.Checkbutton(
                        self.frame_plot_target_rep[ovkey]["column_frame"],
                        style="TCheckbutton",
                        onvalue="true",
                        offvalue="false",
                        variable=self.plot_target_details[ovkey]["plot_duration_curve"])

                    self.frame_plot_target_rep[ovkey]["items"]["plot_runno"] = ttk.Entry(
                        self.frame_plot_target_rep[ovkey]["column_frame"],
                        width=5, style="TEntry",
                        textvariable=self.plot_target_details[ovkey]["plot_runno"],
                        justify="center"
                    )

                    self.frame_plot_target_rep[ovkey]["items"]["orderno"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                        ipady=ipadx_val, expand="false", fill="none",
                        side="top")
                    self.frame_plot_target_rep[ovkey]["items"]["outletid"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                        ipady=ipadx_val, expand="false", fill="none",
                        side="top")
                    self.frame_plot_target_rep[ovkey]["items"]["variableid"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                        ipady=ipadx_val, expand="false", fill="none",
                        side="top")
                    self.frame_plot_target_rep[ovkey]["items"]["plot_time_series"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                        ipady=ipadx_val, expand="false", fill="none",
                        side="top")
                    self.frame_plot_target_rep[ovkey]["items"]["plot_duration_curve"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                        ipady=ipadx_val, expand="false", fill="none",
                        side="top")
                    self.frame_plot_target_rep[ovkey]["items"]["plot_runno"].pack(
                        padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                        ipady=ipadx_val, expand="false", fill="none",
                        side="top")

            # Set the define_plot_target to be true to prevent interface conflict.
            self.proj_data["gui_status"]["define_plot_target"] == "true"

    def save_plot_details(self):
        """
        save the outlet, variable, and run number for plotting, and
        enable the button of create plot
        :return:
        """
        for outlet_key, outlet_detail in self.proj_data["cali_options"]["outlet_details"].items():
            if not outlet_detail["outletid"] == "not_grouped_subareas":
                outlet_detail["plot_time_series"] = self.plot_target_details[outlet_key]["plot_time_series"].get()
                outlet_detail["plot_duration_curve"] = self.plot_target_details[outlet_key]["plot_duration_curve"].get()
                outlet_detail["plot_runno"] = self.plot_target_details[outlet_key]["plot_runno"].get()

        self.button_run_cali_plot.config(state="normal")

        # Add the confirmation to the information box
        self.textbox_plot_output.insert("end",
                                        """{}--Plot details saved""".format(
                                            current_time()))

    def processRunCaliPlot(self):
        """
        collect the parameters and run sa
        :return:
        """
        # Set the destination of displaying
        # proc.join() is not used since it will suspend the main thread,
        # here, the gui.
        self.button_run_cali_plot.config(state="disable")
        self.display_destination = "run_cali_plot"

        self.proc_run_cali_plot = threading.Thread(
            target=runCalibrationPlots,
            args=(pipe_process_to_gui[0],
                  self.proj_data["cali_options"]["outlet_details"],
                  self.proj_data["gui_status"]["proj_path"],
                  self.proj_data["cali_options"]["cali_mode"],
                  self.proj_data["cali_dds"]["totalsimno"],
                  ))

        self.proc_run_cali_plot.daemon = True
        self.proc_run_cali_plot.start()

    def gui_uncertainty(self):
        """
        Interface for uncertainty.
        Basically, the uncertainty is a figure showing the time series of
        simulated values with acceptable runs.
        :return:
        """

        # Row Calibration mode, distributed or lumped
        self.frame_uncertainty_button = ttk.Frame(self.frame_uncertainty_tab, style="TFrame")

        self.label_bestrun_no = ttk.Label(self.frame_uncertainty_button, style="TLabel",
                                          text="Best Iteration No")
        self.input_bestrun_no = tkinter.StringVar()
        self.input_bestrun_no.set(self.proj_data["cali_options"]["best_run_no"])

        self.entry_bestrun_no = ttk.Entry(self.frame_uncertainty_button, width=5, style="TEntry",
                                          textvariable=self.input_bestrun_no,
                                          justify="center",
                                          state="normal")

        self.button_gene_uncertainty_plot = ttk.Button(self.frame_uncertainty_button,
                                                       text="Run Uncertainty Plot",
                                                       command=self.processGeneUncertaintyPlot)

        padx_val = 2
        pady_val = 5
        ipadx_val = 2
        ipady_val = 2

        # Display calibration mode widgets
        self.frame_uncertainty_button.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                           expand="false", fill="x", side="top")

        self.label_bestrun_no.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                   expand="false", fill="none", side="left")
        self.entry_bestrun_no.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                   expand="false", fill="none", side="left")

        self.button_gene_uncertainty_plot.pack(ipadx=ipadx_val, ipady=ipady_val, padx=padx_val, pady=pady_val,
                                               expand="true", fill="none", side="right")

        # TODO: Add function to read the objective function of all outlets, and display sorted best
        # variables in a tree view. Add a scrollbar for display
        # Also, add calibration and validation options. It will be easier here.

        # Print output of command in to textbox with scrollbar
        self.frame_uncertainty_output = ttk.Frame(self.frame_uncertainty_tab, style="TFrame")
        self.scrollbar_uncertainty_output = ttk.Scrollbar(self.frame_uncertainty_output)
        self.textbox_uncertainty_output = tkinter.Listbox(self.frame_uncertainty_output,
                                                          font=('Microsoft YaHei', 12, 'normal'),
                                                          yscrollcommand=self.scrollbar_uncertainty_output.set)
        self.scrollbar_uncertainty_output.config(command=self.textbox_uncertainty_output.yview)

        self.frame_uncertainty_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                           ipady=ipady_val, expand="true", fill="both", side="top")
        self.textbox_uncertainty_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                             ipady=ipady_val, expand="true", fill="both", side="left")
        self.scrollbar_uncertainty_output.pack(padx=padx_val, pady=pady_val, ipadx=ipadx_val,
                                               ipady=ipady_val, expand="false", fill="y", side="right")

    def processGeneUncertaintyPlot(self):

        """
        Generate uncertainty plot
        :return:
        """
        self.display_destination = "run_uncertainty"

        if (int(self.input_bestrun_no.get()) > int(self.proj_data["cali_dds"]["totalsimno"])) or (
                int(self.input_bestrun_no.get()) == 0
        ):
            showinfo("Warning", "Please select a number between 1 and Total iteration no")
            return
        else:
            self.proj_data["cali_options"]["best_run_no"] = self.input_bestrun_no.get()

            self.proc_run_uncertainty_plot = threading.Thread(
                target=runUncertaintyPlot,
                args=(pipe_process_to_gui[0],
                      self.proj_data["cali_options"]["outlet_details"],
                      self.proj_data["gui_status"]["proj_path"],
                      self.proj_data["cali_options"],
                      self.proj_data["cali_dds"]["totalsimno"],
                      ))

            self.proc_run_uncertainty_plot.daemon = True
            self.proc_run_uncertainty_plot.start()

    def gui_about(self):
        """
        This function defines the about tab that introduces basic information about the program
        :return:
        """


        # Display
        padx_val = 2
        pady_val = 2
        ipadx_val = 2
        ipady_val = 1
        
        # Label information variables
        self.frame_about = ttk.Frame(self.frame_about_tab, style="TFrame")
        self.label_about_blank = ttk.Label(
            self.frame_about,
            text="""""",
            style="TLabel",
            justify="left")
        self.label_about_title = ttk.Label(
            self.frame_about,
            text="""DMPOTSWAT: Distributed Model Parameter Optimization Tool for the SWAT model""",
            style="TLabel",
            justify="left")
        self.label_about_developer = ttk.Label(
            self.frame_about,
            text="""Developer: Qingyu Feng""",
            style="TLabel",
            justify="left")
        self.label_about_institute = ttk.Label(
            self.frame_about,
            text="""Institute: Research Center for Eco-Environmental Sciences, Chinese Academy of Sciences""",
            style="TLabel",
            justify="left")
        self.label_about_available = ttk.Label(
            self.frame_about,
            text="""Available at: RCEES Eco-model Cloud""",
            style="TLabel",
            justify="left")
        ecomodel_url = """http://dse.rcees.cas.cn/kyzy/stmx/"""
        self.label_about_url = ttk.Label(
            self.frame_about,
            text=ecomodel_url,
            style="TLabel",
            foreground="blue",
            justify="left"
        )
        self.label_about_url.configure(font="underline")
        # Add hyperlink to allow click
        self.label_about_url.bind("<Button-1>", lambda e:
            self.open_url(ecomodel_url))

        self.label_about_email = ttk.Label(
            self.frame_about,
            text="qyfeng18@rcees.ac.cn",
            style="TLabel",
            justify="left")
        # Add the logo below
        self.img_logo = tkinter.PhotoImage(file=GlobalVars.path_main_logo)
        self.label_about_logo = ttk.Label(
            self.frame_about,
            image=self.img_logo,
            style="TLabel",
            justify="left")

        self.frame_about.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="false", fill="both", side="top")
        # self.label_about_blank.pack(
        #     padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
        #     expand="true", fill="y", side="top", anchor="w")
        self.label_about_title.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="y", side="top", anchor="w")
        self.label_about_developer.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="y", side="top", anchor="w")
        self.label_about_institute.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="y", side="top", anchor="w")
        self.label_about_available.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="y", side="top", anchor="w")
        self.label_about_url.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="y", side="top", anchor="w")
        self.label_about_email.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="y", side="top", anchor="w")
        self.label_about_logo.pack(
            padx=padx_val, pady=pady_val, ipadx=ipadx_val, ipady=ipady_val,
            expand="true", fill="y", side="top", anchor="w")

    def open_url(self, url):
        webbrowser.open_new_tab(url)

if __name__ == "__main__":
    mainWindow = mainWindow()

    mainWindow.mainloop()
