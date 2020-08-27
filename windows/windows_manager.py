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

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from windows.windows import Window, VerticalScrolledFrame, GraphFrame
from windows.formulas import *


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
    # win.append_combobox_row("Opération", list(win.available_operations), fcn=win.operation_cbox_callback, root=frame, row=1, name='operation')
    # win.append_combobox_row("Outil", list(win.tools_data), fcn=win.tool_cbox_callback, root=frame, row=2, name='tool')
    # win.append_label_row(["Diamètre :", ""], root=frame, row=3, names=['', 'diameter'])
    # win.append_label_row(["Nombre de dents :", ""], root=frame, row=4, names=['', 'n_teeth'])

    win.append_label_row(["Opération :", "Fraisage"], root=frame, row=1, names=['', 'operation'])
    win.append_entry_row("Outil", root=frame, row=2, ent_name='tool')
    win.append_entry_row("Diamètre", root=frame, row=3, ent_name='diameter')
    win.append_entry_row("Nombre de dents", root=frame, row=4, ent_name='n_teeth')

    win.append_entry_row("Opérateur", row=5, root=frame, ent_name='user_name')
    win.append_date(root=frame, row_idx=6)
    win.append_entry_row("Lubrification", row=7, root=frame, ent_name='lubrication')
    win.append_entry_row("Commentaires", row=8, root=frame, ent_name='comments')

    frame.pack(padx=20, pady=20)

    # Set buttons
    tk.Button(win, text=" Suivant ", command=lambda **kwargs: win.change_program_state(actions=["get_data", "next"], action_root=[frame]), pady=5).pack(pady=10)

    win()


def get_operation_window_headers(target):
    if target == 'Vc min' in target:
        entries = ["Engagement axial ap (mm)",
                   "Engagement radial ae (mm)",
                   "Avance par dent fz (mm/tr)"]
        dynamic_table_headers = ["Mesure n°", "Vitesse de coupe Vc (m/min)", "Vitesse de broche N", "Vitesse d'avance Vf (m/min)", "Fichier de mesure", "Pc (W)", "Wc (W)"]
    elif target == 'f min':
        entries = ["Engagement axial ap (mm)",
                   "Engagement radial ae (mm)",
                   "Vitesse de coupe Vc (m/min)"]
        dynamic_table_headers = ["Mesure n°", "Avance par dent fz (mm/tr)", "Vitesse de broche N", "Vitesse d'avance Vf (m/min)", "Fichier de mesure", "Pc (W)", "Wc (W)"]
    elif target == 'AD max':
        entries = ["Vitesse de coupe Vc (m/min)",
                   "Avance par dent fz (mm/tr)",
                   "Vitesse de broche N",
                   "Vitesse d'avance Vf (m/min)"]
        # dynamic_table_headers = ["Mesure n°", "Engagement axial ap(mm)", "Engagement radial ae(mm)", "N", "Vf", "Épaisseur de coupe h (mm)", "Fichier de mesure", "Pc (W)", "Wc (W)", "AD", "Statut"]

        dynamic_table_headers = ["Mesure n°", "Engagement axial ap (mm)", "Engagement radial ae (mm)", "Épaisseur de coupe h (mm)", "Fichier de mesure", "Pc (W)", "Énergie spécifique de coupe Wc (W)", "Section de coupe AD", "Statut"]
    elif target == 'Q max':
        entries = ["Engagement axial ap (mm)",
                   "Engagement radial ae (mm)"]
        dynamic_table_headers = ["Mesure n°", "Vitesse de coupe Vc (m/min)", "Vitesse de broche N", "Vitesse d'avance Vf (m/min)", "Avance par dent fz (mm/tr)", "Épaisseur de coupe h (mm)", "Fichier de mesure", "Pc (W)", "Wc (W)", "Débit de copeaux Q", "Statut"]

    return entries, dynamic_table_headers


def set_operation_window_constant_parameters(win, entries):
    # Set constant parameters table
    input_parameters_frame = tk.Frame(win, name="input_parameters", highlightthickness=2, highlightbackground="black")

    win.append_label_row(["Paramètres d’entrée", "Valeurs utilisées"], root=input_parameters_frame, header=True)

    for i, entry in enumerate(entries):
        win.append_entry_row(entry, row=i + 1, root=input_parameters_frame)

    input_parameters_frame.pack(padx=15, pady=15)

    # Set buttons
    buttons_frame = tk.Frame(win, name="buttons")
    btn_next = tk.Button(buttons_frame, text="Valider", command=lambda **kwargs: win.change_program_state(actions=["get_data", "next"], action_root=[input_parameters_frame]), padx=10, pady=5, font='Helvetica 11 bold')
    btn_back = tk.Button(buttons_frame, text="Revenir à la fenêtre précédente", command=lambda **kwargs: win.change_program_state(actions=["back"], action_root=[input_parameters_frame]), padx=10, pady=5, font='Helvetica 11 bold')

    btn_next.grid(row=0, column=0, padx=20, pady=5)
    btn_back.grid(row=0, column=2, padx=20, pady=5)
    buttons_frame.pack(padx=15, pady=15)


def set_operation_window_dynamic_parameters(win, target, table_headers):
    # Set Vc input parameters table
    constant_parameters_frame = tk.Frame(win, name="constant_parameters", highlightthickness=2, highlightbackground="black")

    win.append_label_row(["Paramètres d’entrée", "Valeurs utilisées"], root=constant_parameters_frame, header=True)

    for i, (key, entry) in enumerate(win.result['input_parameters'].items()):
        win.append_label_row([key, entry], row=i + 1, root=constant_parameters_frame)

    constant_parameters_frame.pack(padx=15, pady=15)

    # Set dynamic table frame
    dynamic_parameters_frame = VerticalScrolledFrame(win, interior_name=f'dynamic_parameters_{target}')

    # Set dynamic table headers
    win.append_label_row(table_headers + [""], root=dynamic_parameters_frame.interior, header=True)

    # Additional search parameter
    if 'max' in target:
        search_param = f"{['AD max', 'Q max'][['AD max', 'Q max'].index(target)]}"
        search_param_lbl = tk.Label(win, text=f"{search_param} = ", width=22, font='Helvetica 11 bold', name='search_param', borderwidth=2, relief="solid")

    # Set dynamic table first row
    if win.debug:
        for i in range(10):
            win.append_dynamic_row(root=dynamic_parameters_frame.interior)

    else:
        win.append_dynamic_row(root=dynamic_parameters_frame.interior)

    dynamic_parameters_frame.pack(padx=15, pady=15)
    dynamic_parameters_frame.interior.pack(padx=20, pady=15)

    # Additional search parameter packed here to avoid error while non existing search parameter widged while debugging with append_dynamic_row
    if 'max' in target:
        search_param_lbl.pack(padx=15, pady=15)

    # Set buttons
    buttons_frame = tk.Frame(win, name="buttons")
    buttons_frame.pack(padx=15, pady=15)
    win.append_buttons(table_headers, root=buttons_frame, root_table=[constant_parameters_frame, dynamic_parameters_frame.interior])


# def dynamic_table_validation(target, table):
#     dynamic_table_values = compute_dynamic_table(target, table)
#
#     if target in ['Vc min', 'f min']:
#         show_graphic(dynamic_table_values)
#         return dynamic_table_values['best_range_min']
#     elif target in ['AD max', 'Q max']:
#         return np.max(dynamic_table_values['y'])
#
#     # if validated:
#     #     target_parameter = str(table)[str(table).rfind('Détermination de ') + 17:].lower()
#     #     self.pcs[target_parameter] = pcs


def show_graphic(data, win):
    # DATA FRAME
    data_frame = tk.Frame(win, name='data_frame')

    # DATA TABLE
    table_frame = VerticalScrolledFrame(data_frame, interior_name='table')
    win.append_label_row(["Vitesse de coupe Vc (m/min)", "Wc (W*min/cm3)"], root=table_frame.interior, header=True)
    for row_idx, (vci, wci) in enumerate(zip(data['x'], data['y'])):
        win.append_label_row([vci, wci], root=table_frame.interior, row=row_idx+1)

    table_frame.interior.pack(side=tk.LEFT, padx=10, pady=10)
    table_frame.pack(side=tk.LEFT, padx=10, pady=10)

    # GRAPH
    axis_labels = {'x_lab': 'Cutting speed (Vc)', 'y_lab': 'Cutting energy (Wc)'}
    graph_frame = GraphFrame(win, name='graph_frame', data=data, axis_labels=axis_labels)
    graph_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    data_frame.pack(padx=10, pady=10)

    # BUTTONS
    btns_frame = tk.Frame(win, name='buttons_frame')

    next_btn = tk.Button(btns_frame, text="Valider", command=lambda **kwargs: win.change_program_state(actions=["next"], root=win), padx=10, pady=5, font='Helvetica 11 bold')
    return_btn = tk.Button(btns_frame, text="Revenir à la fenêtre précédente", command=lambda **kwargs: win.change_program_state(actions=["back"], action_root=[table_frame.interior]), padx=10, pady=5, font='Helvetica 11 bold')

    next_btn.grid(row=1, column=0, padx=10, pady=10)
    return_btn.grid(row=1, column=1, padx=10, pady=10)

    btns_frame.pack(padx=10, pady=10)


def set_operation_window(win, target):
    debug = False
    step = 0
    entries, dynamic_table_headers = get_operation_window_headers(target)

    while 0 <= step < 3:
        if step == 0:
            if debug:
                win.result['input_parameters'] = {'engagement axial ap (mm)': '1', 'engagement radial ae (mm)': '2', 'avance par dent fz (mm/tr)': '3'}
                step = step + 1
            else:
                # Set constant parameters table
                win.set_win_title(f'Détermination de {target}')
                set_operation_window_constant_parameters(win, entries)
                win()
                step = step + 1 if win.action == 'next' else step - 1

        if step == 1:
            win.set_win_title(f'Détermination de {target}')
            set_operation_window_dynamic_parameters(win, target, dynamic_table_headers)
            win()
            step = step + 1 if win.action == 'next' else step - 1

        if step == 2:
            if target in ['Vc min', 'f min']:
                dynamic_table_values = compute_dynamic_table(target, win)

                win.set_win_title(f'Résultats')
                show_graphic(dynamic_table_values, win)
                win()

                win.result[target] = dynamic_table_values['min_target_value']

            elif target in ['AD max', 'Q max']:
                win.result[target] = [win.AD_max, win.Q_max][['AD max', 'Q max'].index(target)]

            step = step + 1 if win.action == 'next' else step - 1


def set_user_window(app_name, target, **kwargs):
    kwargs['debug'] = True
    win = Window(app_name, window_title=f'Détermination de {target}', target=target, **kwargs)
    if target == "Caractéristiques de l'usinage":
        set_general_machining_characteristics(win)

    else:
        set_operation_window(win, target)

    res = win.result
    action = win.action

    win.destroy()

    return res, action