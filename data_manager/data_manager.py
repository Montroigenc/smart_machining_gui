# from pandas_ods_reader import read_ods
import matplotlib.pyplot as plt
# import seaborn as sns
import numpy as np
from tqdm import tqdm, trange
import pandas as pd

import tkinter as tk
from tkinter import filedialog
from matplotlib.patches import Patch

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

new_btn_press = False
btn_press_x_position = -1
btn_press_axis_row = -1
btn_press_button = -1


def get_file_name():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(title='Select grayscale image')


def get_pc_from_machining_file(file_path_):
    global new_btn_press, btn_press_x_position, btn_press_axis_row, btn_press_button

    def onclick(event):
        global new_btn_press, btn_press_x_position, btn_press_axis_row, btn_press_button
        new_btn_press = True
        btn_press_x_position = event.xdata
        btn_press_axis_row = event.inaxes.rowNum
        btn_press_button = event.button

    # load a sheet based on its name
    data_frame = pd.read_csv(file_path_, sep=";", error_bad_lines=False)
    # data_time = data_frame.iloc[18:-1, 0].astype(int)
    raw_data = data_frame.iloc[18:-1, 1].astype(int)

    # sampled_raw_data = pd.DataFrame()
    # for c in raw_data.columns:
    #     sampled_raw_data[c] = raw_data[c][::50]
    #
    # raw_data = sampled_raw_data

    t = raw_data.shape[0]

    # get edges
    normalized_data = raw_data - raw_data.min()
    normalized_data /= normalized_data.max()

    # smoothed_data = normalized_data.rolling(window=2000, win_type='gaussian', center=True).mean(std=0.5)
    # smoothed_data = normalized_data.rolling(window=4000).mean()
    smoothed_data = normalized_data

    derivative_data = smoothed_data.diff()

    noise_threshold = 0.0001  # 0.00015
    window_width = 3
    momentum_threshold = 100
    edges = {}
    for measure_idx, header in tqdm(enumerate(raw_data.columns.values), desc='measures loop'):
        measure_edges = {'positive_ini': [], 'positive_end': [], 'negative_ini': [], 'negative_end': [], 'positive_max': [], 'negative_min': []}
        positive_detected, negative_detected = False, False
        max_val, min_val = -9e3, 9e3
        hill_ini, descent_ini = 0, 0
        momentum_count = 0

        for t_idx in trange(window_width, t - window_width, desc='time loop'):
            if np.any(np.isnan(derivative_data[header].values[t_idx - window_width:t_idx + window_width + 1])):
                continue

            previous_val, posterior_val = derivative_data[header][t_idx - window_width:t_idx].median(), derivative_data[header][t_idx:t_idx + window_width + 1].median()
            val = (previous_val + posterior_val) / 2

            if positive_detected:
                if val > max_val:
                    max_val = val
                    max_idx = t_idx
                    momentum_count -= 1
                else:
                    momentum_count += 1
                    if momentum_count > momentum_threshold:
                        if max_val > noise_threshold:
                            measure_edges['positive_max'].append(max_idx)
                            measure_edges['positive_ini'].append(hill_ini)
                        positive_detected = False
                        max_val = -9e3
                        momentum_count = 0

            elif negative_detected:
                if val < min_val:
                    min_val = val
                    min_idx = t_idx
                    momentum_count -= 1
                else:
                    momentum_count += 1
                    if momentum_count > momentum_threshold:
                        if min_val < -noise_threshold:
                            measure_edges['negative_min'].append(min_idx)
                            measure_edges['negative_ini'].append(descent_ini)
                        negative_detected = False
                        min_val = 9e3
                        momentum_count = 0

            else:
                if previous_val < posterior_val:
                    hill_ini = t_idx
                    # positive edge
                    hill_ini = t_idx
                    positive_detected = True
                    negative_detected = False
                else:
                    # negative edge
                    descent_ini = t_idx
                    positive_detected = False
                    negative_detected = True

        edges[header] = measure_edges

    #####################################################3
    # plot data and get low and high values
    fig, axes = plt.subplots(num=9, nrows=raw_data.shape[1], ncols=1, sharex=True)

    for ax, header in zip(axes.flatten(), raw_data.columns.values):
        edges[header]['plots'] = []
        ax.plot(range(t), raw_data[header].values, color='b')
        ax2 = ax.twinx()
        ax2.plot(range(t), derivative_data[header].values, color='g', linestyle='dashed')

        ax.set_ylabel(header)

        low_vals, high_vals = [], []

        if len(edges[header]['positive_max']) == 0:
            low_vals.extend(raw_data[header].values)
            axinf = ax.axvspan(0, t - 1, ymin=0.0, ymax=1.0, alpha=0.5, color='green')
            edges[header]['plots'].append(axinf)
        else:
            for e_idx, edge in enumerate(edges[header]['positive_max']):
                low_vals.extend(raw_data[header].values[:edges[header]['positive_ini'][e_idx]])
                axinf = ax.axvspan(0, edges[header]['positive_ini'][e_idx], ymin=0.0, ymax=1.0, alpha=0.5, color='green')
                edges[header]['plots'].append(axinf)

                if len(edges[header]['negative_ini']) >= e_idx + 1:
                    high_vals.extend(raw_data[header].values[edge:edges[header]['negative_ini'][e_idx]])
                    axinf = ax.axvspan(edge, edges[header]['negative_ini'][e_idx], ymin=0.0, ymax=1.0, alpha=0.5, color='red')
                    edges[header]['plots'].append(axinf)
                else:
                    high_vals.extend(raw_data[header].values[edge:])
                    axinf = ax.axvspan(edge, t - 1, ymin=0.0, ymax=1.0, alpha=0.5, color='red')
                    edges[header]['plots'].append(axinf)

                if len(edges[header]['negative_min']) >= e_idx and len(edges[header]['negative_min']) > 0:
                    if len(edges[header]['positive_ini']) > e_idx + 1:
                        low_vals.extend(raw_data[header].values[edges[header]['negative_min'][e_idx]:edges[header]['positive_ini'][e_idx + 1]])
                        axinf = ax.axvspan(edges[header]['negative_min'][e_idx], edges[header]['positive_ini'][e_idx + 1], ymin=0.0, ymax=1.0, alpha=0.5, color='green')
                        edges[header]['plots'].append(axinf)
                    else:
                        low_vals.extend(raw_data[header].values[edges[header]['negative_min'][e_idx]:])
                        axinf = ax.axvspan(edges[header]['negative_min'][e_idx], t - 1, ymin=0.0, ymax=1.0, alpha=0.5, color='green')
                        edges[header]['plots'].append(axinf)

    fig.canvas.mpl_connect('button_press_event', onclick)

    # modified_axes_row_idx = [True] * len(axes.flatten())
    new_edges = edges.copy()
    for e in new_edges.values():
        e['left_press_idx'] = 0
        e['right_press_idx'] = 0

        e['low_level_ini'] = -1
        e['low_level_end'] = -1

        e['high_level_ini'] = -1
        e['high_level_end'] = -1

    plt.show(False)

    while plt.fignum_exists(fig.number):
        plt.pause(0.0001)

        if new_btn_press:
            new_btn_press = False

            if btn_press_button == 1:
                if new_edges[raw_data.columns[btn_press_axis_row]]['left_press_idx'] % 2 == 0:
                    new_edges[raw_data.columns[btn_press_axis_row]]['low_level_ini'] = int(btn_press_x_position)
                else:
                    new_edges[raw_data.columns[btn_press_axis_row]]['low_level_end'] = int(btn_press_x_position)

                new_edges[raw_data.columns[btn_press_axis_row]]['left_press_idx'] += 1

            elif btn_press_button == 3:
                if new_edges[raw_data.columns[btn_press_axis_row]]['right_press_idx'] % 2 == 0:
                    new_edges[raw_data.columns[btn_press_axis_row]]['high_level_ini'] = int(btn_press_x_position)
                else:
                    new_edges[raw_data.columns[btn_press_axis_row]]['high_level_end'] = int(btn_press_x_position)

                new_edges[raw_data.columns[btn_press_axis_row]]['right_press_idx'] += 1

        for ax, header in zip(axes.flatten(), raw_data.columns.values):
            if new_edges[header]['left_press_idx'] + new_edges[header]['right_press_idx'] > 0:
                while len(new_edges[header]['plots']):
                    new_edges[header]['plots'].pop(0).remove()

                bottom, top = ax.get_ylim()

                if new_edges[header]['left_press_idx'] > 0:
                    if new_edges[header]['low_level_ini'] != -1 and new_edges[header]['low_level_end'] != -1:
                        ax.axvspan(new_edges[header]['low_level_ini'], new_edges[header]['low_level_end'], ymin=0.0, ymax=1.0, alpha=0.5, color='g')
                        t = ax.text((new_edges[header]['low_level_ini'] + new_edges[header]['low_level_ini']) / 3 + new_edges[header]['low_level_ini'], (top - bottom) / 2 + bottom, 'niveau\nbas', fontsize=5, ha='center')
                        edges[header]['plots'].append(t)

                    elif new_edges[header]['low_level_ini'] == -1 and new_edges[header]['low_level_end'] != -1:
                        ax.axvline(x=new_edges[header]['low_level_end'], color='g')
                        t = ax.text(new_edges[header]['low_level_end'], bottom, 'fin niveau bas', rotation='vertical', fontsize=5)
                        edges[header]['plots'].append(t)

                    elif new_edges[header]['low_level_ini'] != -1 and new_edges[header]['low_level_end'] == -1:
                        ax.axvline(x=new_edges[header]['low_level_ini'], color='g')
                        t = ax.text(new_edges[header]['low_level_ini'], bottom, 'début niveau bas', rotation='vertical', fontsize=5)
                        edges[header]['plots'].append(t)

                if new_edges[header]['right_press_idx'] > 0:
                    if new_edges[header]['high_level_ini'] != -1 and new_edges[header]['high_level_end'] != -1:
                        ax.axvspan(new_edges[header]['high_level_ini'], new_edges[header]['high_level_end'], ymin=0.0, ymax=1.0, alpha=0.5, color='r')
                        t = ax.text((new_edges[header]['high_level_end'] + new_edges[header]['high_level_ini']) / 3 + new_edges[header]['high_level_ini'], (top - bottom) / 2 + bottom, 'niveau\nhaut', fontsize=5, ha='center')
                        edges[header]['plots'].append(t)

                    elif new_edges[header]['high_level_ini'] == -1 and new_edges[header]['high_level_end'] != -1:
                        ax.axvline(x=new_edges[header]['high_level_end'], color='r')
                        t = ax.text(new_edges[header]['high_level_end'], bottom, 'fin niveau haut', rotation='vertical', fontsize=5)
                        edges[header]['plots'].append(t)

                    elif new_edges[header]['high_level_ini'] != -1 and new_edges[header]['high_level_end'] == -1:
                        ax.axvline(x=new_edges[header]['high_level_ini'], color='r')
                        t = ax.text(new_edges[header]['high_level_ini'], bottom, 'début niveau haut', rotation='vertical', fontsize=5)
                        edges[header]['plots'].append(t)

    # set high and low values after manual checking
    results = dict()
    for ax, header in zip(axes.flatten(), raw_data.columns.values):
        if new_edges[header]['left_press_idx'] + new_edges[header]['right_press_idx']:
            high_val = np.mean(raw_data[header].values[new_edges[header]['high_level_ini']:new_edges[header]['high_level_end']])
            low_val = np.mean(raw_data[header].values[new_edges[header]['low_level_ini']:new_edges[header]['low_level_end']])
        else:
            high_val, low_val = np.nanmean(high_vals), np.nanmean(low_vals)

        results[header] = {'high_val': high_val, 'low_val': low_val, 'Pc': high_val - low_val}
        # print(f'{header} GAP:{high_val - low_val}, high_val: {high_val}, low_val: {low_val}')

    return results


def get_data_from_machining_file(file_path_):
    # load a sheet based on its name
    data_frame = pd.read_csv(file_path_, sep=";", error_bad_lines=False)

    raw_data = pd.DataFrame()
    raw_data['time'] = data_frame.iloc[18:-1, 0].astype(int)
    raw_data['values'] = data_frame.iloc[18:-1, 1].astype(int)

    t = raw_data.shape[0]

    # get edges
    normalized_data = (raw_data['values'] - raw_data['values'].min()).astype(float)
    normalized_data /= normalized_data.max()

    derivative_data = normalized_data.diff()
    derivative_smoothed_data = derivative_data
    derivative_smoothed_data /= derivative_smoothed_data.abs().max()

    noise_threshold = 0.022

    edges = {'sign_change': [], 'sign_change_idxs': []}

    valid_pos = derivative_smoothed_data.abs() > noise_threshold
    valid_time = raw_data['time'][valid_pos].values
    valid_values = derivative_smoothed_data[valid_pos].values
    valid_idxs = np.arange(t)[valid_pos]

    for idx in range(1, len(valid_time) - 1):
        if np.sign(valid_values[idx - 1]) != np.sign(valid_values[idx]) or np.sign(valid_values[idx + 1]) != np.sign(valid_values[idx]):
            edges['sign_change'].append(valid_time[idx])
            edges['sign_change_idxs'].append(valid_idxs[idx])

    return t, raw_data, normalized_data, derivative_smoothed_data, edges


# def get_pc_from_machining_file_unique_entry(file_path_, show=True, fig=None, ax=None):
#     global new_btn_press, btn_press_x_position, btn_press_button
#
#     def onclick(event):
#         global new_btn_press, btn_press_x_position, btn_press_button
#         new_btn_press = True
#         btn_press_x_position = event.xdata
#         btn_press_button = event.button
#
#     # # load a sheet based on its name
#     # data_frame = pd.read_csv(file_path_, sep=";", error_bad_lines=False)
#     #
#     # raw_data = pd.DataFrame()
#     # raw_data['time'] = data_frame.iloc[18:-1, 0].astype(int)
#     # raw_data['values'] = data_frame.iloc[18:-1, 1].astype(int)
#     #
#     # t = raw_data.shape[0]
#     #
#     # # get edges
#     # normalized_data = (raw_data['values'] - raw_data['values'].min()).astype(float)
#     # normalized_data /= normalized_data.max()
#     #
#     # derivative_data = normalized_data.diff()
#     # derivative_smoothed_data = derivative_data
#     # derivative_smoothed_data /= derivative_smoothed_data.abs().max()
#     #
#     # noise_threshold = 0.022
#     #
#     # edges = {'sign_change': [], 'sign_change_idxs': []}
#     #
#     # valid_pos = derivative_smoothed_data.abs() > noise_threshold
#     # valid_time = raw_data['time'][valid_pos].values
#     # valid_values = derivative_smoothed_data[valid_pos].values
#     # valid_idxs = np.arange(t)[valid_pos]
#     #
#     # for idx in range(1, len(valid_time) - 1):
#     #     if np.sign(valid_values[idx - 1]) != np.sign(valid_values[idx]) or np.sign(valid_values[idx + 1]) != np.sign(valid_values[idx]):
#     #         edges['sign_change'].append(valid_time[idx])
#     #         edges['sign_change_idxs'].append(valid_idxs[idx])
#
#     t, raw_data, normalized_data, derivative_smoothed_data, edges = get_data_from_machining_file(file_path_)
#
#     #####################################################
#     # plot data and get low and high values
#     if fig is None:
#         fig, ax = plt.subplots(num=9)
#
#     color = 'tab:red'
#     ax.set_xlabel('time (ms)')
#     ax.set_ylabel('Pc(W)', color=color)
#     # ax.plot(raw_data['time'], normalized_data.values, color=color)
#     ax.plot(raw_data['time'], raw_data['values'], color=color)
#     ax.tick_params(axis='y', labelcolor=color)
#
#     ax2 = ax.twinx()  # instantiate a second axes that shares the same x-axis
#
#     color = 'tab:blue'
#     ax2.set_ylabel('derivative', color=color)  # we already handled the x-label with ax
#     ax2.plot(raw_data['time'], derivative_smoothed_data.values, color=color)
#     ax2.tick_params(axis='y', labelcolor=color)
#
#     fig.tight_layout()  # otherwise the right y-label is slightly clipped
#
#     edges['plots'] = []
#     low_vals, high_vals = [], []
#
#     if len(edges['sign_change']) < 2:
#         low_vals.extend(normalized_data.values)
#         axinf = ax.axvspan(0, t - 1, ymin=0.0, ymax=1.0, alpha=0.5, color='green')
#         edges['plots'].append(axinf)
#     else:
#         low_vals.extend(raw_data['values'].values[edges['sign_change_idxs'][0]:edges['sign_change_idxs'][1]])
#         axinf = ax.axvspan(edges['sign_change'][0], edges['sign_change'][1], ymin=0.0, ymax=1.0, alpha=0.5, color='green')
#         edges['plots'].append(axinf)
#
#         high_vals.extend(raw_data['values'].values[edges['sign_change_idxs'][2]:edges['sign_change_idxs'][3]])
#         axinf = ax.axvspan(edges['sign_change'][2], edges['sign_change'][3], ymin=0.0, ymax=1.0, alpha=0.5, color='red')
#         edges['plots'].append(axinf)
#
#     fig.canvas.mpl_connect('button_press_event', onclick)
#
#     new_edges = edges.copy()
#     new_edges['left_press_idx'] = 0
#     new_edges['right_press_idx'] = 0
#
#     new_edges['low_level_ini'] = -1
#     new_edges['low_level_end'] = -1
#
#     new_edges['high_level_ini'] = -1
#     new_edges['high_level_end'] = -1
#
#     legend_elements = [Patch(facecolor='green', label='Low Pc level'),
#                        Patch(facecolor='red', label='High Pc level')]
#     ax.legend(handles=legend_elements)
#
#     # figManager = plt.get_current_fig_manager()
#     # figManager.window.showMaximized()
#
#     if show:
#         plt.show(block=False)
#         # fig.show(block=False)
#
#         while plt.fignum_exists(fig.number):
#             plt.pause(0.0001)
#
#             if new_btn_press:
#                 new_btn_press = False
#
#                 if btn_press_button == 1:
#                     if new_edges['left_press_idx'] % 2 == 0:
#                         new_edges['low_level_ini'] = int(btn_press_x_position)
#                     else:
#                         new_edges['low_level_end'] = int(btn_press_x_position)
#
#                     new_edges['left_press_idx'] += 1
#
#                 elif btn_press_button == 3:
#                     if new_edges['right_press_idx'] % 2 == 0:
#                         new_edges['high_level_ini'] = int(btn_press_x_position)
#                     else:
#                         new_edges['high_level_end'] = int(btn_press_x_position)
#
#                     new_edges['right_press_idx'] += 1
#
#             if new_edges['left_press_idx'] + new_edges['right_press_idx'] > 0:
#                 while len(new_edges['plots']):
#                     new_edges['plots'].pop(0).remove()
#
#                 bottom, top = ax.get_ylim()
#
#                 if new_edges['left_press_idx'] > 0:
#                     if new_edges['low_level_ini'] != -1 and new_edges['low_level_end'] != -1:
#                         ax.axvspan(new_edges['low_level_ini'], new_edges['low_level_end'], ymin=0.0, ymax=1.0, alpha=0.5, color='g')
#                         t = ax.text((new_edges['low_level_ini'] + new_edges['low_level_ini']) / 3 + new_edges['low_level_ini'], (top - bottom) / 2 + bottom, 'niveau\nbas', fontsize=5, ha='center')
#                         edges['plots'].append(t)
#
#                     elif new_edges['low_level_ini'] == -1 and new_edges['low_level_end'] != -1:
#                         ax.axvline(x=new_edges['low_level_end'], color='g')
#                         t = ax.text(new_edges['low_level_end'], bottom, 'fin niveau bas', rotation='vertical', fontsize=5)
#                         edges['plots'].append(t)
#
#                     elif new_edges['low_level_ini'] != -1 and new_edges['low_level_end'] == -1:
#                         ax.axvline(x=new_edges['low_level_ini'], color='g')
#                         t = ax.text(new_edges['low_level_ini'], bottom, 'début niveau bas', rotation='vertical', fontsize=5)
#                         edges['plots'].append(t)
#
#                 if new_edges['right_press_idx'] > 0:
#                     if new_edges['high_level_ini'] != -1 and new_edges['high_level_end'] != -1:
#                         ax.axvspan(new_edges['high_level_ini'], new_edges['high_level_end'], ymin=0.0, ymax=1.0, alpha=0.5, color='r')
#                         t = ax.text((new_edges['high_level_end'] + new_edges['high_level_ini']) / 3 + new_edges['high_level_ini'], (top - bottom) / 2 + bottom, 'niveau\nhaut', fontsize=5, ha='center')
#                         edges['plots'].append(t)
#
#                     elif new_edges['high_level_ini'] == -1 and new_edges['high_level_end'] != -1:
#                         ax.axvline(x=new_edges['high_level_end'], color='r')
#                         t = ax.text(new_edges['high_level_end'], bottom, 'fin niveau haut', rotation='vertical', fontsize=5)
#                         edges['plots'].append(t)
#
#                     elif new_edges['high_level_ini'] != -1 and new_edges['high_level_end'] == -1:
#                         ax.axvline(x=new_edges['high_level_ini'], color='r')
#                         t = ax.text(new_edges['high_level_ini'], bottom, 'début niveau haut', rotation='vertical', fontsize=5)
#                         edges['plots'].append(t)
#
#     # set high and low values after manual checking
#     if new_edges['left_press_idx'] + new_edges['right_press_idx']:
#         high_level_ini_idx = (np.abs(raw_data['time'].values - new_edges['high_level_ini'])).argmin()
#         high_level_end_idx = (np.abs(raw_data['time'].values - new_edges['high_level_end'])).argmin()
#         low_level_ini_idx = (np.abs(raw_data['time'].values - new_edges['low_level_ini'])).argmin()
#         low_level_end_idx = (np.abs(raw_data['time'].values - new_edges['low_level_end'])).argmin()
#
#         high_val = np.nanmean(raw_data['values'].values[high_level_ini_idx:high_level_end_idx])
#         low_val = np.nanmean(raw_data['values'].values[low_level_ini_idx:low_level_end_idx])
#     else:
#         high_val, low_val = np.nanmean(high_vals), np.nanmean(low_vals)
#
#     results = {'high_val': high_val, 'low_val': low_val, 'Pc': high_val - low_val}
#
#     return results


# class GraphFrameLoadingData(tk.Frame):
#     def __init__(self, parent, name, show=True):
#         tk.Frame.__init__(self, parent, name=name)
# 
#         self.figure = Figure(figsize=(5, 5), dpi=100)
#         self.subplot = self.figure.add_subplot(111)
#         # self.subplot.plot(data['x'], data['y'])
# 
#         self.show = show
# 
#         canvas = FigureCanvasTkAgg(self.figure, self)
#         canvas.draw()
#         canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
# 
#         toolbar = NavigationToolbar2Tk(canvas, self)
#         toolbar.update()
#         canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


def get_pc_from_machining_file(win, file_path_):
    def onclick(event):
        btn_press_x_position = event.xdata
        btn_press_button = event.button

        if btn_press_button == 1:
            new_edges['left_press_idx'] += 1
            if new_edges['left_press_idx'] % 2 == 0:
                new_edges['low_level_end'] = int(btn_press_x_position)
            else:
                new_edges['low_level_ini'] = int(btn_press_x_position)

        elif btn_press_button == 3:
            new_edges['right_press_idx'] += 1
            if new_edges['right_press_idx'] % 2 == 0:
                new_edges['high_level_end'] = int(btn_press_x_position)
            else:
                new_edges['high_level_ini'] = int(btn_press_x_position)

        while len(new_edges['plots']):
            new_edges['plots'].pop(0).remove()

        bottom, top = frame.subplot.get_ylim()

        if new_edges['left_press_idx'] > 0:
            if new_edges['low_level_ini'] != -1 and new_edges['low_level_end'] != -1:
                frame.subplot.axvspan(new_edges['low_level_ini'], new_edges['low_level_end'], ymin=0.0, ymax=1.0, alpha=0.5, color='g')
                t = frame.subplot.text((new_edges['low_level_ini'] + new_edges['low_level_ini']) / 3 + new_edges['low_level_ini'], (top - bottom) / 2 + bottom, 'niveau\nbas', fontsize=5, ha='center')
                edges['plots'].append(t)

            elif new_edges['low_level_ini'] == -1 and new_edges['low_level_end'] != -1:
                frame.subplot.axvline(x=new_edges['low_level_end'], color='g')
                t = frame.subplot.text(new_edges['low_level_end'], bottom, 'fin niveau bas', rotation='vertical', fontsize=5)
                edges['plots'].append(t)

            elif new_edges['low_level_ini'] != -1 and new_edges['low_level_end'] == -1:
                frame.subplot.axvline(x=new_edges['low_level_ini'], color='g')
                t = frame.subplot.text(new_edges['low_level_ini'], bottom, 'début niveau bas', rotation='vertical', fontsize=5)
                edges['plots'].append(t)

        if new_edges['right_press_idx'] > 0:
            if new_edges['high_level_ini'] != -1 and new_edges['high_level_end'] != -1:
                frame.subplot.axvspan(new_edges['high_level_ini'], new_edges['high_level_end'], ymin=0.0, ymax=1.0, alpha=0.5, color='r')
                t = frame.subplot.text((new_edges['high_level_end'] + new_edges['high_level_ini']) / 3 + new_edges['high_level_ini'], (top - bottom) / 2 + bottom, 'niveau\nhaut', fontsize=5, ha='center')
                edges['plots'].append(t)

            elif new_edges['high_level_ini'] == -1 and new_edges['high_level_end'] != -1:
                frame.subplot.axvline(x=new_edges['high_level_end'], color='r')
                t = frame.subplot.text(new_edges['high_level_end'], bottom, 'fin niveau haut', rotation='vertical', fontsize=5)
                edges['plots'].append(t)

            elif new_edges['high_level_ini'] != -1 and new_edges['high_level_end'] == -1:
                frame.subplot.axvline(x=new_edges['high_level_ini'], color='r')
                t = frame.subplot.text(new_edges['high_level_ini'], bottom, 'début niveau haut', rotation='vertical', fontsize=5)
                edges['plots'].append(t)

        frame.canvas.draw()
        frame.toolbar.update()

    t, raw_data, normalized_data, derivative_smoothed_data, edges = get_data_from_machining_file(file_path_)

    #####################################################
    frame = win.frames['frame_1']
    # plot data and get low and high values
    color = 'tab:red'
    frame.subplot.set_xlabel('time (ms)')
    frame.subplot.set_ylabel('Pc(W)', color=color)
    frame.subplot.plot(raw_data['time'], raw_data['values'], color=color)
    frame.subplot.tick_params(axis='y', labelcolor=color)

    ax2 = frame.subplot.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('derivative', color=color)  # we already handled the x-label with frame.subplot
    ax2.plot(raw_data['time'], derivative_smoothed_data.values, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    frame.figure.tight_layout()  # otherwise the right y-label is slightly clipped

    edges['plots'] = []
    low_vals, high_vals = [], []

    if len(edges['sign_change']) < 2:
        low_vals.extend(normalized_data.values)
        axinf = frame.subplot.axvspan(0, t - 1, ymin=0.0, ymax=1.0, alpha=0.5, color='green')
        edges['plots'].append(axinf)
    else:
        low_vals.extend(raw_data['values'].values[edges['sign_change_idxs'][0]:edges['sign_change_idxs'][1]])
        axinf = frame.subplot.axvspan(edges['sign_change'][0], edges['sign_change'][1], ymin=0.0, ymax=1.0, alpha=0.5, color='green')
        edges['plots'].append(axinf)

        high_vals.extend(raw_data['values'].values[edges['sign_change_idxs'][2]:edges['sign_change_idxs'][3]])
        axinf = frame.subplot.axvspan(edges['sign_change'][2], edges['sign_change'][3], ymin=0.0, ymax=1.0, alpha=0.5, color='red')
        edges['plots'].append(axinf)

    frame.figure.canvas.mpl_connect('button_press_event', onclick)

    new_edges = edges.copy()
    new_edges['left_press_idx'] = 0
    new_edges['right_press_idx'] = 0

    new_edges['low_level_ini'] = -1
    new_edges['low_level_end'] = -1

    new_edges['high_level_ini'] = -1
    new_edges['high_level_end'] = -1

    legend_elements = [Patch(facecolor='green', label='Low Pc level'),
                       Patch(facecolor='red', label='High Pc level')]
    frame.subplot.legend(handles=legend_elements)

    # figManager = plt.get_current_fig_manager()
    # figManager.window.showMaximized()

    frame.canvas.draw()
    frame.toolbar.update()

    win.mainloop()

    if win.frames['frame_1'].res:
        if new_edges['left_press_idx'] + new_edges['right_press_idx']:
            high_level_ini_idx = (np.abs(raw_data['time'].values - new_edges['high_level_ini'])).argmin()
            high_level_end_idx = (np.abs(raw_data['time'].values - new_edges['high_level_end'])).argmin()
            low_level_ini_idx = (np.abs(raw_data['time'].values - new_edges['low_level_ini'])).argmin()
            low_level_end_idx = (np.abs(raw_data['time'].values - new_edges['low_level_end'])).argmin()

            high_val = np.nanmean(raw_data['values'].values[high_level_ini_idx:high_level_end_idx])
            low_val = np.nanmean(raw_data['values'].values[low_level_ini_idx:low_level_end_idx])
        else:
            high_val, low_val = np.nanmean(high_vals), np.nanmean(low_vals)

        results = {'high_val': high_val, 'low_val': low_val, 'Pc': high_val - low_val}
    else:
        results = None

    return results


if __name__ == "__main__":
    file_path = get_file_name()

    vals = get_pc_from_machining_file_unique_entry(file_path)
    print(vals)
