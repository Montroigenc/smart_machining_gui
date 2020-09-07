from pandas_ods_reader import read_ods
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from tqdm import tqdm, trange
import pandas as pd

new_btn_press = False
btn_press_x_position = -1
btn_press_axis_row = -1
btn_press_button = -1


def get_pc_from_machining_file(file_path):
    global new_btn_press, btn_press_x_position, btn_press_axis_row, btn_press_button

    def onclick(event):
        global new_btn_press, btn_press_x_position, btn_press_axis_row, btn_press_button
        new_btn_press = True
        btn_press_x_position = event.xdata
        btn_press_axis_row = event.inaxes.rowNum
        btn_press_button = event.button

    # load a sheet based on its name
    raw_data = read_ods(file_path, "WATTMETRE")

    sampled_raw_data = pd.DataFrame()
    for c in raw_data.columns:
        sampled_raw_data[c] = raw_data[c][::50]

    raw_data = sampled_raw_data

    t = raw_data.shape[0]

    # get edges
    normalized_data = raw_data - raw_data.min()
    normalized_data /= normalized_data.max()

    # smoothed_data = normalized_data.rolling(window=2000, win_type='gaussian', center=True).mean(std=0.5)
    smoothed_data = normalized_data.rolling(window=4000).mean()

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


if __name__ == "__main__":
    file_path = 'C:/Users/RI/Desktop/TEST_WAT_2_W_fmin_DataFile.ods'
    # file_path = 'C:/Users/RI/Desktop/OneDrive - Richemont International SA/smart_machining/data/TEST_WAT_2_W_fmin_DataFile.ods'

    vals = get_pc_from_machining_file(file_path)
    print(vals)
