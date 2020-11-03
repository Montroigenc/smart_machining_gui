import matplotlib.pyplot as plt
import numpy as np
# from sklearn.neural_network import MLPRegressor
import unidecode
import tkinter as tk
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


def plot_tangent_data(data, axis_labels=None):
    # x, y = np.array(data['x']), np.array(data['y'])
    x, y = data[0], data[1]
    f = plt.figure(figsize=(5, 5), dpi=100)
    a = f.add_subplot(111)

    a.plot(x, y, "k", marker='o', label='original data')
    xmin, xmax, ymin, ymax = plt.axis()
    view_tolerance_x = (xmax - xmin) * 0.01
    view_tolerance_y = (ymax - ymin) * 0.01
    a.set_xlim(xmin - view_tolerance_x, xmax + view_tolerance_x)
    a.set_ylim(ymin - view_tolerance_y, ymax + view_tolerance_y)

    try:
        # 1st derivative
        yfirst = np.diff(y, 1) / np.diff(x, 1)

        # first tangent
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

        first_tangent = Tangent(x_in, y_in)

        xmin_ft_plot, xmax_ft_plot = xmin - view_tolerance_x, xmax + view_tolerance_x
        a.plot(tuple([xmin_ft_plot, xmax_ft_plot]), tuple([first_tangent(xmin_ft_plot), first_tangent(xmax_ft_plot)]), color='g', linestyle='--')

        # second tangent
        x_in, y_in, end = [], [], False
        for idx, val in enumerate(yfirst):
            c = val > diff * 0.95 + yfirst.min()
            if len(x_in) > 0 and not c:
                break
            elif c:
                x_in.append(x[idx])
                y_in.append(y[idx])

        second_tangent = Tangent(x_in, y_in)
        a.plot(tuple([xmin_ft_plot, xmax_ft_plot]), tuple([second_tangent(xmin_ft_plot), second_tangent(xmax_ft_plot)]), color='g', linestyle='--')

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
        means_dict = {f"{unidecode.unidecode(axis_labels['x_lab'].lower())}": means[0], f"{unidecode.unidecode(axis_labels['y_lab'].lower())}": means[1]}

        x_param_name = "Vc" if axis_labels['x_lab'] == "Vitesse de coupe Vc (m/min)" else "h"

        a.text(xmax * 0.4, ymax * 0.75, f'{x_param_name} min={means[1]:.2f}', fontsize=12)
        a.text(xmax * 0.4, ymax * 0.7, f'Wc moyenne={means[0]:.2f}', fontsize=12)
    except:
        tk.messagebox.showerror("Error", sys.exc_info()[0], icon='error')
        means_dict = None

    # set axis labels
    a.set_xlabel(axis_labels['x_lab'])
    a.set_ylabel(axis_labels['y_lab'])

    return f, means_dict


def plot_tangent_data_2(data, axis_labels=None):
    x, y = np.array(data['x']), np.array(data['y'])
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

    # first tangent
    diff = yfirst.max() - yfirst.min()
    last_point_idx = (yfirst < diff * 0.2 + yfirst.min()).argmin() + 1
    first_tangent = Tangent(x[:last_point_idx + 1], y[:last_point_idx + 1])
    xmin_ft_plot, xmax_ft_plot = xmin - view_tolerance_x, xmax + view_tolerance_x
    a.plot(tuple([xmin_ft_plot, xmax_ft_plot]), tuple([first_tangent(xmin_ft_plot), first_tangent(xmax_ft_plot)]), color='g', linestyle='--')

    # second tangent
    x_in, y_in, end = [], [], False
    for idx, val in enumerate(yfirst):
        c = val > diff * 0.95 + yfirst.min()
        if len(x_in) > 0 and not c:
            break
        elif c:
            x_in.append(x[idx])
            y_in.append(y[idx])

    second_tangent = Tangent(x_in, y_in)
    a.plot(tuple([xmin_ft_plot, xmax_ft_plot]), tuple([second_tangent(xmin_ft_plot), second_tangent(xmax_ft_plot)]), color='g', linestyle='--')

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
    vc_min_min = (x[closest_idxs[0]] * rest[1] + x[closest_idxs[1]] * rest[0], y_intersection)
    a.plot(vc_min_min[0], vc_min_min[1], color='r', marker='o', markersize=8)
    a.text(vc_min_min[0] + view_tolerance_x, vc_min_min[1] + view_tolerance_y, f'B ({vc_min_min[0]:.2f}, {vc_min_min[1]:.2f})', fontsize=12)

    # vertical intersection
    diffs = np.abs(x - x_intersection)
    closest_idxs = diffs.argsort()[:2]
    rest = diffs[closest_idxs] / np.sum(diffs[closest_idxs])
    vc_min_max = (x_intersection, y[closest_idxs[0]] * rest[1] + y[closest_idxs[1]] * rest[0])
    a.plot(vc_min_max[0], vc_min_max[1], color='r', marker='o', markersize=8)
    a.text(vc_min_max[0] + view_tolerance_x, vc_min_max[1] + view_tolerance_y, f'C ({vc_min_max[0]:.2f}, {vc_min_max[1]:.2f})', fontsize=12)

    if axis_labels is not None:
        a.set_xlabel(axis_labels['x_lab'])
        a.set_ylabel(axis_labels['y_lab'])

    return f


def get_dummy_data_one_inflexion_point(length):
    data = dict()
    data['x'] = [i for i in range(length)]
    data['y'] = [np.exp(-i/4) for i in range(length)]

    return data


if __name__ == "__main__":
    data = get_dummy_data_one_inflexion_point(20)
    plot_tangent_data_2(data)
    plt.show()