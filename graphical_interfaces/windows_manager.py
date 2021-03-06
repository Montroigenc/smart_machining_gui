import tkinter as tk

from graphical_interfaces.graphical_interfaces import Window, VerticalScrolledFrame
from graphical_interfaces.formulas import *


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
    start_frame = [*win.frames.values()][0]
    frame = tk.Frame(start_frame, name='general_machining_characteristics')

    win.append_label_row(["Opération :", "Fraisage"], root=frame, row=1, names=['', 'operation'])
    win.append_entry_row("Outil", root=frame, row=2, ent_name='tool')
    win.append_entry_row("Diamètre", root=frame, row=3, ent_name='diameter')
    win.append_entry_row("Nombre de dents", root=frame, row=4, ent_name='n_teeth')
    win.append_entry_row("Opérateur", row=5, root=frame, ent_name='user_name')
    win.append_date(root=frame, row=6)
    win.append_entry_row("Lubrification", row=7, root=frame, ent_name='lubrication')
    win.append_entry_row("Commentaires", row=8, root=frame, ent_name='comments')

    frame.pack(padx=20, pady=20)

    # Set buttons
    buttons_frame = tk.Frame(start_frame, name='buttons')
    tk.Button(buttons_frame, text=" Suivant ", command=lambda **kwargs: win.change_program_state(actions=["get_data", "next"], action_root=[frame]), pady=5).grid(row=0, column=0)
    tk.Button(buttons_frame, text=" Télécharger un document existant ", command=lambda **kwargs: win.change_program_state(actions=["select_file_existing", "back"], action_root=[frame]), pady=5).grid(row=0, column=1)
    buttons_frame.pack(padx=20, pady=20)

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
                   "Avance par dent fz (mm/tr)",]

        dynamic_table_headers = ["Mesure n°", "Engagement axial ap (mm)", "Engagement radial ae (mm)", "Épaisseur de coupe h (mm)", "Fichier de mesure", "Pc (W)", "Énergie spécifique de coupe Wc (W)", "Section de coupe AD", "Statut"]
    elif target == 'Q max':
        entries = ["Engagement axial ap (mm)",
                   "Engagement radial ae (mm)"]
        dynamic_table_headers = ["Mesure n°", "Vitesse de coupe Vc (m/min)", "Vitesse de broche N", "Vitesse d'avance Vf (m/min)", "Avance par dent fz (mm/tr)", "Épaisseur de coupe h (mm)", "Fichier de mesure", "Pc (W)", "Wc (W)", "Débit de copeaux Q", "Statut"]

    return entries, dynamic_table_headers


def set_operation_window_constant_parameters(win, entries):
    start_frame = [*win.frames.values()][0]

    # Set constant parameters table
    input_parameters_frame = tk.Frame(start_frame, name="input_parameters", highlightthickness=2, highlightbackground="black")

    win.append_label_row(["Paramètres d’entrée", "Valeurs utilisées"], root=input_parameters_frame, header=True)

    for i, entry in enumerate(entries):
        win.append_entry_row(entry, row=i + 1, root=input_parameters_frame)

    input_parameters_frame.pack(padx=15, pady=15)

    # Set buttons
    buttons_frame = tk.Frame(start_frame, name="buttons")
    btn_next = tk.Button(buttons_frame, text="Valider",
                         command=lambda **kwargs: win.change_program_state(actions=["get_data", "next"], action_root=[input_parameters_frame]),
                         padx=10, pady=5, font='Helvetica 11 bold')
    btn_back = tk.Button(buttons_frame, text="Revenir à la fenêtre précédente",
                         command=lambda **kwargs: win.change_program_state(actions=["back"], action_root=[input_parameters_frame]),
                         padx=10, pady=5, font='Helvetica 11 bold')

    btn_next.grid(row=0, column=0, padx=20, pady=5)
    btn_back.grid(row=0, column=2, padx=20, pady=5)
    buttons_frame.pack(padx=15, pady=15)


def set_operation_window_dynamic_parameters(win, target, table_headers):
    start_frame = [*win.frames.values()][0]

    # SET MAIN FRAME
    # main_frame = tk.Frame(start_frame, name="main")

    # Set Vc input parameters table
    constant_parameters_frame = tk.Frame(start_frame, name="constant_parameters", highlightthickness=2, highlightbackground="black")

    win.append_label_row(["Paramètres d’entrée", "Valeurs utilisées"], root=constant_parameters_frame, header=True)

    if target == 'AD max':
        d = float(win.data['general_parameters']['diameter'])
        Vc = float(win.result['input_parameters']['vitesse de coupe vc (m/min)'])
        fz = float(win.result['input_parameters']['avance par dent fz (mm/tr)'])
        z = float(win.data['general_parameters']['n_teeth'])

        N = compute_N(Vc, d)

        win.result['input_parameters']["vitesse de broche n"] = N
        win.result['input_parameters']["vitesse d'avance vf (m/min)"] = compute_Vf(N, fz, z)

    for i, (key, entry) in enumerate(win.result['input_parameters'].items()):
        win.append_label_row([key, entry], row=i + 1, root=constant_parameters_frame)

    constant_parameters_frame.pack(padx=15, pady=15)
    # constant_parameters_frame.grid(row=0, column=0, sticky='news')

    # Set dynamic table frame
    dynamic_parameters_frame = VerticalScrolledFrame(start_frame, interior_name=f'dynamic_parameters_{target}')

    # Set dynamic table headers
    win.append_label_row(table_headers + [""], root=dynamic_parameters_frame.interior, header=True)

    # Additional search parameter
    if 'max' in target:
        search_param = f"{['AD max', 'Q max'][['AD max', 'Q max'].index(target)]}"
        search_param_lbl = tk.Label(win, text=f"{search_param} = ", width=22, font='Helvetica 11 bold', name='search_param', borderwidth=2, relief="solid")

    # Set dynamic table first row
    if win.data['debug'] > 1:
        for i in range(10):
            win.append_dynamic_row(root=dynamic_parameters_frame.interior)
    else:
        win.append_dynamic_row(root=dynamic_parameters_frame.interior)

    dynamic_parameters_frame.pack(padx=15, pady=15)
    # dynamic_parameters_frame.grid(row=0, column=1, sticky='news')

    # Additional search parameter packed here to avoid error while non existing search parameter widget while debugging with append_dynamic_row
    if 'max' in target:
        search_param_lbl.pack(padx=15, pady=15)
        # dynamic_parameters_frame.grid(row=0, column=2, sticky='news')

    # Set buttons
    buttons_frame = tk.Frame(start_frame, name="buttons")
    buttons_frame.pack(padx=15, pady=15)
    win.append_buttons(table_headers, root=buttons_frame, root_table=[constant_parameters_frame, dynamic_parameters_frame.interior])

    # if target in ['Vc min', 'f min']:
    #     loading_data_graph_frame = GraphFrameLoadingData(win, name='loading_data_graph_frame')
    #     loading_data_graph_frame.grid(row=0, column=0, sticky="nsew")

    # main_frame.grid(row=0, column=0, sticky="nsew")


# def show_tangent_graph(data, win):
#     # DATA FRAME
#     data_frame = tk.Frame(win.frames['frame_0'], name='data_frame')
#
#     # DATA TABLE
#     table_frame = VerticalScrolledFrame(data_frame, interior_name='table')
#     x_param_name = "Vitesse de coupe Vc (m/min)" if win.target == "Vc min" else "Épaisseur de coupe h (mm)"
#
#     win.append_label_row([x_param_name, "Wc (W*min/cm3)"], root=table_frame.interior, header=True)
#
#     for row_idx, (vci, wci) in enumerate(zip(data[0], data[1])):
#         win.append_label_row([vci, wci], root=table_frame.interior, row=row_idx+1)
#
#     # SET VC MIN RESULT ENTRY
#     results_frame = tk.Frame(data_frame, name='results_frame')
#     win.append_entry_row(win.target, root=results_frame, ent_field=np.min(data[1]))
#
#     # BUTTONS
#     btns_frame = tk.Frame(data_frame, name='buttons_frame')
#
#     next_btn = tk.Button(btns_frame, text="Valider", command=lambda **kwargs: win.change_program_state(actions=["get_target", "next"], root=win), padx=10, pady=5, font='Helvetica 11 bold')
#     return_btn = tk.Button(btns_frame, text="Revenir à la fenêtre précédente", command=lambda **kwargs: win.change_program_state(actions=["back"], action_root=[table_frame.interior]), padx=10, pady=5, font='Helvetica 11 bold')
#
#     next_btn.grid(row=1, column=0, padx=10, pady=10)
#     return_btn.grid(row=1, column=1, padx=10, pady=10)
#
#     data_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)
#
#     # GRAPH
#     axis_labels = {'x_lab': x_param_name, 'y_lab': "Énergie spécifique de coupe Wc (W)"}
#
#     figure, res = plot_tangent_data(data, axis_labels)
#
#     graph_frame = GraphFrame(win.frames['frame_0'], name='graph_frame', figure=figure)
#     graph_frame.pack(side=tk.RIGHT, padx=20, pady=20)
#
#     # pack inner data table
#     table_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)
#     results_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)
#     btns_frame.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)
#
#     return res


def show_tangent_graph(data, win):
    win.show_frame('frame_1')
    win.frames['frame_1'].generate_fig()
    win.frames['frame_1'].generate_widgets_tangent(data)

    win()

    res = win.frames['frame_1'].res
    win.show_frame('frame_0')

    return res


def set_operation_window(win, target):
    step = 0
    entries, dynamic_table_headers = get_operation_window_headers(target)

    while 0 <= step < 3:
        if step == 0:
            if win.data['debug'] > 2:
                win.result['input_parameters'] = dict(zip(entries, np.ones_like(entries)))
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

                win.set_win_title(f'Résultats {target}')
                res = show_tangent_graph(dynamic_table_values, win)

            elif target in ['AD max', 'Q max']:
                win.result[target] = [win.max_params['AD'], win.max_params['Q']][['AD max', 'Q max'].index(target)]

            step = step + 1 if win.action == 'next' else step - 1


def set_user_window(app_name, target, **kwargs):
    win = Window(app_name, window_title=f'Détermination de {target}', target=target, **kwargs)
    if target == "Caractéristiques de l'usinage":
        set_general_machining_characteristics(win)
    else:
        set_operation_window(win, target)

    res = win.result
    action = win.action

    win.destroy()

    return res, action