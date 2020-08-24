import tkinter as tk
import tkinter.ttk as TTK
from tkinter import messagebox, filedialog
# import cv2
# import PIL.Image, PIL.ImageTk
# import pyautogui
# import os
# import glob
# import ntpath
from datetime import date
# import time
# import sys
# import traceback
# import shutil
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from utils.utils import load_tools_data
from data_manager.data_manager import get_pc_from_machining_file


class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """

    def __init__(self, parent, *args, **kw):
        interior_name = kw['interior_name']
        del kw['interior_name']
        tk.Frame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE, padx=5)
        canvas = tk.Canvas(self, bd=0, highlightthickness=2, yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas, highlightthickness=2, highlightbackground="black", name=interior_name)
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


class GraphFrame(tk.Frame):
    def __init__(self, parent, name, data, axis_labels):
        tk.Frame.__init__(self, parent, name=name)

        f = Figure(figsize=(5, 5), dpi=100)
        a = f.add_subplot(111)
        a.plot(data['x'], data['y'])
        a.set_xlabel(axis_labels['x_lab'])
        a.set_ylabel(axis_labels['y_lab'])

        # a.axvline(data['best_range_min'], linewidth=4, color='r')
        # a.axvline(data['best_range_max'], linewidth=4, color='r')

        a.axvspan(data['best_range_min'], data['best_range_max'], facecolor='g', alpha=0.5)

        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


class Window(tk.Tk):
    def __init__(self, app_name, **kwargs):
        tk.Tk.__init__(self)
        self.protocol("WM_DELETE_WINDOW", self.user_exit)
        self.title(app_name)

        if 'window_title' in kwargs:
            tk.Label(self, text=kwargs['window_title'], padx=5, pady=5, font='Helvetica 15 bold').pack(pady=15)

        self.vc_data = dict()
        self.manual_exit = False
        self.tools_data = []
        self.available_operations = kwargs['available_operations'] if 'available_operations' in kwargs else None
        self.general_parameters = kwargs['general_parameters'] if 'general_parameters' in kwargs else None

        self.result = dict()
        self.pcs = dict()

    def __call__(self, *args, **kwargs):
        self.mainloop()

    def show_frame(self, key):
        frame = self.frames[key]
        frame.tkraise()

    def add_frame(self, key, frame):
        self.frames[key] = frame

    def delete_frame(self, key):
        self.frames[key].destroy()

    def get_button(self, text, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        bold = ' bold' if 'bold' in kwargs else ''
        color = kwargs['color'] if 'color' in kwargs else ''
        w = 12 if 'w' not in kwargs else kwargs['w']
        h = 3 if 'h' not in kwargs else kwargs['h']
        font_size = 11 if 'font_size' not in kwargs else kwargs['font_size']
        padx = 10 if 'padx' not in kwargs else kwargs['padx']
        pady = 5 if 'pady' not in kwargs else kwargs['pady']

        return tk.Button(root, text=text, width=w, height=h, command=kwargs['fcn'], bg=color, font=f"Helvetica {font_size}{bold}", wraplength=160, padx=padx, pady=pady)

    @staticmethod
    def get_data(items):
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

    def show_graphic(self, data):
        pcs_win = Window(self.title, window_title='Résultats')

        # DATA FRAME
        data_frame = tk.Frame(pcs_win, name='data_frame')

        # DATA TABLE
        table_frame = VerticalScrolledFrame(data_frame, interior_name='table')
        self.set_label_row(["Vitesse de coupe Vc (m/min)", "Wc (W.min/cm3)"], root=table_frame.interior, header=True)
        for row_idx, (vci, wci) in enumerate(zip(data['x'], data['y'])):
            self.set_label_row([vci, wci], root=table_frame.interior, row=row_idx+1)

        table_frame.interior.pack(side=tk.LEFT, padx=10, pady=10)
        table_frame.pack(side=tk.LEFT, padx=10, pady=10)

        # GRAPH
        axis_labels = {'x_lab': 'Cutting speed (Vc)', 'y_lab': 'Cutting energy (Wc)'}
        graph_frame = GraphFrame(pcs_win, name='graph_frame', data=data, axis_labels=axis_labels)
        graph_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        data_frame.pack(padx=10, pady=10)

        # BUTTONS
        btns_frame = tk.Frame(pcs_win, name='buttons_frame')
        get_data_btn = tk.Button(btns_frame, text="Enregistrer les données", command=lambda **kwargs: self.change_program_state(actions=["get_data"], action_root=[table_frame.interior]), padx=10, pady=5, font='Helvetica 11 bold')
        next_btn = tk.Button(btns_frame, text="Valider", command=lambda **kwargs: self.change_program_state(actions=["next"], action_root=[table_frame.interior]), padx=10, pady=5, font='Helvetica 11 bold')

        get_data_btn.grid(row=1, column=0, padx=10, pady=10)
        next_btn.grid(row=1, column=1, padx=10, pady=10)

        btns_frame.pack(padx=10, pady=10)

        pcs_win()

        validated = False

        return validated

    def compute_h(self, ae, fz):
        d = self.general_parameters['diameter']
        if ae < d:
            h = 2 * fz * np.square((ae / d) * (1 - ae / d))
        else:
            h = fz
            
        return h

    def compute_dynamic_table(self, table, target):
        res = {'x': [], 'y': [], 'statut': []}
        for key, item in table.children.items():
            if 'fichier de mesure' in key:
                row_idx = int(key.replace('fichier de mesure_', ''))

                # just for debugging while not having the real machining file
                # file_path = item['text']
                # pcs.append(get_pc_from_machining_file(file_path))

                if target == 'f min':
                    h = self.compute_h(10 - row_idx)
                    Pc = 10 - row_idx
                    res['x'].append(h)
                    res['y'].append(Pc)
                if target == 'AD max':
                    Pc = 10 - row_idx
                    ap, ae = 2, 1
                    AD = ap * ae
                    statut = 'OK'
                    res['x'].append(Pc)
                    res['y'].append(AD)
                    res['statut'].append(statut)
                if target == 'Q max':
                    AD, Vf, fz, Zu, d, n, Vc = 3, 2, 1, 2, 3, 5, 4
                    # Q = AD * Vf / 1000
                    # or:
                    # Q = AD * fz * Zu * n / 1000
                    # or:
                    Q = AD * fz * Zu * Vc / np.pi / d

                    Pc = 10 - row_idx
                    statut = 'OK'
                    res['x'].append(Pc)
                    res['y'].append(Q)
                    res['statut'].append(statut)
                elif target == 'Vc min':
                    Vc = row_idx - 1
                    Pc = np.exp(-row_idx)
                    res['x'].append(Vc)
                    res['y'].append(Pc)

        dydx = np.diff(res['y']) / np.diff(res['x'])
        res['best_range_min'] = np.argmin(dydx) + 1
        res['best_range_max'] = res['best_range_min'] - 1
        print(dydx)

        return res

    def dynamic_table_validation(self, table):
        target = str(table)[str(table).rfind('Détermination de ') + 17:].lower()

        dynamic_table_values = self.compute_dynamic_table(table, target)

        if target in ['Vc min', 'f min']:
            self.show_graphic(dynamic_table_values)
        elif target in ['AD max', 'Q max']:
            result = np.max(dynamic_table_values['y'])

        if validated:
            target_parameter = str(table)[str(table).rfind('Détermination de ') + 17:].lower()
            self.pcs[target_parameter] = pcs

    def change_program_state(self, *args, **kwargs):
        for action in kwargs['actions']:
            if action == 'add_dynamic_row':
                dynamic_parameters = [i for i in kwargs['action_root'] if 'dynamic' in str(i)][0]
                self.append_dynamic_row(kwargs['keys'], root=dynamic_parameters)

            elif action == 'select_file':
                filename = tk.filedialog.askopenfilename(initialdir="/", title="Sélectionner un fichier")
                if filename != "":
                    n = kwargs['file'] + 1

                    # Set green and text filename in button
                    kwargs['action_root'].children[f"fichier de mesure_{n}"].configure(fg="green", text=filename)

                    # Set Pc (W)
                    # pc = get_pc_from_machining_file(filename)
                    pc = np.random.random()
                    kwargs['action_root'].children[f"pc (w)_{n}"].configure(text=pc)

                    # Set dynamic parameters columns values
                    dynamic_param_names = [param_name for param_name in kwargs['action_root'].children if (f'_{n}' in param_name and 'fichier de mesure' not in param_name and 'pc (w)' not in param_name)]

                    for dynamic_param_name in dynamic_param_names:
                        # dynamic_param_name = f"{kwargs['action_root'].children['label_r0c1']['text'].lower()}_{n}"
                        kwargs['action_root'].children[dynamic_param_name].configure(text=f'{dynamic_param_name}')

            elif action == "get_data":
                if len(kwargs['action_root']) > 1:
                    for table in kwargs['action_root']:
                        self.result.update(self.get_data(table.children.items()))
                else:
                    self.result = self.get_data(kwargs['action_root'][0].children.items())

            elif action == "compute_pc":
                dynamic_parameters = [i for i in kwargs['action_root'] if 'dynamic' in str(i)][0]
                self.dynamic_table_validation(dynamic_parameters)

            elif action == "quit" or action == "next":
                root = kwargs['root'] if 'root' in kwargs else self
                # root.destroy_window()
                root.destroy()

    def append_date(self, root=None, row_idx=0):
        root = self if root is None else root
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
            return self
        elif type(key) is str:
            return self.active_tables[key]
        else:
            return key

    def operation_cbox_callback(self, eventObject, root):
        root = self if root is None else root
        self.tools_data = load_tools_data(eventObject.widget.get())

        root.children['tool']['values'] = list(load_tools_data(eventObject.widget.get()))
        root.children['tool'].current(0)

        diametre = self.tools_data[root.children['tool'].get()][1]
        n_dents = self.tools_data[root.children['tool'].get()][2]

        self.set_tool_parameters(root, diametre, n_dents)

    def tool_cbox_callback(self, eventObject, root):
        root = self if root is None else root
        diametre = self.tools_data[eventObject.widget.get()][1]
        n_dents = self.tools_data[eventObject.widget.get()][2]

        self.set_tool_parameters(root, diametre, n_dents)

    @staticmethod
    def set_tool_parameters(root, diametre, n_dents):
        # Set diametre
        root.children['diameter']['text'] = diametre
        # Set nombre de dents
        root.children['n_teeth']['text'] = n_dents

    def append_combobox_row(self, text, values, fcn, **kwargs):  # root=None, row=0):
        root = kwargs['root'] if 'root' in kwargs else self
        row = kwargs['row'] if 'row' in kwargs else 0

        tk.Label(root, width=25, text=text + ": ", padx=5, pady=5).grid(row=row, column=0)

        name = kwargs['name'] if 'name' in kwargs else text.lower()
        cbox = tk.ttk.Combobox(root, values=values, state="readonly", width=22, name=name)
        cbox.bind("<<ComboboxSelected>>", lambda event, root=root: fcn(event, root))
        cbox.grid(row=row, column=1)

    def append_buttons(self, keys, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        root_table = kwargs['root_table'] if 'root_table' in kwargs else None

        btn_next = tk.Button(root, text="Valider", command=lambda **kwargs: self.change_program_state(actions=["get_data", "next"], action_root=root_table), padx=10, pady=5, font='Helvetica 11 bold')
        btn_calculer = tk.Button(root, text="Calculer Pc", command=lambda **kwargs: self.change_program_state(actions=["compute_pc"], action_root=root_table), padx=10, pady=5, font='Helvetica 11 bold')
        btn_add = tk.Button(root, text="Ajouter une autre ligne", command=lambda **kwargs: self.change_program_state(keys=keys, actions=["add_dynamic_row"], action_root=root_table), padx=10, pady=5, font='Helvetica 11 bold')

        btn_next.grid(row=0, column=0, padx=20, pady=5)
        btn_calculer.grid(row=0, column=2, padx=20, pady=5)
        btn_add.grid(row=0, column=4, padx=20, pady=5)

    def append_entry_row(self, text, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        row = kwargs['row'] if 'row' in kwargs else 0

        tk.Label(root, width=25, text=text + " :").grid(row=row, column=0)

        ent_name = kwargs['ent_name'] if 'ent_name' in kwargs else f"entry_r{row}c1"
        tk.Entry(root, width=25, name=ent_name).grid(row=row, column=1)

    def set_label_row(self, headers, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        row = kwargs['row'] if 'row' in kwargs else 0

        for i, h in enumerate(headers):
            name = kwargs['names'][i] if 'names' in kwargs else f"label_r{row}c{i}"
            if 'header' in kwargs:
                tk.Label(root, text=h, width=22, font='Helvetica 11 bold', bg='gray', name=name).grid(row=row, column=i)
            else:
                tk.Label(root, text=h, width=22, name=name).grid(row=row, column=i)

    def append_dynamic_row(self, keys, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        n = len(root.children) // len(keys) - 1
        row = n + 1
        tk.Label(root, text=f"{n}").grid(row=row, column=0, pady=5, padx=5)

        for col_idx, key in enumerate(keys[1:]):
            name = f'{key.lower()}_{row}'

            if key == "Fichier de mesure":
                btn = tk.Button(root, text="Parcourir", command=lambda **kwargs: self.change_program_state(actions=['select_file'], file=n, action_root=root), name=name)
                btn.grid(row=row, column=col_idx + 1, pady=5, padx=5)
            else:
                tk.Label(root, text='...', name=name).grid(row=row, column=col_idx + 1, pady=5, padx=5)

    # def destroy_window(self):
    #     self.destroy()

    def user_exit(self):
        selection = tk.messagebox.askquestion("quitter l'application", "Voulez-vous vraiment quitter l'application?", icon='warning')

        if selection == 'yes':
            self.destroy_window()


def parse_res(win):
    res = {}
    for key in win.children:
        if not "button" in key:
            label = win.children[key].children["!label"].cget("text")
            vals = []
            for wn in win.children[key].children:
                if 'entry' in wn or 'combobox' in wn:
                    vals.append(f"{win.children[key].children[wn].get()}")
                elif 'label2' in wn:
                    vals.append(f"{win.children[key].children[wn]['text']}")

            res[label] = ('/'.join(vals, ))

    return res


def set_general_machining_characteristics(win):
    frame = tk.Frame(win, name='general_machining_characteristics')

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
    tk.Button(win, text=" Suivant ", command=lambda **kwargs: win.change_program_state(actions=["get_data", "next"], action_root=[frame]), pady=5).pack(pady=10)


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
        table2_headers = ["Mesure n°", "Engagement axial ap(mm)", "Engagement radial ae(mm)", "Fichier de mesure", "Pc (W)", "Statut"]
    elif 'Q max' in target:
        entries = ["Engagement axial ap (mm)",
                   "Engagement radial ae (mm)",
                   "Vitesse de coupe init Vc (m/min)",
                   "Épaisseur de coupe init h (mm)"]
        table2_headers = ["Mesure n°", "Épaisseur de coupe h (mm)", "Vitesse de coupe Vc (mm/tr)", "Fichier de mesure", "Pc (W)", "Statut"]

    # Set Vc input parameters table
    input_parameters_frame = tk.Frame(win, name="input_parameters", highlightthickness=2, highlightbackground="black")

    win.set_label_row(["Paramètres d’entrée", "Valeurs utilisées"], root=input_parameters_frame, header=True)

    for i, entry in enumerate(entries):
        win.append_entry_row(entry, row=i+1, root=input_parameters_frame)

    input_parameters_frame.pack(padx=15, pady=15)

    # Set Vc input parameters table
    dynamic_parameters_frame = VerticalScrolledFrame(win, interior_name=f'dynamic_parameters_{target}')

    # Set headers
    win.set_label_row(table2_headers, root=dynamic_parameters_frame.interior, header=True)

    # Set first row
    win.append_dynamic_row(table2_headers, root=dynamic_parameters_frame.interior)

    dynamic_parameters_frame.pack(padx=15, pady=15)
    dynamic_parameters_frame.interior.pack(padx=20, pady=15)

    # Set buttons
    buttons_frame = tk.Frame(win, name="buttons")
    buttons_frame.pack(padx=15, pady=15)
    win.append_buttons(table2_headers, root=buttons_frame, root_table=[input_parameters_frame, dynamic_parameters_frame.interior])


def set_user_window(app_name, target, **kwargs):
    win = Window(app_name, window_title=target, **kwargs)
    if target == "Caractéristiques de l'usinage":
        set_general_machining_characteristics(win)

    elif "Détermination" in target:
        set_operation_window(win, target)

    win()
    res = win.result

    return res
