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

    def change_program_state(self, s, keys=None, root=None):
        self.res = s

        if s == 'add':
            self.append_vc_row(keys, root=root)

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

                self.active_tables['parameters'].children['!canvas'].children['!frame'].children[f"!button{n_but}"].configure(fg="green", text=filename)
        elif s == "quit" or s == "next":
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

    def set_operation_window(self, target):
        if 'vcmin' in target:
            title = "Détermination de Vc min"
            entries = ["Engagement axial ap (mm)",
                       "Engagement radial ae (mm)",
                       "Avance par dent fz (mm/tr)"]
            table2_headers = ["Mesure n°", "Vitesse de coupe Vc (m/min)", "Fichier de mesure", "Pc (W)"]
        elif 'fmin' in target:
            title = "Détermination de f min"
            entries = ["Engagement axial ap (mm)",
                       "Engagement radial ae (mm)",
                       "Vitesse de coupe Vc (m/min)"]
            table2_headers = ["Mesure n°", "Avance par dent fz (mm/tr)", "Fichier de mesure", "Pc (W)"]
        elif 'admax' in target:
            title = "Détermination de AD max"
            entries = ["Engagement axial init ap (mm)",
                       "Engagement radial init ae (mm)",
                       "Vitesse de coupe Vc (m/min)",
                       "Épaisseur de coupe h (mm)"]
            table2_headers = ["Mesure n°", "Engagement axial ap(mm)", "Engagement radial ae(mm)", "Fichier de mesure", "Pc(W)", "Statut"]

        tk.Label(self.root, text=title, padx=5, pady=5, font='Helvetica 15 bold').pack(pady=15)

        # Set Vc input parameters table
        self.active_tables["input_parameters"] = tk.Frame(self.root, name="input_parameters", highlightthickness=2, highlightbackground="black")

        self.set_table_headers(["Paramètres d’entrée", "Valeurs utilisées"], self.active_tables["input_parameters"])

        for i, entry in enumerate(entries):
            self.append_entry_row(entry, entry, root=self.active_tables["input_parameters"])

        self.active_tables["input_parameters"].pack(padx=15, pady=15)

        # Set Vc input parameters table
        self.active_tables["parameters"] = VerticalScrolledFrame(self.root)

        # Set headers
        self.set_table_headers(table2_headers, self.active_tables["parameters"].interior)

        # Set first row
        self.append_vc_row(table2_headers, root=self.active_tables["parameters"].interior)

        self.active_tables["parameters"].pack(padx=15, pady=15)
        self.active_tables["parameters"].interior.pack(padx=20, pady=15)

        # Set buttons
        self.active_tables["buttons"] = tk.Frame(self.root, name="buttons")
        self.active_tables["buttons"].pack(padx=15, pady=15)
        self.append_buttons(table2_headers, root=self.active_tables["buttons"], root_table=self.active_tables["parameters"].interior)

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

    def append_buttons(self, keys, root=None, root_table=None):
        # row = tk.Frame(self.set_root(root), name=key)
        # row.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=5)
        btn_next = tk.Button(self.set_root(root), text="Valider", command=lambda *args: self.change_program_state("next"), padx=10, pady=5, font='Helvetica 11 bold')
        btn_calculer = tk.Button(self.set_root(root), text="Calculer Pc", command=lambda *args: self.change_program_state("compute_vc"), padx=10, pady=5, font='Helvetica 11 bold')
        btn_add = tk.Button(self.set_root(root), text="Ajouter une autre ligne", command=lambda *args: self.change_program_state("add", keys=keys, root=root_table), padx=10, pady=5, font='Helvetica 11 bold')

        # btn_next.grid(row=0, column=0, pady=20, padx=5, columnspan=2)
        # btn_add.grid(row=0, column=2, pady=20, padx=5, columnspan=2)

        btn_next.grid(row=0, column=0, padx=20, pady=5)  #.pack(side=tk.LEFT, padx=20, pady=5)
        btn_calculer.grid(row=0, column=2, padx=20, pady=5)
        btn_add.grid(row=0, column=4, padx=20, pady=5)  #.pack(side=tk.LEFT, padx=20, pady=5)

    def append_entry_row(self, key, text, root=None):
        lab = tk.Label(self.set_root(root), width=22, text=text+": ")
        ent = tk.Entry(self.set_root(root), width=22)

        lab.grid(row=len(self.operation_parameters)+1, column=0)
        ent.grid(row=len(self.operation_parameters)+1, column=1)

        self.operation_parameters[key] = ent

    def set_table_headers(self, headers, root=None):
        for i, h in enumerate(headers):
            tk.Label(self.set_root(root), text=h, width=22, font='Helvetica 11 bold', bg="gray").grid(row=0, column=i)

    def append_vc_row(self, keys, root=None):
        n = len(self.vc_data)
        tk.Label(self.set_root(root), text=f"{n}").grid(row=n+1, column=0, pady=5, padx=5)

        self.vc_data[f"{n}"] = dict()
        for col_idx, key in enumerate(keys[1:]):
            print([col_idx, key])
            if key == "Fichier de mesure":
                self.vc_data[f"{n}"][key] = tk.Button(self.set_root(root), text="Parcourir", command=lambda *args: self.change_program_state(f"file_{n}")).grid(row=n+1, column=col_idx+1, pady=5, padx=5)
            else:
                self.vc_data[f"{n}"][key] = tk.Entry(self.set_root(root)).grid(row=n+1, column=col_idx+1, pady=5, padx=5)

        # self.vc_data[f"{n}"]['ent_vc'] = tk.Entry(self.set_root(root)).grid(row=n+1, column=1, pady=5, padx=5)
        # self.vc_data[f"{n}"]['btn_file'] = tk.Button(self.set_root(root), text="Parcourir", command=lambda *args: self.change_program_state(f"file_{n}")).grid(row=n+1, column=2, pady=5, padx=5)
        # self.vc_data[f"{n}"]['ent_pc'] = tk.Entry(self.set_root(root)).grid(row=n+1, column=3, pady=5, padx=5)

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


def set_user_input_parameters_window(target, title, tools_data, operation=''):
    win = Window(target, title, tools_data)

    if operation == "":
        set_general_parameters(win)
    else:
        if operation == "Fraisage":
            win.set_operation_window(target)
            # set_fraisage_parameters_table(win)
        # elif operation == "Perçage":
        #     set_fraisage_parameters(win)
        # elif operation == "Tournage":
        #     set_fraisage_parameters(win)
        # elif operation == "vc_range":
        # set_dynamic_entry(win)

    win()

    # res = parse_res(win)
    res = None

    win.quit()

    return res