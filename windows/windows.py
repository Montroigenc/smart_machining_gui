import tkinter as tk
import tkinter.ttk as TTK
from tkinter import messagebox, filedialog
import cv2
import PIL.Image, PIL.ImageTk
import pyautogui
import numpy as np
import os
import glob
import ntpath
import datetime
import time
import sys
import traceback
import shutil


class NormalFrame(tk.Frame):
    """A pure Tkinter frame
    * Use the 'interior' attribute to place widgets inside the frame
    * Construct and pack/place/grid normally

    """
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        # create a canvas object
        canvas = tk.Canvas(self, bd=0, highlightthickness=2)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        # canvas.pack(side=tk.LEFT, fill=tk.X, expand=tk.TRUE)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=tk.NW)

        # track changes to the canvas and frame width and sync them
        def _configure_interior(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)


class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=2, yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=tk.NW)

        # track changes to the canvas and frame width and sync them, also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)


class Window:
    def __init__(self, name, title, tools_data=None):
        self.name = name
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.user_exit)
        self.root.title(title)
        self.res = "ini"
        # self.operation_parameters = {}
        self.vc_data = {}
        self.manual_exit = False
        self.tools_data = tools_data
        self.active_tables = dict()

    def __call__(self, *args, **kwargs):
        self.root.mainloop()

    def get_button(self, text, color, fcn, w=12, h=3, font_size=16, padx=2, pady=2):
        return tk.Button(self.root, text=text, width=w, height=h, command=fcn, bg=color, font=('Helvetica', '{}'.format(font_size)),
                         wraplength=160, padx=padx, pady=pady)

    def change_program_state(self, s, key=None, root=None):
        self.res = s

        if s == 'add':
            self.append_vc_row(key, root=root)

        elif "file_" in s:
            # n = int(s.replace("file_", ""))
            # n_vc = (n - 1) * 2 + 1
            # n_file = n + 2
            # n_pc = (n - 1) * 2 + 2

            # vc = self.root.children[f"!entry{n_vc}"].get()
            filename = tk.filedialog.askopenfilename(initialdir="/", title="Sélectionner un fichier")
            if filename != "":
                n = s.replace("file_", "")
                n = '' if n == '0' else n
                # self.root.children[f"!button{n_file}"].configure(fg="green", text=filename)
                root.children['vc_parameters'].children[f"!button{n}"].configure(fg="green", text=filename)
        else:
            self.root.quit()

    def append_date(self):
        from datetime import date
        today = date.today()

        row = tk.Frame(self.root)
        lab = tk.Label(row, width=20, text="Date du traitement: ", anchor='w', padx=5, pady=5)

        day = tk.ttk.Combobox(row, values=[i for i in range(1, 32)])
        day.current(today.day - 1)

        month = tk.ttk.Combobox(row, values=["janvier",
                                        "février",
                                        "mars",
                                        "avril",
                                        "mai",
                                        "juin",
                                        "juillet",
                                        "aout",
                                        "septembre",
                                        "octobre",
                                        "novembre",
                                        "décembre"],
                                state="readonly")

        month.current(today.month - 1)

        year = tk.ttk.Combobox(row, values=[i for i in range(2020, 2040)])
        year.current(today.year - 2020)

        row.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        lab.pack(side=tk.LEFT)
        day.pack(side=tk.LEFT, pady=5)
        month.pack(side=tk.LEFT, padx=5, pady=5)
        year.pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)

        # self.operation_parameters["date"] = row

    def append_entry_row(self, key, text, root=None):
        row = tk.Frame(self.set_root(root), name=key)
        lab = tk.Label(row, width=20, text=text+": ", anchor='w', padx=5, pady=5)
        ent = tk.Entry(row)
        row.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        lab.pack(side=tk.LEFT, padx=20, pady=5)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

        # self.operation_parameters[key] = row

    def set_root(self, key):
        if key is None:
            return self.root
        elif type(key) is str:
            return self.active_tables[key]
        else:
            return key

    def set_operation_window(self):
        # self.active_tables["input_parameters"] = tk.Frame(self.root, name="input_parameters", borderwidth=3)  #.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        # self.active_tables["buttons"] = tk.Frame(self.root, name="buttons")  #.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        # self.active_tables["vc_parameters"] = tk.Frame(self.root, name="vc_parameters")  #.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)

        self.active_tables["input_parameters"] = NormalFrame(self.root)
        self.active_tables["input_parameters"].pack()
        self.set_vc_headers(["Paramètres d’entrée", "Valeurs utilisées"], 'vc_headers_1', self.active_tables["input_parameters"].interior)
        self.append_entry_row("engagement_Axial", "Engagement axial ap (mm) ", root=self.active_tables["input_parameters"].interior)
        self.append_entry_row("engagement_radial", "Engagement radial ae (mm)", root=self.active_tables["input_parameters"].interior)
        self.append_entry_row("avance_dent", "Avance par dent fz (mm/tr) ", root=self.active_tables["input_parameters"].interior)

        # Set input parameters table
        # self.set_vc_headers(["Paramètres d’entrée", "Valeurs utilisées"], "input_parameters")
        # self.append_entry_row("engagement_Axial", "Engagement axial ap (mm) ", root="input_parameters")
        # self.append_entry_row("engagement_radial", "Engagement radial ae (mm)", root="input_parameters")
        # self.append_entry_row("avance_dent", "Avance par dent fz (mm/tr) ", root="input_parameters")



        # Set headers
        # self.set_vc_headers(["Mesure n°", "Vitesse de coupe Vc (m/min)", "Fichier de mesure", "Pc (W)"], "vc_parameters")

        self.active_tables["vc_parameters"] = VerticalScrolledFrame(self.root)
        self.active_tables["vc_parameters"].pack()

        self.set_vc_headers(["Mesure n°", "Vitesse de coupe Vc (m/min)", "Fichier de mesure", "Pc (W)"], 'vc_headers_2', self.active_tables["vc_parameters"].interior)

        # Set first row
        self.append_vc_row("vc_parameters", self.active_tables["vc_parameters"].interior)

        # Set buttons
        self.active_tables["buttons"] = NormalFrame(self.root)
        self.active_tables["buttons"].pack()
        self.append_buttons("buttons", root=self.active_tables["buttons"].interior, root_table=self.active_tables["vc_parameters"].interior)

        # Pack frames
        # for key in self.active_tables.keys():
        #     self.active_tables[key].pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)

    def append_label_row(self, key, text1, text2="", root=None):
        row = tk.Frame(self.set_root(root), name=key)
        lab1 = tk.Label(row, width=20, text=text1+": ", anchor='w', padx=5, pady=5)
        lab2 = tk.Label(row, width=20, text=text2, anchor='w', padx=5, pady=5)
        row.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        lab1.pack(side=tk.LEFT)
        lab2.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

        # self.operation_parameters[key] = row

    def cbox_callback(self, eventObject):
        self.root.children['diametre'].children['!label2']['text'] = self.tools_data[eventObject.widget.get()][1]
        self.root.children['n_dents'].children['!label2']['text'] = self.tools_data[eventObject.widget.get()][2]

    def append_combobox_row(self, key, text, values):
        row = tk.Frame(self.root, name=key)
        lab = tk.Label(row, width=20, text=text + ": ", anchor='w', padx=5, pady=5)
        cbox = tk.ttk.Combobox(row, values=values, state="readonly")
        cbox.bind("<<ComboboxSelected>>", self.cbox_callback)

        row.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        lab.pack(side=tk.LEFT)
        cbox.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

        # self.operation_parameters[key] = row

    def append_buttons(self, key, root=None, root_table=None):
        row = tk.Frame(self.set_root(root), name=key)
        row.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=5)
        btn_next = tk.Button(row, text="Suivant", command=lambda *args: self.change_program_state("next"), bg="green", padx=10, pady=5)
        btn_add = tk.Button(row, text="Ajouter une autre ligne", command=lambda *args: self.change_program_state("add", key=key, root=root_table), bg="light sky blue", padx=10, pady=5)

        # btn_next.grid(row=0, column=0, pady=20, padx=5, columnspan=2)
        # btn_add.grid(row=0, column=2, pady=20, padx=5, columnspan=2)

        btn_next.pack(side=tk.LEFT, padx=5, pady=5)
        btn_add.pack(side=tk.LEFT, padx=5, pady=5)

    def set_vc_headers(self, headers, key, root=None):
        row = tk.Frame(self.set_root(root), name=key)
        row.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)

        for i, h in enumerate(headers):
            # tk.Label(row, text=h).grid(row=0, column=int(i / len(headers) * 4), pady=5, padx=5, columnspan=2)  #.pack(side=tk.LEFT)
            tk.Label(row, text=h).pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)

        # tk.Label(row, text="Mesure n°").pack(side=tk.LEFT)
        # tk.Label(row, text="Vitesse de coupe Vc (m/min)").pack(side=tk.LEFT)
        # tk.Label(row, text="Fichier de mesure").pack(side=tk.LEFT)
        # tk.Label(row, text="Pc (W)").pack(side=tk.LEFT)

        # l0 = tk.Label(row, text="Mesure n°").grid(row=1, column=0, pady=5, padx=5)
        # l1 = tk.Label(row, text="Vitesse de coupe Vc (m/min)").grid(row=1, column=1, pady=5, padx=5)
        # l2 = tk.Label(row, text="Fichier de mesure").grid(row=1, column=2, pady=5, padx=5)
        # l3 = tk.Label(row, text="Pc (W)").grid(row=1, column=3, pady=5, padx=5)
        #
        # row.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        # l0.pack(side=tk.LEFT)
        # l1.pack(side=tk.LEFT)
        # l2.pack(side=tk.LEFT)
        # l3.pack(side=tk.LEFT)

        # self.vc_data["headers"] = ["Mesure n°", "Vitesse de coupe Vc (m/min)", "Fichier de mesure", "Pc (W)"]

    def append_vc_row(self, key, root=None):
        row = tk.Frame(self.set_root(root), name=key)
        row.pack(side=tk.TOP, fill=tk.X, padx=20)

        n = len(self.vc_data)
        # tk.Label(row, text=f"{n}").grid(row=n+1, column=0, pady=5, padx=5)
        # ent_vc = tk.Entry(row).grid(row=n+1, column=1, pady=5, padx=5)
        # btn_file = tk.Button(row, text="Parcourir", command=lambda *args: self.change_program_state(f"file_{n}", key)).grid(row=n+1, column=2, pady=5, padx=5)
        # ent_pc = tk.Entry(row).grid(row=n+1, column=3, pady=5, padx=5)

        tk.Label(row, text=f"{n}").pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)
        ent_vc = tk.Entry(row).pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)
        btn_file = tk.Button(row, text="Parcourir", command=lambda *args: self.change_program_state(f"file_{n}", key, root=root)).pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)
        ent_pc = tk.Entry(row).pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)

        # self.vc_data[f"{n}"] = [ent_vc, btn_file, ent_pc, ""]
        self.vc_data[f"{n}"] = row

    def quit(self):
        self.root.destroy()
        self.root.quit()

    def user_exit(self):
        selection = tk.messagebox.askquestion("quitter l'application", "Voulez-vous vraiment quitter l'application?", icon='warning')

        if selection == 'yes':
            self.root.quit()


def set_trioption_window(name, title, t1, t2, t3):
    win = Window(name, title)

    # Set buttons
    win.btn1 = win.get_button(text=t1, color="blue", fcn=lambda *args: win.change_program_state(t1))
    win.btn2 = win.get_button(text=t2, color="green", fcn=lambda *args: win.change_program_state(t2))
    win.btn3 = win.get_button(text=t3, color="yellow", fcn=lambda *args: win.change_program_state(t3))

    # Place everything
    win.btn1.grid(row=0, column=0, padx=20, pady=20)
    win.btn2.grid(row=0, column=1, padx=20, pady=20)
    win.btn3.grid(row=0, column=2, padx=20, pady=20)

    win()

    res = win.res

    win.quit()

    return res


def parse_res(win):
    res = {}
    for key in win.root.children:
        if not "button" in key:
            label = win.root.children[key].children["!label"].cget("text")
            vals = []
            for wn in win.root.children[key].children:
                if 'entry' in wn or 'combobox' in wn:
                    vals.append(f"{win.root.children[key].children[wn].get()}")
                elif 'label2' in wn:
                    vals.append(f"{win.root.children[key].children[wn]['text']}")

            res[label] = ('/'.join(vals, ))

    return res


def set_general_parameters(win):
    # Set text entries
    win.append_combobox_row("outil", "Outil", list(win.tools_data.keys()))
    # win.append_user_text("outil", "Outil")
    win.append_label_row("diametre", "Diamètre")
    win.append_label_row("n_dents", "Nombre de dents")
    # win.append_user_text("diametre", "Diamètre")
    # win.append_user_text("n_dents", "Nombre de dents")
    win.append_entry_row("operateur", "Opérateur")
    win.append_date()
    win.append_entry_row("lubrification", "Lubrification")
    win.append_entry_row("commentaires", "Commentaires")

    # Set buttons
    win.btn1 = win.get_button(text="Suivant", color="green", fcn=lambda *args: win.change_program_state("next"))
    win.btn1.pack(pady=10)


def set_fraisage_parameters_table(win):
    # Set entry parameters table
    win.add_table("input_parameters")
    # win.append_label_row("table1_header", "Paramètres d’entrée", "Valeurs utilisées")
    # win.append_entry_row("engagement_Axial", "Engagement axial ap (mm) ")
    # win.append_entry_row("engagement_radial", "Engagement radial ae (mm)")
    # win.append_entry_row("avance_dent", "Avance par dent fz (mm/tr) ")
    #
    # # Set buttons
    # win.btn1 = win.get_button(text="Suivant", color="green", fcn=lambda *args: win.change_program_state("next"))
    # win.btn1.pack(pady=10)


def set_dynamic_entry(win):
    # # create a vertical scrollbar-no need
    # # to write orient as it is by
    # # default vertical
    # v = tk.Scrollbar(win)
    #
    # # attach Scrollbar to root window on the side
    # v.grid(row=1, column=4, pady=5, padx=5, rowspan=4)

    # Set buttons
    win.append_buttons()

    # Set table frame
    # win.add_table("vc_parameters")

    # Set headers
    win.set_vc_headers("vc_parameters")

    # Set first row
    win.append_vc_row("vc_parameters")


def set_user_input_parameters_window(name, title, tools_data, operation=''):
    win = Window(name, title, tools_data)

    if operation == "":
        set_general_parameters(win)
    else:
        if operation == "Fraisage":
            win.set_operation_window()
            # set_fraisage_parameters_table(win)
        # elif operation == "Perçage":
        #     set_fraisage_parameters(win)
        # elif operation == "Tournage":
        #     set_fraisage_parameters(win)
        # elif operation == "vc_range":
        # set_dynamic_entry(win)

    win()

    res = parse_res(win)

    win.quit()

    return res





# class UserGUIOld():
#     def __init__(self):
#         if getattr(sys, 'frozen', False):
#             application_path = os.path.dirname(sys.executable)
#         elif __file__:
#             application_path = os.path.dirname(__file__)
#
#         config_path = os.path.join(application_path, "config.ini")
#
#         self.loadConfig(config_path)
#         self.inputDir = self.loadPathFromConfig(application_path, "inputDir")
#         self.outputDir = self.loadPathFromConfig(application_path, "outputDir")
#         self.labeledDir = self.loadPathFromConfig(application_path, "labeledDir")
#
#         self.w_partitions = int(self.configParams["widthPartitions"])
#         self.h_partitions = int(self.configParams["heightPartitions"])
#         self.screenSize = pyautogui.size()
#         self.possibleTypes = [p for p in self.configParams["possibleTypes"].split(", ")]
#         self.removeInputDirImages = self.configParams["removeInputDirImages"] == "True"
#         self.imageSize = int(self.configParams["imageSize"])
#
#         self.possibleScores = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
#         self.programStatus = ''
#
#     def loadPathFromConfig(self, application_path, folderName):
#         if folderName not in self.configParams:
#             root = tk.Tk()
#             root.withdraw()
#             messagebox.showerror("Error", '{} chemin non présent dans le fichier de configuration.'.format(folderName))
#
#         path = os.path.join(application_path, self.configParams[folderName])
#         if os.path.isdir(path):
#             print("{} path set to {}".format(folderName, path))
#             return path
#         else:
#             root = tk.Tk()
#             root.withdraw()
#             messagebox.showerror("Error", "Le dossier {} n'existe pas.".format(path))
#
#     def loadConfig(self, filePath):
#         if os.path.isfile(filePath):
#             f = open(filePath, "r", encoding='utf-8')
#             data = f.read().replace("\ufeff", "")
#             data = data.split("\n")
#
#             self.configParams = dict()
#             for l in data:
#                 l = l.split(" = ")
#                 self.configParams["{}".format(l[0])] = l[1]
#
#             print("{} config file loaded".format(filePath))
#         else:
#             root = tk.Tk()
#             root.withdraw()
#             messagebox.showerror("Error", "Le fichier de configuration n'est pas présent dans {}".format(filePath))
#
#
#     def userExit(self):
#         selection = tk.messagebox.askquestion("quitter l'application", "Voulez-vous vraiment quitter l'application?", icon='warning')
#
#         if selection == 'yes':
#             self.root.destroy()
#             self.root.quit()
#             self.programStatus = 'break'
#
#     def setWaitingWindow(self):
#         self.window = 'waiting'
#         self.root = tk.Tk()
#         self.root.protocol("WM_DELETE_WINDOW", self.userExit)
#         self.root.title("Contrôle estétique")
#
#         # Set labels
#         tk.Label(self.root, text="En attente d'un déclencheur TCP/IP.", font=('Helvetica', '16')).pack(padx=10, pady=10)
#
#         # Set buttons
#         self.btn_trigger = self.getButton(text="Téléchargez une image manuellement", color="green", fcn=lambda *args: self.changeProgramState('trigger'), w=16).pack(padx=10, pady=10)
#
#         self.root.mainloop()
#
#     def setMainWindow(self):
#         self.window = 'main'
#         self.root = tk.Tk()
#         self.root.protocol("WM_DELETE_WINDOW", self.userExit)
#         self.root.title("Contrôle estétique")
#
#         # setting up a tkinter canvas with scrollbars
#         frame = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
#         self.canvas = tk.Canvas(frame, bd=0, width=self.image.shape[1], height=self.image.shape[0])
#
#         self.pil_defects_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.currentPart.defects_image))
#         self.image_on_canvas = self.canvas.create_image(0, 0, image=self.pil_defects_image)
#         self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
#
#         # Set buttons
#         self.btn_lancer = self.getButton(text="Lancer étiquetage", color="blue", fcn=lambda *args: self.changeProgramState('next'))
#
#         # Text that displays the reference piece
#         self.text_display = tk.Text(self.root, state='normal', width=40, height=15)
#         self.text_display.tag_configure("right", justify='right')
#         self.text_display.insert('end', 'Reference pièce:\n{}\n'.format(self.currentPart.ref))
#         self.text_display.insert('end', '\nNuméro OF:\n{}\n'.format(self.currentPart.of))
#         self.text_display.insert('end', '\nChemin du fichier:\n{}'.format(self.imagePath))
#         self.text_display['state'] = 'disabled'
#
#         # Place everything
#         frame.grid(row=0, column=1, padx=10, pady=10, rowspan=4)  #, columnspan=3, rowspan=3)
#         self.canvas.grid(row=0, column=1, sticky=tk.N + tk.S + tk.E + tk.W)
#         self.btn_lancer.grid(row=0, column=2, padx=10, pady=10)
#         # self.btn_trigger.grid(row=1, column=2, padx=10, pady=10)
#         self.text_display.grid(row=2, column=2, padx=10, pady=10)
#
#         self.root.mainloop()
#
#     def setDefectWindowLocalization(self):
#         self.window = 'defectLocalization'
#         self.root = tk.Tk()
#         self.root.protocol("WM_DELETE_WINDOW", self.userExit)
#         self.root.title("Contrôle estétique: Localisation sur la pièce")
#
#         # setting up a tkinter canvas with scrollbars
#         frame = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
#         self.canvas = tk.Canvas(frame, bd=0, width=self.image.shape[1], height=self.image.shape[0])
#         self.canvas.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
#         self.pil_defects_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.currentPart.defects_image))
#         self.image_on_canvas = self.canvas.create_image(0, 0, image=self.pil_defects_image)
#         self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
#
#         # mouseclick event
#         self.canvas.bind("<Button 1>", self.toggleQuadrant)
#
#         # Set buttons
#         self.btn_valider = self.getButton(text="Valider localisation", color="green", fcn=lambda *args: self.changeProgramState('next'))
#
#         # Text that displays the reference piece
#         self.text_display = tk.Text(self.root, state='normal', width=20, height=8)
#         self.text_display.tag_configure("right", justify='right')
#         self.text_display.insert('end', 'Reference pièce:\n{}\n'.format(self.currentPart.ref))
#         self.text_display.insert('end', '\nNuméro OF:\n{}'.format(self.currentPart.ref))
#         self.text_display['state'] = 'disabled'
#
#         # Text that displays the current added errors
#         self.errors_display = tk.Text(self.root, state='normal', wrap='none', width=40, height=35)
#         self.errors_display.insert('end', 'État pièce: {} \n'.format(self.currentPart.partStatus))
#         self.errors_display.insert('end', 'Total défauts: {}\n'.format(len(self.currentPart.defects)))
#         self.errors_display.insert('end', 'Défaut       Type       Gravité Surface\n')
#         for d in self.currentPart.defects:
#             thisType = d.type
#             l = 15
#             while len(thisType) > 24:
#                 thisType = "".join([s[:l] for s in d.type.split()])
#                 l -= 1
#
#             self.errors_display.insert('end', '{:^3s} {:^24s} {:^3s} {:^3s}\n'.format(str(d.id), thisType, d.score, str(len(d.quadrants))))
#
#         self.errors_display['state'] = 'disabled'
#
#         # Place everything
#         self.errors_display.grid(row=0, column=0, padx=10, pady=10, rowspan=4)
#         frame.grid(row=0, column=1, padx=10, pady=10, rowspan=4)
#         self.canvas.grid(row=0, column=1, sticky=tk.N + tk.S + tk.E + tk.W)
#         self.text_display.grid(row=0, column=2, padx=10, pady=10)
#         self.btn_valider.grid(row=1, column=2, padx=10, pady=10)
#
#         self.updateCanvas()
#
#         self.root.mainloop()
#
#     def setDefectWindow1(self):
#         self.currentPart.partStatus = "OK"
#         self.window = 'defect1'
#         self.root = tk.Tk()
#         self.root.protocol("WM_DELETE_WINDOW", self.userExit)
#         self.root.title("Étape 1 – Étiquetage")
#
#         # Text that displays the reference piece
#         text_display = tk.Text(self.root, state='normal', width=20, height=8)
#         text_display.tag_configure("right", justify='right')
#         text_display.insert('end', 'Reference pièce:\n{}\n'.format(self.currentPart.ref))
#         text_display.insert('end', '\nNuméro OF:\n{}'.format(self.currentPart.of))
#         text_display['state'] = 'disabled'
#
#         # Set buttons
#         self.btn_okko = self.getButton(text=" Renseigner l’état OK ou KO de la pièce", color="gray", fcn=self.changeBtnStatus)
#         btn_next = self.getButton(text="Suivant\n->", color="blue", fcn=lambda *args: self.changeProgramState('next'))
#
#         # Place everything
#         text_display.grid(row=0, column=0, padx=10, pady=10, rowspan=2)
#         self.btn_okko.grid(row=0, column=1, padx=10, pady=10)
#         btn_next.grid(row=1, column=1, padx=10, pady=10)
#
#         self.root.mainloop()
#
#     def setDefectWindow2_0(self):
#         self.window = 'defectT2_0'
#         self.root = tk.Tk()
#         self.root.protocol("WM_DELETE_WINDOW", self.userExit)
#         self.root.title("Étape 2 – Renseignement ")
#
#         # Set labels
#         l0 = tk.Label(self.root, text="Choisissez le type et la gravité du défaut")
#         l1 = tk.Label(self.root, text="Type défaut:")
#         l2 = tk.Label(self.root, text="Gravité défaut:")
#
#         # Set comboboxes
#         self.comboType = TTK.Combobox(self.root, state="readonly", values=self.possibleTypes)
#         self.comboScore = TTK.Combobox(self.root, state="readonly", values=self.possibleScores)
#
#         # Set buttons
#         btn_next = self.getButton(text="Localiser le défaut sur la pièce", color="blue", fcn=lambda *args: self.changeProgramState('next'))
#         btn_end = self.getButton(text="Aucun défaut sur pièce", color="green", fcn=lambda *args: self.changeProgramState('end'))
#
#         # Place everything
#         l0.grid(row=0, column=0, padx=10, pady=10, columnspan=4)
#         l1.grid(row=1, column=0, padx=10, pady=10, columnspan=2)
#         l2.grid(row=2, column=0, padx=10, pady=10, columnspan=2)
#         self.comboType.grid(row=1, column=2, padx=10, pady=10, columnspan=2)
#         self.comboScore.grid(row=2, column=2, padx=10, pady=10, columnspan=2)
#         btn_next.grid(row=3, column=2, padx=10, pady=10, columnspan=2)
#
#         if self.programStatus != 'newDefect':
#             btn_end.grid(row=3, column=0, padx=10, pady=10, columnspan=2)
#
#         self.root.mainloop()
#
#     def setDefectWindow2_1(self):
#         self.window = 'defectT2_1'
#         self.root = tk.Tk()
#         self.root.protocol("WM_DELETE_WINDOW", self.userExit)
#         self.root.title("Étape 2 – Renseignement")
#
#         # setting up a tkinter canvas with scrollbars
#         frame = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
#         self.canvas = tk.Canvas(frame, bd=0, width=self.image.shape[1], height=self.image.shape[0])
#         self.canvas.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
#         self.pil_defects_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.currentPart.defects_image))
#         self.image_on_canvas = self.canvas.create_image(0, 0, image=self.pil_defects_image)
#         self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
#
#         # Set labels
#         l0 = tk.Label(self.root, text="Défaut {}/{}\nlocalisé\n".format(self.currentPart.currentDefectId + 1, len(self.currentPart.defects)), font=('Helvetica', '16'))
#         l1 = tk.Label(self.root, text="Type\ndéfaut", font=('Helvetica', '16'))
#         l2 = tk.Label(self.root, text="Score\ndéfaut", font=('Helvetica', '16'))
#
#         # Set comboboxes
#         self.comboType = TTK.Combobox(self.root, state="readonly", values=self.possibleTypes)
#         self.comboType.current(self.possibleTypes.index(self.currentPart.defects[self.currentPart.currentDefectId].type))
#         self.comboType.bind("<<ComboboxSelected>>", self.textBoxUpdate)
#
#         self.comboScore = TTK.Combobox(self.root, state="readonly", values=self.possibleScores)
#         self.comboScore.current(self.possibleScores.index(self.currentPart.defects[self.currentPart.currentDefectId].score))
#         self.comboScore.bind("<<ComboboxSelected>>", self.textBoxUpdate)
#
#         self.comboCurrentDefect = TTK.Combobox(self.root, state="readonly", values=["{}".format(i) for i in range(1, len(self.currentPart.defects) + 1)])
#         self.comboCurrentDefect.current(self.currentPart.currentDefectId)
#         self.comboCurrentDefect.bind("<<ComboboxSelected>>", self.textBoxUpdate)
#
#         # Set buttons
#         btn_modify = self.getButton(text="Modifier la localisation du défaut", color="blue", fcn=lambda *args: self.changeProgramState('next'))
#         btn_delete = self.getButton(text="Supprimer ce défaut", color="red", fcn=lambda *args: self.changeProgramState('delete'))
#         btn_end = self.getButton(text="Tous défauts renseignés", color="green", fcn=lambda *args: self.changeProgramState('end'))
#         btn_new = self.getButton(text="Renseigner autre défaut\n->", color="blue", fcn=lambda *args: self.changeProgramState('newDefect'))
#
#         # Place everything
#         l0.grid(row=0, column=0, padx=10, pady=10)
#         l1.grid(row=1, column=0, padx=10, pady=10)
#         l2.grid(row=2, column=0, padx=10, pady=10)
#         self.comboType.grid(row=1, column=1, padx=10, pady=10)
#         self.comboScore.grid(row=2, column=1, padx=10, pady=10)
#         self.comboCurrentDefect.grid(row=0, column=1, padx=10, pady=10)
#         btn_modify.grid(row=0, column=2, padx=10, pady=10)
#         btn_delete.grid(row=1, column=2, padx=10, pady=10)
#         btn_end.grid(row=3, column=0, padx=10, pady=10)
#         btn_new.grid(row=3, column=2, padx=10, pady=10)
#         frame.grid(row=0, column=4, padx=10, pady=10, rowspan=4)
#         self.canvas.grid(row=0, column=4, sticky=tk.N + tk.S + tk.E + tk.W)
#
#         self.updateCanvas()
#
#         self.root.mainloop()
#
#     def textBoxUpdate(self, event):
#         self.currentPart.defects[self.currentPart.currentDefectId].type = self.comboType.get()
#         self.currentPart.defects[self.currentPart.currentDefectId].score = self.comboScore.get()
#
#         if self.currentPart.currentDefectId != int(self.comboCurrentDefect.get()) - 1:
#             self.currentPart.currentDefectId = int(self.comboCurrentDefect.get()) - 1
#             self.comboType.current(self.possibleTypes.index(self.currentPart.defects[self.currentPart.currentDefectId].type))
#             self.comboScore.current(self.possibleScores.index(self.currentPart.defects[self.currentPart.currentDefectId].score))
#             self.updateCanvas()
#
#     def showWarning(self, text):
#         root = tk.Tk()
#         root.withdraw()
#         messagebox.showwarning("Avertissement", text)
#
#     def changeProgramState(self, s):
#         self.programStatus = s
#         if s == 'trigger':
#             self.imagePath = filedialog.askopenfilename(initialdir=self.inputDir, title="Sélectionner un fichier", filetypes=(("fichiers {}".format(self.configParams['imageExtension']), "*.{}".format(self.configParams['imageExtension'])), ("all files", "*.*")))
#             self.fileName = ntpath.basename(self.imagePath)
#             if self.fileName == '':
#                 return
#             s = self.fileName.split('_')
#             self.currentPart = Part(ref=s[0], of=s[1])
#             self.gray = cv2.imread(self.imagePath, cv2.IMREAD_GRAYSCALE)
#             self.resizingRatio = self.imageSize / max(self.gray.shape[0], self.gray.shape[1])
#             self.gray = cv2.resize(self.gray, (int(self.gray.shape[1] * self.resizingRatio), int(self.gray.shape[0] * self.resizingRatio)), interpolation=cv2.INTER_AREA)
#             self.image = cv2.cvtColor(self.gray, cv2.COLOR_GRAY2RGB)
#             self.currentPart.defects_image = self.getGridImage()
#
#         if s == 'next':
#             if 'defectLocalization' in self.window:
#                 if len(self.currentPart.defects[self.currentPart.currentDefectId].quadrants) == 0:
#                     self.showWarning("Il n'est pas possible de créer une erreur avec un emplacement sélectionné. Si vous souhaitez effacer cette erreur, sélectionnez un emplacement et supprimez-le à l'étape suivante.")
#                     # root = tk.Tk()
#                     # root.withdraw()
#                     # messagebox.showwarning("Avertissement", "Il n'est pas possible de créer une erreur avec un emplacement sélectionné. Si vous souhaitez effacer cette erreur, sélectionnez un emplacement et supprimez-le à l'étape suivante.")
#                     return
#
#             elif 'defectT2' in self.window:
#                 if self.comboType.get() == "" or self.comboScore.get() == "":
#                     self.showWarning("Il n'est pas possible de créer une erreur sans une valeur de type ou de gravité du défaut.")
#                     # root = tk.Tk()
#                     # root.withdraw()
#                     # messagebox.showwarning("Avertissement", "Il n'est pas possible de créer une erreur sans une valeur de type ou de gravité du défaut.")
#                     return
#
#                 if self.window == 'defectT2_0':
#                     self.currentPart.newDefect(type=self.comboType.get(), score=self.comboScore.get())
#
#                 if self.window == 'defectT2_1':
#                     self.currentPart.defects[self.currentPart.currentDefectId].type = self.comboType.get()
#                     self.currentPart.defects[self.currentPart.currentDefectId].score = self.comboScore.get()
#
#             elif 'defect1' in self.window:
#                 if self.btn_okko['bg'] == 'gray':
#                     self.showWarning("Il n'est pas possible de passer à l'étape suivante sans avoir sélectionné une valeur de pièce OK ou KO en appuyant sur le bouton gris.")
#                     return
#
#         if s == 'delete':
#             self.currentPart.removeDefect(self.currentPart.currentDefectId)
#
#         self.root.destroy()
#         self.root.quit()
#
#     def changeBtnStatus(self):
#         if self.btn_okko['bg'] == 'green':
#             self.btn_okko.configure(bg="red", text='État de la    pièce: KO')
#             self.currentPart.partStatus = "KO"
#         else:
#             self.btn_okko.configure(bg="green", text='État de la    pièce: OK')
#             self.currentPart.partStatus = "OK"
#
#     def getButton(self, text, color, fcn, w=12, h=3, fontSize=16):
#         return tk.Button(self.root, text=text, width=w, height=h, command=fcn, bg=color, font=('Helvetica', '{}'.format(fontSize)), wraplength=160, padx=2, pady=2)
#
#     def getQuadrant(self, x, y):
#         yq = int(x / (self.image.shape[1] / self.w_partitions))
#         xq = int(y / (self.image.shape[0] / self.h_partitions))
#         return np.asarray([yq, xq])
#
#     def plotDefectGrid(self, defect, img, screenShot=False):
#         if screenShot:
#             color = (0, 255, 255)
#         else:
#             color = (255, 255, 0) if defect.id != self.currentPart.currentDefectId else (255, 0, 0)
#
#         vertices = np.zeros((len(defect.quadrants) * 4, 2), dtype='int')
#         i = 0
#         for q in defect.quadrants:
#             yc, xc = self.partitions_vertices['{},{}'.format(q[0], q[1])]  # q = [col, row]
#             # horizontal lines
#             if not np.any(np.all(np.asarray([q[0] - 1, q[1]]) == defect.quadrants, axis=1)):
#                 cv2.line(img, (yc[0], xc[0]), (yc[0], xc[1]), color, 3)
#             if not np.any(np.all(np.asarray([q[0] + 1, q[1]]) == defect.quadrants, axis=1)):
#                 cv2.line(img, (yc[1], xc[1]), (yc[1], xc[0]), color, 3)
#
#             # vertical lines
#             if not np.any(np.all(np.asarray([q[0], q[1] - 1]) == defect.quadrants, axis=1)):
#                 cv2.line(img, (yc[0], xc[0]), (yc[1], xc[0]), color, 3)
#             if not np.any(np.all(np.asarray([q[0], q[1] + 1]) == defect.quadrants, axis=1)):
#                 cv2.line(img, (yc[1], xc[1]), (yc[0], xc[1]), color, 3)
#
#             vertices[i] = [yc[0], xc[0]]
#             vertices[i + 1] = [yc[1], xc[1]]
#             vertices[i + 2] = [yc[0], xc[1]]
#             vertices[i + 3] = [yc[1], xc[0]]
#             i += 4
#
#         maxv = vertices[np.argmax(np.sum(vertices, axis=1))]
#         cv2.putText(img, "{}".format(defect.id + 1), (maxv[0] + 5, maxv[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, .5, color, 2, cv2.LINE_AA)
#
#         return img
#
#     def getUpdatedImage(self, screenShot=False):
#         img = self.getGridImage()
#         for defect in self.currentPart.defects:
#             if len(defect.quadrants) > 0:
#                 img = self.plotDefectGrid(defect, img, screenShot)
#
#         return img
#
#     def updateCanvas(self):
#         self.newImg = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.getUpdatedImage()))
#         self.canvas.itemconfig(self.image_on_canvas, image=self.newImg)
#
#     # function to be called when mouse is clicked
#     def toggleQuadrant(self, event):
#         q = self.getQuadrant(event.x, event.y)
#
#         if len(self.currentPart.defects[self.currentPart.currentDefectId].quadrants) == 0:
#             self.currentPart.defects[self.currentPart.currentDefectId].quadrants.append(q)
#         else:
#             if not np.any(np.all(q == np.asarray(self.currentPart.defects[self.currentPart.currentDefectId].quadrants), axis=1)) and np.any(np.all(np.abs(q - np.asarray(self.currentPart.defects[self.currentPart.currentDefectId].quadrants)) <= 1, axis=1)):
#                 self.currentPart.defects[self.currentPart.currentDefectId].quadrants.append(q)
#             else:
#                 self.currentPart.defects[self.currentPart.currentDefectId].quadrants = list(np.asarray(self.currentPart.defects[self.currentPart.currentDefectId].quadrants)[np.any(q != np.asarray(self.currentPart.defects[self.currentPart.currentDefectId].quadrants), axis=1)])
#
#         self.updateCanvas()
#
#     def getPartitionsVertices(self):
#         w, h = self.gray.shape[1], self.gray.shape[0]
#         partitions_vertices = dict()
#         wp = w / self.w_partitions
#         hp = h / self.h_partitions
#         for y in range(self.w_partitions):
#             for x in range(self.h_partitions):
#                 partitions_vertices['{},{}'.format(y, x)] = [[int(wp * y),  int(wp * (y + 1))], [int(hp * x),  int(hp * (x + 1))]]
#
#         self.partitions_vertices = partitions_vertices
#
#     def getGridImage(self):
#         self.getPartitionsVertices()
#         img = self.image.copy()
#         wp = img.shape[1] / self.w_partitions
#         hp = img.shape[0] / self.h_partitions
#
#         for i in range(1, self.w_partitions):
#             cv2.line(img, (int(wp * i), 0), (int(wp * i), img.shape[0]), (255, 255, 255), 1, 4)
#
#         for i in range(1, self.h_partitions):
#             cv2.line(img, (0, int(hp * i)), (img.shape[1], int(hp * i)), (255, 255, 255), 1, 4)
#
#         return img
#
#     def setFileName(self):
#         # Set output file name
#         dt = datetime.datetime.now().strftime('%y%m%d_%H%M')
#         self.fileName = '{}/{}_{}_{}x{}_{}_{}_{}_{}'.format(self.outputDir,
#                                                            self.currentPart.ref,
#                                                            self.currentPart.of,
#                                                            self.image.shape[0],
#                                                            self.image.shape[1],
#                                                            self.w_partitions,
#                                                            self.h_partitions,
#                                                            dt,
#                                                            self.currentPart.partStatus)
#
#
#     def writePartInfo(self):
#         # Open file
#         f = open('{}.txt'.format(self.fileName), "w+")
#
#         # Write info
#         f.write("ID TYPE SCORE QUADRANTS\n")
#         for d in self.currentPart.defects:
#             q = "{}".format(d.quadrants).replace(" ", "")
#             l = "{} {} {} {}\n".format(d.id, d.type.replace(" ", "_"), d.score, q)
#             l = l.replace("array(", "").replace(")", "")
#             f.write(l)
#
#         f.close()
#
#     def createScreenShot(self):
#         img = self.getUpdatedImage(screenShot=True)
#         img = cv2.resize(img, (int(img.shape[1] / self.resizingRatio), int(img.shape[0] / self.resizingRatio)), interpolation=cv2.INTER_AREA)
#         textBox = np.zeros((img.shape[0], 800, 3))
#         x, y = 0, 50
#         color = (255, 255, 255)
#         text = ['Etat piece: {}'.format(self.currentPart.partStatus),
#                 'Total defauts: {}'.format(len(self.currentPart.defects))]
#
#         if len(self.currentPart.defects) > 0:
#             text.append('Defaut Type Gravite Surface')
#             for d in self.currentPart.defects:
#                 text.append('{} {} {} {}'.format(d.id, d.type, d.score, len(d.quadrants)))
#
#         for l in text:
#             cv2.putText(textBox, l, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)
#             y += 50
#
#         img = np.concatenate((img, textBox), axis=1)
#         cv2.imwrite('{}.png'.format(self.fileName), img)
#
#     def __call__(self):
#         while True:
#             if self.programStatus == 'break': return
#             time.sleep(0.5)
#
#             self.setWaitingWindow()
#
#             # for image_path in glob.glob(os.path.join(self.inputDir, '*{}.{}'.format(self.configParams['imageToShowExtension'], self.configParams['imageExtension']))):
#             #     self.imagePath = image_path
#             #     fileName = ntpath.basename(image_path)
#             #     s = fileName.split('_')
#             #     self.currentPart = Part(ref=s[0], of=s[1])
#             #     self.gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
#             #     self.resizingRatio = self.imageSize / max(self.gray.shape[0], self.gray.shape[1])
#             #     self.gray = cv2.resize(self.gray, (int(self.gray.shape[1] * self.resizingRatio), int(self.gray.shape[0] * self.resizingRatio)), interpolation=cv2.INTER_AREA)
#             #     self.image = cv2.cvtColor(self.gray, cv2.COLOR_GRAY2RGB)
#             #     self.currentPart.defects_image = self.getGridImage()
#
#             # State diagram
#             if self.programStatus == 'break': return
#             self.setMainWindow()
#             if self.programStatus == 'break': return
#             self.setDefectWindow1()
#             if self.programStatus == 'next':
#                 while self.programStatus != 'end':
#                     if self.programStatus == 'newDefect' or len(self.currentPart.defects) == 0:
#                         self.setDefectWindow2_0()
#                         if self.programStatus in ['end', 'break']: break
#                         self.programStatus = 'next'
#                     if not self.programStatus == 'delete':
#                         self.setDefectWindowLocalization()
#                     if self.programStatus == 'break': return
#                     self.setDefectWindow2_1()
#
#             if self.programStatus == 'break': return
#             self.setFileName()
#             self.writePartInfo()
#             self.createScreenShot()
#             if self.removeInputDirImages:
#                 for ip in glob.glob(os.path.join(self.inputDir, self.fileName.replace(self.configParams['imageToShowExtension'], "*"))):
#                     fn = ntpath.basename(ip)
#                     shutil.move(ip, "{}/{}".format(self.labeledDir, fn))