import tkinter as tk
import tkinter.ttk as TTK
from tkinter import messagebox, filedialog
from datetime import date
import numpy as np
import unidecode
import random
import json

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from utils.utils import load_tools_data
from data_manager.data_manager import get_pc_from_machining_file
from graphical_interfaces.formulas import compute_Q, compute_Wc, compute_h, compute_N, compute_Vf
from graphical_interfaces.tangent_method import plot_tangent_data

dummy_pc_file = "C:/Users/RI/Desktop/smart_machining/Test full.csv"

LARGE_FONT = ("Verdana", 12)


def raise_frame(frame):
    frame.tkraise()


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


# class GraphFrameLoadingData(tk.Frame):
#     def __init__(self, parent, name):
#         tk.Frame.__init__(self, parent, name=name)
#
#         self.figure = Figure(figsize=(5, 5), dpi=100)
#         self.subplot = self.figure.add_subplot(111)
#         # self.subplot.plot(data['x'], data['y'])
#
#         canvas = FigureCanvasTkAgg(self.figure, self)
#         canvas.draw()
#         canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
#
#         toolbar = NavigationToolbar2Tk(canvas, self)
#         toolbar.update()
#         canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


class GraphFrame(tk.Frame):
    def __init__(self, parent, name, figure):
        tk.Frame.__init__(self, parent, name=name)

        # f = Figure(figsize=(5, 5), dpi=100)
        # a = f.add_subplot(111)
        # a.plot(data['x'], data['y'])

        # f, means = plot_tangent_data(data, axis_labels)

        canvas = FigureCanvasTkAgg(figure, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


class StartFrame(tk.Frame):
    def __init__(self, parent, controller, name):
        tk.Frame.__init__(self, parent, name=name)


class AuxGraphFrame(tk.Frame):
    def __init__(self, parent, controller, name):
        tk.Frame.__init__(self, parent, name=name)

        self.controller = controller
        self.res = None

    def generate_fig(self):
        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.subplot = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  #side=tk.LEFT, fill=tk.BOTH, expand=True)  # side=tk.BOTTOM)  #, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(fill=tk.BOTH, expand=True)  #side=tk.LEFT)  #side=tk.TOP)  #, fill=tk.BOTH, expand=True)

    def generate_widgets_power(self):
        # BUTTONS
        btns_frame = tk.Frame(self, name='buttons_frame')

        next_btn = tk.Button(btns_frame, text="Valider", command=lambda **kwargs: self.controller.change_program_state(actions=["back_to_frame_0_set_ok"], root=self.controller), padx=10, pady=5, font='Helvetica 11 bold')
        return_btn = tk.Button(btns_frame, text="Revenir à la fenêtre précédente", command=lambda **kwargs: self.controller.change_program_state(actions=["back_to_frame_0_set_ko"]), padx=10, pady=5, font='Helvetica 11 bold')

        next_btn.grid(row=1, column=0, padx=10, pady=10)
        return_btn.grid(row=1, column=1, padx=10, pady=10)

        btns_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def generate_widgets_tangent(self, data):
        # DATA FRAME
        data_frame = tk.Frame(self, name='data_frame')

        # DATA TABLE
        table_frame = VerticalScrolledFrame(data_frame, interior_name='table')
        x_param_name = "Vitesse de coupe Vc (m/min)" if self.controller.target == "Vc min" else "Épaisseur de coupe h (mm)"

        self.controller.append_label_row([x_param_name, "Wc (W*min/cm3)"], root=table_frame.interior, header=True)

        for row_idx, (vci, wci) in enumerate(zip(data[0], data[1])):
            self.controller.append_label_row([vci, wci], root=table_frame.interior, row=row_idx + 1)

        # SET VC MIN RESULT ENTRY
        results_frame = tk.Frame(data_frame, name='results_frame')
        self.controller.append_entry_row(self.controller.target, root=results_frame, ent_field=np.min(data[1]))

        # BUTTONS
        btns_frame = tk.Frame(data_frame, name='buttons_frame')

        next_btn = tk.Button(btns_frame, text="Valider", command=lambda **kwargs: self.controller.change_program_state(actions=["get_target", "back_to_frame_0_set_ok"], root=self.controller), padx=10, pady=5, font='Helvetica 11 bold')
        return_btn = tk.Button(btns_frame, text="Revenir à la fenêtre précédente", command=lambda **kwargs: self.controller.change_program_state(actions=["back_to_frame_0_set_ko"], action_root=[table_frame.interior]), padx=10, pady=5, font='Helvetica 11 bold')

        next_btn.grid(row=1, column=0, padx=10, pady=10)
        return_btn.grid(row=1, column=1, padx=10, pady=10)

        # data_frame.pack(side=tk.RIGHT, padx=10, pady=10)  #, fill=tk.BOTH, expand=tk.TRUE)

        # GRAPH
        axis_labels = {'x_lab': x_param_name, 'y_lab': "Énergie spécifique de coupe Wc (W)"}

        self.res = plot_tangent_data(self, data, axis_labels)
        #
        # graph_frame = GraphFrame(self, name='graph_frame', figure=figure)
        # graph_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        # pack inner data table
        table_frame.pack(side=tk.TOP, padx=10, pady=10)  #, fill=tk.BOTH, expand=tk.TRUE)
        results_frame.pack(side=tk.TOP, padx=10, pady=10)  #, fill=tk.BOTH, expand=tk.TRUE)
        btns_frame.pack(side=tk.BOTTOM, padx=10, pady=10)  #, fill=tk.BOTH, expand=tk.TRUE)

        data_frame.pack(side=tk.LEFT)  # , fill=tk.BOTH, expand=tk.TRUE)


class Window(tk.Tk):
    def __init__(self, app_name, **kwargs):
        tk.Tk.__init__(self)
        self.protocol("WM_DELETE_WINDOW", self.user_exit)
        self.title(app_name)

        tk.Label(self, text='', padx=5, pady=5, font='Helvetica 15 bold', name='title').pack(pady=15)

        self.target = kwargs['target'] if 'target' in kwargs else None
        self.manual_exit = False
        self.tools_data = []
        self.available_operations = kwargs['available_operations'] if 'available_operations' in kwargs else None

        self.data = kwargs['data'] if 'data' in kwargs else None

        self.result = dict()

        self.max_params = {'AD': -1, 'Q': -1}

        self.action = None
        self.debug = kwargs['data']['debug'] if 'debug' in kwargs['data'] else False
        self.name = None

        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for f_idx, F in enumerate([StartFrame, AuxGraphFrame]):
            frame = F(self.container, self, f'frame_{f_idx}')

            self.frames[f'frame_{f_idx}'] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame('frame_0')

        # self.mainloop()

    def set_win_title(self, window_title):
        self.children['title'].configure(text=window_title)

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
            root = [v for (k, v) in self.frames['frame_0'].children.items() if 'verticalscrolledframe' in k][0].interior

            target_widgets = np.asarray([kw[1]['text'] for kw in root.children.items() if f'{self.target.split()[0].lower()}_' in kw[0].split('.')[-1]])
            status_list = [kw[1].get() == 'OK' for kw in root.children.items() if "statut_" in kw[0]]

            ok_values = target_widgets[status_list].astype('float')

            if len(ok_values) > 0:
                self.max_params[self.target.split()[0]] = ok_values.max()
                self.children['search_param'].configure(text=f'{self.target} = {np.max(ok_values):.4f}')

    def get_table_values(self, val_names, widgets_):
        vals = []
        for val_name in val_names:
            if val_name == 'd':
                vals.append(float(self.data['general_parameters']['diameter']))
            elif val_name == 'z':
                vals.append(float(self.data['general_parameters']['n_teeth']))
            else:
                if val_name == 'ap':
                    complete_val_name = 'engagement axial ap (mm)'
                    short_val_name = 'ap (mm)'
                elif val_name == 'ae':
                    complete_val_name = 'engagement radial ae (mm)'
                    short_val_name = 'ae (mm)'
                elif val_name == 'Vc':
                    complete_val_name = 'vitesse de coupe vc (m/min)'
                    short_val_name = 'vc (m/min)'
                elif val_name == 'fz':
                    complete_val_name = 'avance par dent fz (mm/tr)'
                    short_val_name = 'fz (mm/tr)'

                vals.append(float(self.result['input_parameters'][complete_val_name]) \
                                if complete_val_name in self.result['input_parameters'].keys() else \
                                float([w for w in widgets_ if short_val_name in str(w).split('.')[-1]][0].get()))

        return vals

    def get_Pc(self, filename_, **kwargs):
        # Set Pc (W)
        if filename_ is None:
            Pc = np.random.randint(10, 100)
            filename = 'dummy'
        else:
            self.frames['frame_1'].generate_fig()
            self.frames['frame_1'].generate_widgets_power()

            self.show_frame('frame_1')
            file_data = get_pc_from_machining_file(self, filename_)
            Pc = float(file_data['Pc']) if file_data is not None else None

        return Pc

    def update_dynamic_row(self, btn, filename=None, Pc=None, **kwargs):
        # Set Pc (W)
        if Pc is None:
            Pc = np.random.randint(10, 100)
            filename = 'dummy'

        root = [v for (k, v) in self.frames['frame_0'].children.items() if 'verticalscrolledframe' in k][0].interior

        row = btn.grid_info()['row']

        # Get all widgets of the pressed button row
        widgets = [kv for kv in root.children.values() if kv.grid_info()['row'] == row and kv.grid_info()['column'] > 0]

        # Check if there was already a selected file
        already_used = btn['text'] != 'Parcourir'

        # Set green and text filename in button
        btn.configure(fg="green", text=filename)

        [w for w in widgets if 'pc (w)' in str(w).split('.')[-1]][0].configure(text=f'{Pc:.2f}')

        d, z, ap, ae, Vc, fz = self.get_table_values(['d', 'z', 'ap', 'ae', 'Vc', 'fz'], widgets)

        for widget in widgets:
            widget_name = str(widget).split(".")[-1]
            if 'wc (w)' in widget_name:
                widget.configure(text=f'{compute_Wc(d, Pc, ap, ae, z, fz, Vc):.4f}')

            elif 'vitesse de broche n' in widget_name:
                N = compute_N(Vc, d)
                widget.configure(text=f'{N:.4f}')

            elif 'vf' in widget_name:
                Vf = compute_Vf(N, fz, z)
                widget.configure(text=f'{Vf:.4f}')

            elif 'h (mm)' in widget_name:
                widget.configure(text=f'{compute_h(ae, fz, d):.4f}')

            elif 'statut' in widget_name:
                # widget.configure(text="OK")
                widget.delete(0, tk.END)
                widget.insert(0, 'OK')

            elif 'ad_' in widget_name:
                widget.configure(text=f'{ap * ae:.4f}')

            elif 'q_' in widget_name:
                AD = ap * ae
                widget.configure(text=f'{compute_Q(AD, Vf):.4f}')

        self.update_ADQ_max(widgets, row, **kwargs)

        return already_used

    def check_required_entries(self, btn):
        root = [v for (k, v) in self.frames['frame_0'].children.items() if 'verticalscrolledframe' in k][0].interior
        row = btn.grid_info()['row']

        # Get all widgets of the pressed button's row
        widgets = [kv for kv in root.children.values() if kv.grid_info()['row'] == row and kv.grid_info()['column'] > 0]

        # CHECK IF REQUIRED ENTRIES ARE ALREADY FILLED
        empty_entries = []
        for w in widgets:
            if isinstance(w, tk.Entry):
                if w.get() == '':
                    empty_entries.append(str(w).split('.')[-1])

        res = len(empty_entries) == 0
        if not res:
            tk.messagebox.showerror("Error", f"Les champs {','.join(empty_entries)} doivent être remplis", icon='error')

        return res

    def change_program_state(self, *args, **kwargs):
        for action in kwargs['actions']:
            if 'select_file' in action:
                # CHECK IF REQUIRED ENTRIES ARE ALREADY FILLED
                res = self.check_required_entries(args[0].widget)
                if not res:
                    continue

                # filename = 'C:/Users/RI/Desktop/smart_machining/Test full.csv'
                filename = tk.filedialog.askopenfilename(initialdir="/", title="Sélectionner un fichier")
                if filename == "":
                    continue

                if action == 'select_file_pc':
                    # Get Pc (W)
                    Pc = self.get_Pc(filename)
                    if Pc is None:
                        continue

                    already_used = self.update_dynamic_row(args[0].widget, filename, Pc=Pc, **kwargs)

                    if not already_used:
                        self.append_dynamic_row(root=[v for (k, v) in self.frames['frame_0'].children.items() if 'verticalscrolledframe' in k][0].interior)

                elif action == 'select_file_existing':
                    self.result["file_name"] = filename

            elif action == "get_data":
                if self.target == "Caractéristiques de l'usinage":
                    root = [v for (k, v) in self.frames['frame_0'].children.items() if 'general_machining_characteristics' in k][0]
                    self.result = self.get_data(root.children.items())
                else:
                    if 'input_parameters' in self.children['!frame'].children['frame_0'].children.keys():
                        root = [v for (k, v) in self.frames['frame_0'].children.items() if 'input_parameters' in k][0]
                        self.result["input_parameters"] = self.get_data(root.children.items())

                    if '!verticalscrolledframe' in self.frames['frame_0'].children.keys():
                        root = [v for (k, v) in self.frames['frame_0'].children.items() if 'verticalscrolledframe' in k][0].interior
                        self.result["dynamic_parameters"] = self.get_data(root.children.items())

            elif action == "get_target":
                root = [v for (k, v) in self.frames['frame_1'].children.items() if 'data_frame' in k][0]
                self.result[self.target] = float(root.children['results_frame'].children[self.target.lower()].get())

            elif action == "compute_pc":
                dynamic_parameters = [i for i in kwargs['action_root'] if 'dynamic' in str(i)][0]
                self.result['computation_results'] = self.dynamic_table_validation(dynamic_parameters)

            elif action == "delete_line":
                root = [v for (k, v) in self.frames['frame_0'].children.items() if 'verticalscrolledframe' in k][0].interior

                # n = int(args[0].widget._name.split('_')[-1])
                n = [child.grid_info()["row"] for child in root.grid_slaves() if child is args[0].widget][0]

                widgets2delete = [child for child in root.grid_slaves() if child.grid_info()["row"] == n]

                for child in widgets2delete:
                    child.destroy()

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

            elif "back_to_frame" in action:
                self.show_frame('frame_0')
                self.frames['frame_1'].res = 'set_ok' in action

                for c in self.frames['frame_1'].winfo_children():
                    c.destroy()

                self.quit()

            elif action == "back" or action == "next":
                for c in self.frames['frame_0'].winfo_children():
                    c.destroy()

                self.quit()
                self.action = action

            elif action == "destroy_all_frames":
                for child in self.winfo_children():
                    child.destroy()
                # self.destroy()

                self.quit()
                self.action = action

    def append_date(self, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        row = kwargs['row'] if 'row' in kwargs else 0

        date_cell = tk.Frame(root, name='date')
        lab = tk.Label(root, width=25, text="Date du traitement :", padx=5, pady=5)

        day = tk.ttk.Combobox(date_cell, values=[i for i in range(1, 32)], width=2, name='day')

        months_french = ["janvier",
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
                         "décembre"]

        month = tk.ttk.Combobox(date_cell, values=months_french,
                                state="readonly",
                                width=8,
                                name='month')

        year = tk.ttk.Combobox(date_cell, values=[i for i in range(2020, 2040)], width=4, name='year')

        if "date" not in self.data["general_parameters"]:
            today = date.today()
            day.current(today.day - 1)
            month.current(today.month - 1)
            year.current(today.year - 2020)
        else:
            day_loaded, month_loaded, year_loaded = self.data["general_parameters"]["date"].split('/')
            day.current(int(day_loaded) - 1)
            month.current(months_french.index(month_loaded))
            year.current(int(year_loaded) - 2020)

        lab.grid(row=row, column=0)
        date_cell.grid(row=row, column=1)

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

        if 'ent_name' in self.data["general_parameters"]:
            ent.insert(0, f"{kwargs['ent_field']}")

        elif self.data["debug"]:
            ent.insert(0, f'{random.randint(1, 10)}')

        ent.grid(row=row, column=1)

    def append_label_row(self, headers, **kwargs):
        root = kwargs['root'] if 'root' in kwargs else self
        row = kwargs['row'] if 'row' in kwargs else 0

        for i, h in enumerate(headers):
            name = kwargs['names'][i] if 'names' in kwargs else f"label_r{row}c{i}"
            if 'header' in kwargs:
                # tk.Label(root, text=h, width=22, font='Helvetica 11 bold', bg='gray', name=name).grid(row=row, column=i)
                tk.Label(root, text=h, font='Helvetica 11 bold', bg='gray', name=name).grid(row=row, column=i, sticky=tk.N + tk.S + tk.E + tk.W)
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
                # btn.bind("<Button-1>", lambda event, **kwargs: self.change_program_state(event, actions=['select_file_pc']))
                btn.bind("<Button-1>", lambda event, **kwargs: self.change_program_state(event, actions=['select_file_pc']))
                btn.grid(row=row, column=col_idx + 1, pady=5, padx=0)

            elif key in ['Engagement axial ap (mm)', 'Engagement radial ae (mm)', "Vitesse de coupe Vc (m/min)", "Avance par dent fz (mm/tr)"]:
                ent = tk.Entry(root, width=25, name=name, justify='center')
                if self.data['debug']:
                    ent.insert(0, f'{random.randint(1, 10)}')

                ent.grid(row=row, column=col_idx + 1, pady=5, padx=0)

            elif key == "Statut":
                ent = tk.Entry(root, width=25, name=name, justify='center')
                if self.data['debug']:
                    ent.insert(0, 'OK')

                ent.grid(row=row, column=col_idx + 1, pady=5, padx=0)

            elif key == "":
                del_btn = tk.Button(root, text="Supprimer ligne", name=f'del{name}')
                del_btn.bind("<Button-1>", lambda event, **kwargs: self.change_program_state(event, actions=['delete_line']))
                del_btn.grid(row=row, column=col_idx + 1, pady=5, padx=40)

            else:
                tk.Label(root, text='...', name=name).grid(row=row, column=col_idx + 1, pady=5, padx=0)

        if self.data['debug'] > 1:
            self.update_dynamic_row(btn, **kwargs)

    def user_exit(self):
        selection = tk.messagebox.askquestion("quitter l'application", "Voulez-vous vraiment quitter l'application?", icon='warning')

        if selection == 'yes':
            # self.destroy_window()
            self.destroy()
