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
        self.interior = interior = tk.Frame(canvas, highlightthickness=2, highlightbackground="black")
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
        self.vc_data = dict()
        self.manual_exit = False
        self.tools_data = tools_data
        self.active_tables = dict()

        self.operation_parameters = dict()

    def __call__(self, *args, **kwargs):
        self.root.mainloop()

    def get_button(self, text, color, fcn, w=12, h=3, font_size=16, padx=2, pady=2):
        return tk.Button(self.root, text=text, width=w, height=h, command=fcn, bg=color, font=('Helvetica', f'{font_size}'),
                         wraplength=160, padx=padx, pady=pady)

    def change_program_state(self, s, key=None, root=None):
        self.res = s

        if s == 'add':
            self.append_vc_row(key, root=root)

        elif "file_" in s:


            # vc = self.root.children[f"!entry{n_vc}"].get()
            filename = tk.filedialog.askopenfilename(initialdir="/", title="Sélectionner un fichier")
            if filename != "":
                n = int(s.replace("file_", "")) + 1
                # n_vc = (n - 1) * 2 + 1
                # n_pc = (n - 1) * 2 + 2

                n_but = '' if n == 1 else n
                # self.root.children[f"!button{n_file}"].configure(fg="green", text=filename)
                # root.children['vc_parameters'].children[f"!button{n}"].configure(fg="green", text=filename)
                # self.vc_data[n].children["!button"].configure(fg="green", text=filename)

                self.active_tables['vc_parameters'].children['!canvas'].children['!frame'].children[f"!button{n_but}"].configure(fg="green", text=filename)
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

    def set_root(self, key):
        if key is None:
            return self.root
        elif type(key) is str:
            return self.active_tables[key]
        else:
            return key

    def set_operation_window(self):
        # Set Vc input parameters table
        self.active_tables["input_parameters"] = tk.Frame(self.root, name="input_parameters", highlightthickness=2, highlightbackground="black")

        self.set_vc_headers(["Paramètres d’entrée", "Valeurs utilisées"], 'vc_headers_1', self.active_tables["input_parameters"])
        self.append_entry_row("engagement_Axial", "Engagement axial ap (mm) ", root=self.active_tables["input_parameters"])
        self.append_entry_row("engagement_radial", "Engagement radial ae (mm)", root=self.active_tables["input_parameters"])
        self.append_entry_row("avance_dent", "Avance par dent fz (mm/tr) ", root=self.active_tables["input_parameters"])
        self.active_tables["input_parameters"].pack(padx=15, pady=15)

        # Set Vc input parameters table
        self.active_tables["vc_parameters"] = VerticalScrolledFrame(self.root)

        # Set headers
        self.set_vc_headers(["Mesure n°", "Vitesse de coupe Vc (m/min)", "Fichier de mesure", "Pc (W)"], 'vc_headers_2', self.active_tables["vc_parameters"].interior)

        # Set first row
        self.append_vc_row("vc_parameters", self.active_tables["vc_parameters"].interior)

        self.active_tables["vc_parameters"].pack(padx=15, pady=15)

        # Set buttons
        self.active_tables["buttons"] = tk.Frame(self.root, name="buttons")
        self.active_tables["buttons"].pack(padx=15, pady=15)
        self.append_buttons("buttons", root=self.active_tables["buttons"], root_table=self.active_tables["vc_parameters"].interior)

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
        btn_next = tk.Button(row, text="Suivant", command=lambda *args: self.change_program_state("next"), bg="green", padx=10, pady=5, font='Helvetica 11 bold')
        btn_add = tk.Button(row, text="Ajouter une autre ligne", command=lambda *args: self.change_program_state("add", key=key, root=root_table), bg="light sky blue", padx=10, pady=5, font='Helvetica 11 bold')

        # btn_next.grid(row=0, column=0, pady=20, padx=5, columnspan=2)
        # btn_add.grid(row=0, column=2, pady=20, padx=5, columnspan=2)

        btn_next.pack(side=tk.LEFT, padx=20, pady=5)
        btn_add.pack(side=tk.LEFT, padx=20, pady=5)

    def append_entry_row(self, key, text, root=None):
        # row = tk.Frame(self.set_root(root), name=key, highlightthickness=1, highlightbackground="black")
        lab = tk.Label(self.set_root(root), width=22, text=text+": ")  #, padx=10, pady=5)
        ent = tk.Entry(self.set_root(root), width=22)
        # row.pack(side=tk.TOP, fill=tk.X)
        # lab.pack(side=tk.LEFT, padx=10, pady=5)
        # ent.pack(side=tk.LEFT, padx=10, pady=5)  #, expand=tk.YES, fill=tk.X)

        lab.grid(row=len(self.operation_parameters)+1, column=0)
        ent.grid(row=len(self.operation_parameters)+1, column=1)

        # row.grid(row=len(self.operation_parameters))

        self.operation_parameters[key] = ent

    def set_vc_headers(self, headers, key, root=None):
        # row = tk.Frame(self.set_root(root), name=key, highlightthickness=1, highlightbackground="black")
        # # row.pack(side=tk.TOP, fill=tk.X)
        # row.grid(row=0)

        for i, h in enumerate(headers):
            tk.Label(self.set_root(root), text=h, width=22, font='Helvetica 11 bold', bg="gray").grid(row=0, column=i)  #.pack(side=tk.LEFT)
            # tk.Label(row, text=h, font='Helvetica 11 bold').pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)

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
        # row = tk.Frame(self.set_root(root), name=key)
        # row = tk.Frame(self.set_root(root), highlightthickness=1, highlightbackground="black")
        # row.pack(side=tk.TOP, fill=tk.X, padx=20)

        # row = VcRow(self.set_root(root))

        n = len(self.vc_data)
        self.vc_data[f"{n}"] = dict()
        tk.Label(self.set_root(root), text=f"{n}").grid(row=n+1, column=0, pady=5, padx=5)
        self.vc_data[f"{n}"]['ent_vc'] = tk.Entry(self.set_root(root)).grid(row=n+1, column=1, pady=5, padx=5)
        self.vc_data[f"{n}"]['btn_file'] = tk.Button(self.set_root(root), text="Parcourir", command=lambda *args: self.change_program_state(f"file_{n}", key)).grid(row=n+1, column=2, pady=5, padx=5)
        self.vc_data[f"{n}"]['ent_pc'] = tk.Entry(self.set_root(root)).grid(row=n+1, column=3, pady=5, padx=5)

        # row.pack(side=tk.TOP, fill=tk.X, padx=20)
        # row.pack(padx=20)
        # row.grid(row=n+1)

        # row.label = tk.Label(row, text=f"{n}").pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)
        # row.ent_vc = tk.Entry(row).pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)
        # row.btn_file = tk.Button(row, text="Parcourir", command=lambda *args: self.change_program_state(f"file_{n}", key, root=root)).pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)
        # row.ent_pc = tk.Entry(row).pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)

        # self.vc_data[f"{n}"] = [ent_vc, btn_file, ent_pc, ""]
        # self.vc_data[f"{n}"] = row

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