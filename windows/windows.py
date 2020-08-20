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

from utils.utils import load_tools_data


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
    def __init__(self, app_name, **kwargs):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.user_exit)
        self.root.title(app_name)

        if 'window_title' in kwargs:
            tk.Label(self.root, text=kwargs['window_title'], padx=5, pady=5, font='Helvetica 15 bold').pack(pady=15)

        self.res = "ini"
        self.vc_data = dict()
        self.manual_exit = False
        self.tools_data = []
        self.available_operations = kwargs['available_operations'] if 'available_operations' in kwargs else None
        self.active_tables = dict()

        self.operation_parameters = dict()
        self.data = dict()

    def __call__(self, *args, **kwargs):
        self.root.mainloop()

    def get_button(self, text, **kwargs):  # fcn=None, color=None, root=None, w=12, h=3, font_size=11, padx=10, pady=5, bold=False):
        root = kwargs['root'] if 'root' in kwargs else self.root
        bold = ' bold' if 'bold' in kwargs else ''
        color = kwargs['color'] if 'color' in kwargs else ''
        w = 12 if 'w' not in kwargs else kwargs['w']
        h = 3 if 'h' not in kwargs else kwargs['h']
        font_size = 11 if 'font_size' not in kwargs else kwargs['font_size']
        padx = 10 if 'padx' not in kwargs else kwargs['padx']
        pady = 5 if 'pady' not in kwargs else kwargs['pady']

        return tk.Button(root, text=text, width=w, height=h, command=kwargs['fcn'], bg=color, font=f"Helvetica {font_size}{bold}", wraplength=160, padx=padx, pady=pady)

    def get_data(self, items):
        res = dict()
        for key, widget in items:
            if 'label' not in key:
                if key == 'date':
                    vals = []
                    for w in widget.children:
                        vals.append(f"{widget.children[w].get()}")

                    res[key] = ('/'.join(vals, ))

                elif 'Combobox' in str(type(widget)) or 'Entry' in str(type(widget)):
                    res[key] = widget.get()
                elif 'Label' in str(type(widget)):
                    res[key] = widget['text']
                else:
                    res[key] = widget['text']

        return res

    def change_program_state(self, *args, **kwargs):
        for action in kwargs['actions']:
            if action == 'add_dynamic_row':
                self.append_dynamic_row(kwargs['keys'], root=kwargs['action_root'][1])

            elif action == 'select_file':
                filename = tk.filedialog.askopenfilename(initialdir="/", title="Sélectionner un fichier")
                if filename != "":
                    kwargs['action_root'].children[f"fichier de mesure_{kwargs['file'] + 1}"].configure(fg="green", text=filename)

            elif action == "get_data":
                if len(kwargs['action_root']) > 1:
                    for table in kwargs['action_root']:
                        self.data.update(self.get_data(table.children.items()))
                else:
                    self.data = self.get_data(kwargs['action_root'].children.items())

            elif action == "compute_vc":
                pass

            elif action == "quit" or action == "next":
                self.root.quit()

    def append_date(self, root=None, row_idx=0):
        from datetime import date

        root = self.root if root is None else root
        today = date.today()

        date_cell = tk.Frame(root, name='date')
        lab = tk.Label(root, width=25, text="Date du traitement :", padx=5, pady=5)

        day = tk.ttk.Combobox(date_cell, values=[i for i in range(1, 32)], width=2, name='day')
        day.current(today.day - 1)

        month = tk.ttk.Combobox(date_cell, values=["janvier",
                                                   "février",
                                                   "mars",
                                                   "avril",
                                                   "mai",
                                                   "juin",
                                                   "juillet",
                                                   "août",
                                                   "septembre",
                                                   "octobre",
                                                   "novembre",
                                                   "décembre"],
                                state="readonly",
                                width=8,
                                name='month')

        month.current(today.month - 1)

        year = tk.ttk.Combobox(date_cell, values=[i for i in range(2020, 2040)], width=4, name='year')
        year.current(today.year - 2020)

        lab.grid(row=row_idx, column=0)
        date_cell.grid(row=row_idx, column=1)

        day.pack(side=tk.LEFT, pady=1)
        month.pack(side=tk.LEFT, padx=1, pady=1)
        year.pack(side=tk.LEFT, expand=tk.YES, pady=1)

    def set_root(self, key):
        if key is None:
            return self.root
        elif type(key) is str:
            return self.active_tables[key]
        else:
            return key

    def operation_cbox_callback(self, eventObject, root):
        root = self.root if root is None else root
        self.tools_data = load_tools_data(eventObject.widget.get())

        root.children['tool']['values'] = list(load_tools_data(eventObject.widget.get()))
        root.children['tool'].current(0)

        diametre = self.tools_data[root.children['tool'].get()][1]
        n_dents = self.tools_data[root.children['tool'].get()][2]

        self.set_tool_parameters(root, diametre, n_dents)

    def tool_cbox_callback(self, eventObject, root):
        root = self.root if root is None else root
        diametre = self.tools_data[eventObject.widget.get()][1]
        n_dents = self.tools_data[eventObject.widget.get()][2]

        self.set_tool_parameters(root, diametre, n_dents)

    def set_tool_parameters(self, root, diametre, n_dents):
        # Set diametre
        root.children['diameter']['text'] = diametre
        # Set nombre de dents
        root.children['n_teeth']['text'] = n_dents

    def append_combobox_row(self, text, values, fcn, **kwargs):  # root=None, row=0):
        root = kwargs['root'] if 'root' in kwargs else self.root
        row = kwargs['row'] if 'row' in kwargs else 0

        tk.Label(root, width=25, text=text + ": ", padx=5, pady=5).grid(row=row, column=0)

        name = kwargs['name'] if 'name' in kwargs else text.lower()
        cbox = tk.ttk.Combobox(root, values=values, state="readonly", width=22, name=name)
        cbox.bind("<<ComboboxSelected>>", lambda event, root=root: fcn(event, root))
        cbox.grid(row=row, column=1)

    def append_buttons(self, keys, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self.root
        root_table = kwargs['root_table'] if 'root_table' in kwargs else None

        btn_next = tk.Button(root, text="Valider", command=lambda **kwargs: self.change_program_state(actions=["get_data", "next"], action_root=root_table), padx=10, pady=5, font='Helvetica 11 bold')
        btn_calculer = tk.Button(root, text="Calculer Pc", command=lambda **kwargs: self.change_program_state(actions=["compute_vc"]), padx=10, pady=5, font='Helvetica 11 bold')
        btn_add = tk.Button(root, text="Ajouter une autre ligne", command=lambda **kwargs: self.change_program_state(keys=keys, actions=["add_dynamic_row"], action_root=root_table), padx=10, pady=5, font='Helvetica 11 bold')

        btn_next.grid(row=0, column=0, padx=20, pady=5)
        btn_calculer.grid(row=0, column=2, padx=20, pady=5)
        btn_add.grid(row=0, column=4, padx=20, pady=5)

    def append_entry_row(self, text, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self.root
        row = kwargs['row'] if 'row' in kwargs else 0

        tk.Label(root, width=25, text=text + " :").grid(row=row, column=0)

        ent_name = kwargs['ent_name'] if 'ent_name' in kwargs else f"label_r{row}c1"
        tk.Entry(root, width=25, name=ent_name).grid(row=row, column=1)

    def set_label_row(self, headers, **kwargs):  # root=None, row=0, bold=True, names=None):
        root = kwargs['root'] if 'root' in kwargs else self.root
        row = kwargs['row'] if 'row' in kwargs else 0

        for i, h in enumerate(headers):
            name = kwargs['names'][i] if 'names' in kwargs else f"label_r{row}c{i}"
            if 'header' in kwargs:
                tk.Label(root, text=h, width=22, font='Helvetica 11 bold', bg='gray', name=name).grid(row=row, column=i)
            else:
                tk.Label(root, text=h, width=22, name=name).grid(row=row, column=i)

    def append_dynamic_row(self, keys, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self.root
        n = len(root.children) // len(keys) - 1
        row = n + 1
        tk.Label(root, text=f"{n}").grid(row=row, column=0, pady=5, padx=5)

        # self.vc_data[f"{n}"] = dict()
        for col_idx, key in enumerate(keys[1:]):
            name = f'{key.lower()}_{row}'

            if key == "Fichier de mesure":
                # self.vc_data[f"{n}"][key] = tk.Button(root, text="Parcourir", command=lambda **kwargs: self.change_program_state(actions=['select_file'], file=n, action_root=root), name=name)
                btn = tk.Button(root, text="Parcourir", command=lambda **kwargs: self.change_program_state(actions=['select_file'], file=n, action_root=root), name=name)
                btn.grid(row=row, column=col_idx + 1, pady=5, padx=5)
            else:
                tk.Label(root, text='...', name=name).grid(row=row, column=col_idx + 1, pady=5, padx=5)

    def quit(self):
        self.root.destroy()
        self.root.quit()

    def user_exit(self):
        selection = tk.messagebox.askquestion("quitter l'application", "Voulez-vous vraiment quitter l'application?", icon='warning')

        if selection == 'yes':
            self.root.quit()


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


def set_general_machining_characteristics(win):
    frame = tk.Frame(win.root, name='general_machining_characteristics')

    # Set text entries
    win.append_combobox_row("Opération", list(win.available_operations), fcn=win.operation_cbox_callback, root=frame, row=1, name='operation')
    win.append_combobox_row("Outil", list(win.tools_data), fcn=win.tool_cbox_callback, root=frame, row=2, name='tool')
    win.set_label_row(["Diamètre :", ""], root=frame, row=3, names=['', 'diameter'])
    win.set_label_row(["Nombre de dents :", ""], root=frame, row=4, names=['', 'n_teeth'])

    win.append_entry_row("Opérateur", row=5, root=frame, ent_name='user_name')
    win.append_date(root=frame, row_idx=6)
    win.append_entry_row("Lubrification", row=7, root=frame, ent_name='lubrication')
    win.append_entry_row("Commentaires", row=8, root=frame, ent_name='comments')

    frame.pack(padx=20, pady=20)

    # Set buttons
    tk.Button(win.root, text=" Suivant ", command=lambda **kwargs: win.change_program_state(actions=["get_data", "next"], action_root=frame), pady=5).pack(pady=10)


def set_operation_window(win, target):
    if 'Vc min' in target:
        entries = ["Engagement axial ap (mm)",
                   "Engagement radial ae (mm)",
                   "Avance par dent fz (mm/tr)"]
        table2_headers = ["Mesure n°", "Vitesse de coupe Vc (m/min)", "Fichier de mesure", "Pc (W)"]
    elif 'f min' in target:
        entries = ["Engagement axial ap (mm)",
                   "Engagement radial ae (mm)",
                   "Vitesse de coupe Vc (m/min)"]
        table2_headers = ["Mesure n°", "Avance par dent fz (mm/tr)", "Fichier de mesure", "Pc (W)"]
    elif 'AD max' in target:
        entries = ["Engagement axial init ap (mm)",
                   "Engagement radial init ae (mm)",
                   "Vitesse de coupe Vc (m/min)",
                   "Épaisseur de coupe h (mm)"]
        table2_headers = ["Mesure n°", "Engagement axial ap(mm)", "Engagement radial ae(mm)", "Fichier de mesure", "Pc(W)", "Statut"]

    # Set Vc input parameters table
    win.active_tables["input_parameters"] = tk.Frame(win.root, name="input_parameters", highlightthickness=2, highlightbackground="black")

    win.set_label_row(["Paramètres d’entrée", "Valeurs utilisées"], root=win.active_tables["input_parameters"], header=True)

    for i, entry in enumerate(entries):
        win.append_entry_row(entry, row=i+1, root=win.active_tables["input_parameters"])

    win.active_tables["input_parameters"].pack(padx=15, pady=15)

    # Set Vc input parameters table
    win.active_tables["parameters"] = VerticalScrolledFrame(win.root)

    # Set headers
    win.set_label_row(table2_headers, root=win.active_tables["parameters"].interior, header=True)

    # Set first row
    win.append_dynamic_row(table2_headers, root=win.active_tables["parameters"].interior)

    win.active_tables["parameters"].pack(padx=15, pady=15)
    win.active_tables["parameters"].interior.pack(padx=20, pady=15)

    # Set buttons
    win.active_tables["buttons"] = tk.Frame(win.root, name="buttons")
    win.active_tables["buttons"].pack(padx=15, pady=15)
    win.append_buttons(table2_headers, root=win.active_tables["buttons"], root_table=[win.active_tables["input_parameters"], win.active_tables["parameters"].interior])

    # Pack frames
    # for key in win.active_tables.keys():
    #     win.active_tables[key].pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)


def set_user_input_parameters_window(name, target, tools_data, operation):
    win = Window(name, target, tools_data)
    set_operation_window(win, target)

    # if operation == "":
    #     set_general_window(win, operations)
    # else:
    #     if operation == "Fraisage":
    #         set_operation_window(win, target)
    #         # set_fraisage_parameters_table(win)
    #     # elif operation == "Perçage":
    #     #     set_fraisage_parameters(win)
    #     # elif operation == "Tournage":
    #     #     set_fraisage_parameters(win)
    #     # elif operation == "vc_range":
    #     # set_dynamic_entry(win)

    win()

    res = parse_res(win)
    # res = None

    win.quit()

    return res


def set_user_window(app_name, target, **kwargs):
    win = Window(app_name, window_title=target, **kwargs)
    if target == "Caractéristiques de l'usinage":
        set_general_machining_characteristics(win)

    elif "Détermination" in target:
        set_operation_window(win, target)

    win()
    res = win.data
    win.quit()

    return res
