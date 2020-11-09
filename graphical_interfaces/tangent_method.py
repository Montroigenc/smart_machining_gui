import matplotlib.pyplot as plt
import numpy as np
# from sklearn.neural_network import MLPRegressor
import unidecode
import tkinter as tk
from tkinter import messagebox
import sys


def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


class Tangent:
    def __init__(self, ft_x, ft_y):
        # try:
        self.m, self.c = np.polyfit(ft_x, ft_y, 1)
        # except AssertionError as error:
        #     print(error)

    def __call__(self, x):
        return self.m * x + self.c

    def get_params(self):
        return self.m, + self.c


def get_lines_intersection(m1, c1, m2, c2):
    x = (c2 - c1) / (m1 - m2)
    y = m1 * x + c1
    return x, y


def plot_tangent_data(frame, data, axis_labels=None):
    means_dict = None

    x, y = data[0], data[1]
    frame.subplot.plot(x, y, "k", marker='o', label='original data')

    if True:
        # xmin, xmax, ymin, ymax = plt.axis()
        # xmin, xmax = frame.subplot.get_xlim()
        # ymin, ymax = frame.subplot.get_ylim()
        # view_tolerance_x = (xmax - xmin) * 0.01
        # view_tolerance_y = (ymax - ymin) * 0.01

        xmin, xmax = x.min(), x.max()
        ymin, ymax = y.min(), y.max()
        view_tolerance_x = (xmax - xmin) * 0.05
        view_tolerance_y = (ymax - ymin) * 0.05

        frame.subplot.set_xlim(xmin - view_tolerance_x, xmax + view_tolerance_x)
        frame.subplot.set_ylim(ymin - view_tolerance_y, ymax + view_tolerance_y)

        # try:
        # 1st derivative
        yfirst = np.diff(y, 1) / np.diff(x, 1)

        # 1ST TANGENT
        diff = yfirst.max() - yfirst.min()

        x_in, y_in, end = [], [], False
        yfirst_min = yfirst.min()
        for idx, val in enumerate(yfirst):
            c = val < diff * 0.75 + yfirst_min
            if len(x_in) > 0 and not c:
                break
            elif c:
                x_in.append(x[idx])
                y_in.append(y[idx])

        if len(x_in) > 0:
            first_tangent = Tangent(x_in, y_in)

            xmin_ft_plot, xmax_ft_plot = xmin - view_tolerance_x, xmax + view_tolerance_x
            frame.subplot.plot(tuple([xmin_ft_plot, xmax_ft_plot]), tuple([first_tangent(xmin_ft_plot), first_tangent(xmax_ft_plot)]), color='g', linestyle='--')

        # 2nd TANGENT
        x_in, y_in, end = [], [], False
        for idx, val in enumerate(yfirst):
            c = val > diff * 0.95 + yfirst.min()
            if len(x_in) > 0 and not c:
                break
            elif c:
                x_in.append(x[idx])
                y_in.append(y[idx])

        if len(x_in) > 0:
            second_tangent = Tangent(x_in, y_in)
            frame.subplot.plot(tuple([xmin_ft_plot, xmax_ft_plot]), tuple([second_tangent(xmin_ft_plot), second_tangent(xmax_ft_plot)]), color='g', linestyle='--')

            # get the two tangents intersection
            m1, c1 = first_tangent.get_params()
            m2, c2 = second_tangent.get_params()
            x_intersection, y_intersection = get_lines_intersection(m1, c1, m2, c2)
            frame.subplot.plot(x_intersection, y_intersection, color='r', marker='o', markersize=8)
            frame.subplot.text(x_intersection + view_tolerance_x, y_intersection + view_tolerance_y, 'A', fontsize=12)

            # get orthogonal points in the original function
            frame.subplot.axvline(x_intersection, linestyle='--', color='r')
            frame.subplot.axhline(y_intersection, linestyle='--', color='r')

            # horizontal intersection
            diffs = np.abs(y - y_intersection)
            closest_idxs = diffs.argsort()[:2]
            rest = diffs[closest_idxs] / np.sum(diffs[closest_idxs])
            vc_min_min = np.array([x[closest_idxs[0]] * rest[1] + x[closest_idxs[1]] * rest[0], y_intersection])
            frame.subplot.plot(vc_min_min[0], vc_min_min[1], color='r', marker='o', markersize=8)
            frame.subplot.text(vc_min_min[0] + view_tolerance_x, vc_min_min[1] + view_tolerance_y, f'B {vc_min_min[0]:.2f}, {vc_min_min[1]:.2f}', fontsize=12)

            # vertical intersection
            diffs = np.abs(x - x_intersection)
            closest_idxs = diffs.argsort()[:2]
            rest = diffs[closest_idxs] / np.sum(diffs[closest_idxs])
            vc_min_max = np.array([x_intersection, y[closest_idxs[0]] * rest[1] + y[closest_idxs[1]] * rest[0]])
            frame.subplot.plot(vc_min_max[0], vc_min_max[1], color='r', marker='o', markersize=8)
            frame.subplot.text(vc_min_max[0] + view_tolerance_x, vc_min_max[1] + view_tolerance_y, f'C {vc_min_max[0]:.2f}, {vc_min_max[1]:.2f}', fontsize=12)

            means = (vc_min_max + vc_min_min) / 2

            if axis_labels is not None:
                means_dict = {f"{unidecode.unidecode(axis_labels['x_lab'].lower())}": means[0], f"{unidecode.unidecode(axis_labels['y_lab'].lower())}": means[1]}
                # set axis labels
                frame.subplot.set_xlabel(axis_labels['x_lab'])
                frame.subplot.set_ylabel(axis_labels['y_lab'])

                x_param_name = "Vc" if axis_labels['x_lab'] == "Vitesse de coupe Vc (m/min)" else "h"

                frame.subplot.text(xmax * 0.4, ymax * 0.75, f'{x_param_name} min={means[1]:.2f}', fontsize=12)
                frame.subplot.text(xmax * 0.4, ymax * 0.7, f'Wc moyenne={means[0]:.2f}', fontsize=12)

        # except:
        #     messagebox.showerror("Error", sys.exc_info()[0], icon='error')
        #     means_dict = None

    frame.canvas.draw()
    frame.toolbar.update()

    return means_dict


def plot_tangent_data_trial(data, axis_labels=None):
    x, y = data[0], data[1]
    f = plt.figure(figsize=(5, 5), dpi=100)
    a = f.add_subplot(111)

    a.plot(x, y, "k", marker='o', label='original data')
    xmin, xmax, ymin, ymax = plt.axis()
    view_tolerance_x = (xmax - xmin) * 0.01
    view_tolerance_y = (ymax - ymin) * 0.01
    a.set_xlim(xmin - view_tolerance_x, xmax + view_tolerance_x)
    a.set_ylim(ymin - view_tolerance_y, ymax + view_tolerance_y)

    # 1st derivative
    yfirst = np.diff(y, 1) / np.diff(x, 1)

    # 1ST TANGENT
    diff = yfirst.max() - yfirst.min()

    x_in, y_in, end = [], [], False
    yfirst_min = yfirst.min()
    for idx, val in enumerate(yfirst):
        c = val < diff * 0.75 + yfirst_min
        if len(x_in) > 0 and not c:
            break
        elif c:
            x_in.append(x[idx])
            y_in.append(y[idx])
            a.plot(x[idx], y[idx], color='green', marker='o')

    first_tangent = Tangent(x_in, y_in)

    xmin_ft_plot, xmax_ft_plot = xmin - view_tolerance_x, xmax + view_tolerance_x
    a.plot(tuple([xmin_ft_plot, xmax_ft_plot]), tuple([first_tangent(xmin_ft_plot), first_tangent(xmax_ft_plot)]), color='g', linestyle='--')

    # 2nd TANGENT
    x_in, y_in, end = [], [], False
    for idx, val in enumerate(yfirst):
        c = val > diff * 0.95 + yfirst.min()
        if len(x_in) > 0 and not c:
            break
        elif c:
            x_in.append(x[idx])
            y_in.append(y[idx])
            a.plot(x[idx], y[idx], color='yellow', marker='o')

    second_tangent = Tangent(x_in, y_in)
    a.plot(tuple([xmin_ft_plot, xmax_ft_plot]), tuple([second_tangent(xmin_ft_plot), second_tangent(xmax_ft_plot)]), color='y', linestyle='--')

    # get the two tangents intersection
    m1, c1 = first_tangent.get_params()
    m2, c2 = second_tangent.get_params()
    x_intersection, y_intersection = get_lines_intersection(m1, c1, m2, c2)
    a.plot(x_intersection, y_intersection, color='r', marker='o', markersize=8)
    a.text(x_intersection + view_tolerance_x, y_intersection + view_tolerance_y, 'A', fontsize=12)

    # get orthogonal points in the original function
    a.axvline(x_intersection, linestyle='--', color='r')
    a.axhline(y_intersection, linestyle='--', color='r')

    # horizontal intersection
    diffs = np.abs(y - y_intersection)
    closest_idxs = diffs.argsort()[:2]
    rest = diffs[closest_idxs] / np.sum(diffs[closest_idxs])
    vc_min_min = np.array([x[closest_idxs[0]] * rest[1] + x[closest_idxs[1]] * rest[0], y_intersection])
    a.plot(vc_min_min[0], vc_min_min[1], color='r', marker='o', markersize=8)
    a.text(vc_min_min[0] + view_tolerance_x, vc_min_min[1] + view_tolerance_y, f'B {vc_min_min[0]:.2f}, {vc_min_min[1]:.2f}', fontsize=12)

    # vertical intersection
    diffs = np.abs(x - x_intersection)
    closest_idxs = diffs.argsort()[:2]
    rest = diffs[closest_idxs] / np.sum(diffs[closest_idxs])
    vc_min_max = np.array([x_intersection, y[closest_idxs[0]] * rest[1] + y[closest_idxs[1]] * rest[0]])
    a.plot(vc_min_max[0], vc_min_max[1], color='r', marker='o', markersize=8)
    a.text(vc_min_max[0] + view_tolerance_x, vc_min_max[1] + view_tolerance_y, f'C {vc_min_max[0]:.2f}, {vc_min_max[1]:.2f}', fontsize=12)

    means = (vc_min_max + vc_min_min) / 2

    if axis_labels is not None:
        means_dict = {f"{unidecode.unidecode(axis_labels['x_lab'].lower())}": means[0], f"{unidecode.unidecode(axis_labels['y_lab'].lower())}": means[1]}
        # set axis labels
        a.set_xlabel(axis_labels['x_lab'])
        a.set_ylabel(axis_labels['y_lab'])

        x_param_name = "Vc" if axis_labels['x_lab'] == "Vitesse de coupe Vc (m/min)" else "h"

        a.text(xmax * 0.4, ymax * 0.75, f'{x_param_name} min={means[1]:.2f}', fontsize=12)
        a.text(xmax * 0.4, ymax * 0.7, f'Wc moyenne={means[0]:.2f}', fontsize=12)
    else:
        means_dict = None

    return f, means_dict


def get_dummy_data_one_inflexion_point(length):
    data = []
    data.append(np.asarray([i for i in range(length)]))
    data.append(np.asarray([np.exp(-i/4) for i in range(length)]))

    return data


if __name__ == "__main__":
    from graphical_interfaces.graphical_interfaces import VerticalScrolledFrame, GraphFrame, Window
    import graphical_interfaces

    def show_graphic(data, win):
        # DATA FRAME
        data_frame = tk.Frame(win, name='data_frame')

        # DATA TABLE
        table_frame = VerticalScrolledFrame(data_frame, interior_name='table')
        x_param_name = "Vitesse de coupe Vc (m/min)" if win.target == "Vc min" else "Épaisseur de coupe h (mm)"

        win.append_label_row([x_param_name, "Wc (W*min/cm3)"], root=table_frame.interior, header=True)

        # for row_idx, (vci, wci) in enumerate(zip(data['x'], data['y'])):
        for row_idx, (vci, wci) in enumerate(zip(data[0], data[1])):
            win.append_label_row([vci, wci], root=table_frame.interior, row=row_idx + 1)

        # SET VC MIN RESULT ENTRY
        results_frame = tk.Frame(data_frame, name='results_frame')
        win.append_entry_row(win.target, root=results_frame, ent_field=np.min(data[1]))

        # BUTTONS
        btns_frame = tk.Frame(data_frame, name='buttons_frame')

        next_btn = tk.Button(btns_frame, text="Valider", command=lambda **kwargs: win.change_program_state(actions=["get_target", "next"], root=win), padx=10, pady=5, font='Helvetica 11 bold')
        return_btn = tk.Button(btns_frame, text="Revenir à la fenêtre précédente", command=lambda **kwargs: win.change_program_state(actions=["back"], action_root=[table_frame.interior]), padx=10, pady=5, font='Helvetica 11 bold')

        next_btn.grid(row=1, column=0, padx=10, pady=10)
        return_btn.grid(row=1, column=1, padx=10, pady=10)

        data_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)

        # GRAPH
        axis_labels = {'x_lab': x_param_name, 'y_lab': "Énergie spécifique de coupe Wc (W)"}

        figure, res = plot_tangent_data_trial(data, axis_labels)

        graph_frame = GraphFrame(win, name='graph_frame', figure=figure)
        graph_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        # pack inner data table
        table_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)
        results_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)
        btns_frame.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)

        return res

    data = get_dummy_data_one_inflexion_point(20)
    win = Window('DUMMY')
    show_graphic(data, win)
    plt.show()