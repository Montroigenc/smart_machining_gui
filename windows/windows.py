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
import unidecode
import random

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from utils.utils import load_tools_data
from data_manager.data_manager import get_pc_from_machining_file
from windows.formulas import compute_Q, compute_Wc, compute_h, compute_N, compute_Vf


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

        # a.axvspan(data['x'][data['best_range_min']], data['x'][data['best_range_max']], facecolor='g', alpha=0.5)
        a.axvspan(data['x'][data['min_target_value']], data['x'][data['min_target_value'] + 1], facecolor='g', alpha=0.5)

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

        # if 'window_title' in kwargs:
        #     tk.Label(self, text=kwargs['window_title'], padx=5, pady=5, font='Helvetica 15 bold').pack(pady=15)

        self.target = kwargs['target'] if 'target' in kwargs else None
        self.manual_exit = False
        self.tools_data = []
        self.available_operations = kwargs['available_operations'] if 'available_operations' in kwargs else None
        self.general_parameters = kwargs['general_parameters'] if 'general_parameters' in kwargs else None

        self.result = dict()

        self.AD_max = None
        self.Q_max = None
        self.max_params = {'AD': -1, 'Q': -1}

        self.action = None
        self.debug = kwargs['debug'] if 'debug' in kwargs else False

        # self.resizable(0, 0)

    def set_win_title(self, window_title):
        tk.Label(self, text=window_title, padx=5, pady=5, font='Helvetica 15 bold').pack(pady=15)

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

    def update_ADQ_max(self, dynamic_widgets, n, **kwargs):
        if self.target in ['AD max', 'Q max']:
            root = [kv[1] for kv in self.children.items() if 'verticalscrolledframe' in kv[0]][0].interior

            target_widgets = np.asarray([kw[1]['text'] for kw in root.children.items() if f'{self.target.split()[0].lower()}_' in kw[0].split('.')[-1]])
            status_list = [kw[1].get() == 'OK' for kw in root.children.items() if "statut_" in kw[0]]

            ok_values = target_widgets[status_list]

            if len(ok_values) > 0:
                self.max_params[self.target.split()[0]] = np.max(ok_values)
                self.children['search_param'].configure(text=f'{self.target} = {np.max(ok_values):.4f}')

    def update_dynamic_row(self, filename, btn, **kwargs):
        root = [kv[1] for kv in self.children.items() if 'verticalscrolledframe' in kv[0]][0].interior

        row = btn.grid_info()['row']

        # Check if there was already a selected file
        already_used = btn['text'] != 'Parcourir'

        # Set green and text filename in button
        btn.configure(fg="green", text=filename)

        # Get all widgets of the pressed button row
        widgets = [kv for kv in root.children.values() if kv.grid_info()['row'] == row and kv.grid_info()['column'] > 0]

        # Set Pc (W)
        # pc = get_pc_from_machining_file(filename)
        Pc = np.random.randint(100, 1000)
        [w for w in widgets if 'pc (w)' in str(w).split('.')[-1]][0].configure(text=Pc)

        d = self.general_parameters['diameter']
        z = self.general_parameters['n_teeth']

        ap = float(self.result['input_parameters']['engagement axial ap (mm)']) if 'engagement axial ap (mm)' in self.result['input_parameters'].keys() else float([w for w in widgets if 'ap (mm)' in str(w).split('.')[-1]][0].get())
        ae = float(self.result['input_parameters']['engagement radial ae (mm)']) if 'engagement radial ae (mm)' in self.result['input_parameters'].keys() else float([w for w in widgets if 'ae (mm)' in str(w).split('.')[-1]][0].get())

        Vc = float(self.result['input_parameters']['vitesse de coupe vc (m/min)']) if 'vitesse de coupe vc (m/min)' in self.result['input_parameters'].keys() else float([w for w in widgets if 'vc (m/min)' in str(w).split('.')[-1]][0].get())

        fz = float(self.result['input_parameters']['avance par dent fz (mm/tr)']) if 'avance par dent fz (mm/tr)' in self.result['input_parameters'].keys() else float([w for w in widgets if 'fz (mm/tr)' in str(w).split('.')[-1]][0].get())

        for widget in widgets:
            widget_name = str(widget).split(".")[-1]
            if 'wc (w)' in widget_name:
                widget.configure(text=compute_Wc(d, Pc, ap, ae, z, fz, Vc))

            elif 'vitesse de broche n' in widget_name:
                N = compute_N(Vc, d)
                widget.configure(text=N)

            elif 'vf' in widget_name:
                Vf = compute_Vf(N, fz, z)
                widget.configure(text=Vf)

            elif 'h (mm)' in widget_name:
                widget.configure(text=compute_h(ae, fz, d))

            elif 'statut' in widget_name:
                # widget.configure(text="OK")
                widget.delete(0, tk.END)
                widget.insert(0, 'OK')

            elif 'ad_' in widget_name:
                widget.configure(text=ap * ae)

            elif 'q_' in widget_name:
                AD = ap * ae
                widget.configure(text=compute_Q(AD, Vf))

            # elif 'Label' in str(type(widget)):
            #     if 'statut' in widget_name:
            #         widget.configure(text="OK")
            #     else:
            #         widget.configure(text=f'{random.randint(0, 10)}')
            #
            # elif 'Entry' in str(type(widget)):
            #     widget.delete(0, tk.END)
            #     widget.insert(0, f'{random.randint(0, 10)}')

        self.update_ADQ_max(widgets, row, **kwargs)

        return already_used

    def change_program_state(self, *args, **kwargs):

        for action in kwargs['actions']:
            if action == 'select_file':
                filename = tk.filedialog.askopenfilename(initialdir="/", title="Sélectionner un fichier")
                if filename != "":
                    already_used = self.update_dynamic_row(filename, args[0].widget, **kwargs)

                    if not already_used:
                        self.append_dynamic_row(root=[kv[1] for kv in self.children.items() if 'verticalscrolledframe' in kv[0]][0].interior)

            elif action == "get_data":
                if self.target == "Caractéristiques de l'usinage":
                    root = [kv[1] for kv in self.children.items() if 'general_machining_characteristics' in kv[0]][0]
                    self.result = self.get_data(root.children.items())
                else:
                    root = [kv[1] for kv in self.children.items() if 'input_parameters' in kv[0]]
                    if len(root) > 0:
                        self.result["input_parameters"] = self.get_data(root[0].children.items())

                    root = [kv[1] for kv in self.children.items() if 'verticalscrolledframe' in kv[0]]
                    if len(root) > 0:
                        self.result["dynamic_parameters"] = self.get_data(root[0].interior.children.items())

                    # for table in [self.children['input_parameters'], root[0].interior]:
                    #     self.result.update(self.get_data(table.children.items()))

            elif action == "compute_pc":
                dynamic_parameters = [i for i in kwargs['action_root'] if 'dynamic' in str(i)][0]
                self.result['computation_results'] = self.dynamic_table_validation(dynamic_parameters)

            elif action == "delete_line":
                root = [kv[1] for kv in self.children.items() if 'verticalscrolledframe' in kv[0]][0].interior

                # n = int(args[0].widget._name.split('_')[-1])
                n = [child.grid_info()["row"] for child in root.grid_slaves() if child is args[0].widget][0]

                widgets2delete = [child for child in root.grid_slaves() if child.grid_info()["row"] == n]

                for child in widgets2delete:
                    child.destroy()

                x = 0
                x = 1

                for child in root.grid_slaves()[::-1]:
                    # if int(child._name.split('_')[1]) >= n:
                    if child.grid_info()["row"] >= n:
                        # grid_info = child.grid_info()
                        # grid_info["row"] -= 1
                        # child.grid(grid_info)

                        # child._name = '_'.join([child._name.split('_')[0], str(child.grid_info()["row"])])

                        if int(child.grid_info()["column"]) == 0:
                            child['text'] = str(child.grid_info()["row"] - 2)

                # Append new line if needed
                new_line_not_needed = False
                for child in root.grid_slaves():
                    if 'fichier de mesure_' in str(child):
                        new_line_not_needed = child['text'] == 'Parcourir'
                        if new_line_not_needed:
                            break

                if not new_line_not_needed:
                    self.append_dynamic_row(root=root)

                x = 0
                x = 1
                x = 2

            elif action == "back" or action == "next":
                # root = kwargs['root'] if 'root' in kwargs else self

                for child in self.winfo_children():
                    child.destroy()
                self.quit()

                # if action == "back":
                #     root.destroy()
                # elif action == "next":
                #     for child in root.winfo_children():
                #         child.destroy()
                #     root.quit()

                self.action = action

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
        # btn_calculer = tk.Button(root, text="Afficher curve Wc", command=lambda **kwargs: self.change_program_state(actions=["compute_pc"], action_root=root_table), padx=10, pady=5, font='Helvetica 11 bold')
        btn_back = tk.Button(root, text="Revenir à la fenêtre précédente", command=lambda **kwargs: self.change_program_state(actions=["back"], action_root=[root_table]), padx=10, pady=5, font='Helvetica 11 bold')

        btn_next.grid(row=0, column=0, padx=20, pady=5)
        # btn_calculer.grid(row=0, column=2, padx=20, pady=5)
        btn_back.grid(row=0, column=4, padx=20, pady=5)

    def append_entry_row(self, text, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        row = kwargs['row'] if 'row' in kwargs else 0

        tk.Label(root, width=25, text=f"{text} :").grid(row=row, column=0)

        ent_name = kwargs['ent_name'] if 'ent_name' in kwargs else f'{unidecode.unidecode(text.lower())}'
        ent = tk.Entry(root, width=25, name=ent_name, justify='center')

        if self.debug:
            ent.insert(0, f'{random.randint(1, 10)}')

        ent.grid(row=row, column=1)

    def append_label_row(self, headers, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        row = kwargs['row'] if 'row' in kwargs else 0

        for i, h in enumerate(headers):
            name = kwargs['names'][i] if 'names' in kwargs else f"label_r{row}c{i}"
            if 'header' in kwargs:
                # tk.Label(root, text=h, width=22, font='Helvetica 11 bold', bg='gray', name=name).grid(row=row, column=i)
                tk.Label(root, text=h, font='Helvetica 11 bold', bg='gray', name=name).grid(row=row, column=i, sticky=tk.N+tk.S+tk.E+tk.W)
            else:
                tk.Label(root, text=h, width=22, name=name).grid(row=row, column=i)

    def append_dynamic_row(self, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        keys = [root.children[l]['text'] for l in root.children if '_r0c' in l]

        row = max([child.grid_info()["row"] for child in root.grid_slaves()]) + 1

        # Set row index
        tk.Label(root, text=f"{row - 1}", name=f'{unidecode.unidecode(keys[0].lower())}_{row - 1}').grid(row=row, column=0, pady=5, padx=0)

        for col_idx, key in enumerate(keys[1:]):
            name = f'{unidecode.unidecode(key.lower())}_{row - 1}'

            if key == "Fichier de mesure":
                btn = tk.Button(root, text="Parcourir", name=name)
                btn.bind("<Button-1>", lambda event, **kwargs: self.change_program_state(event, actions=['select_file']))
                btn.grid(row=row, column=col_idx + 1, pady=5, padx=0)

            elif key in ['Engagement axial ap (mm)', 'Engagement radial ae (mm)', "Vitesse de coupe Vc (m/min)", "Avance par dent fz (mm/tr)", "Statut"]:
                ent = tk.Entry(root, width=25, name=name, justify='center')
                if self.debug:
                    ent.insert(0, f'{random.randint(1, 10)}')

                ent.grid(row=row, column=col_idx + 1, pady=5, padx=0)

            elif key == "":
                del_btn = tk.Button(root, text="Supprimer ligne", name=f'del{name}')
                del_btn.bind("<Button-1>", lambda event, **kwargs: self.change_program_state(event, actions=['delete_line']))
                del_btn.grid(row=row, column=col_idx + 1, pady=5, padx=40)

            else:
                tk.Label(root, text='...', name=name).grid(row=row, column=col_idx + 1, pady=5, padx=0)

        if self.debug:
            self.update_dynamic_row("dummy_file", btn, **kwargs)

    def user_exit(self):
        selection = tk.messagebox.askquestion("quitter l'application", "Voulez-vous vraiment quitter l'application?", icon='warning')

        if selection == 'yes':
            # self.destroy_window()
            self.destroy()
