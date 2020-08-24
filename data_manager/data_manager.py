from pandas_ods_reader import read_ods
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from tqdm import tqdm, trange


def get_pc_from_machining_file(file_path):

    # load a sheet based on its index (1 based)
    df_header_sheet = read_ods(file_path, 1)

    # load a sheet based on its name
    raw_data = read_ods(file_path, "WATTMETRE")

    t = raw_data.shape[0]

    # get edges
    raw_min_vals = raw_data.min()
    raw_max_vals = raw_data.max()

    normalized_data = raw_data - raw_min_vals
    normalized_data /= normalized_data.max()

    # smoothed_data = normalized_data.rolling(window=2000, win_type='gaussian', center=True).mean(std=0.5)
    smoothed_data = normalized_data.rolling(window=4000).mean()

    derivative_data = smoothed_data.diff()

    noise_threshold = 0.0001  # 0.00015
    window_width = 3
    momentum_threshold = 100
    edges = {}
    for measure_idx, header in tqdm(enumerate(raw_data.columns.values), desc='measures loop'):
        measure_edges = {}
        measure_edges['positive_ini'], measure_edges['positive_end'], measure_edges['negative_ini'], measure_edges['negative_end'], measure_edges['positive_max'], measure_edges['negative_min'] = [], [], [], [], [], []
        positive_detected, negative_detected = False, False
        max_val, min_val = -9e3, 9e3
        hill_ini, descent_ini = 0, 0
        momentum_count = 0

        for t_idx in trange(window_width, t-window_width, desc='time loop'):
            if np.any(np.isnan(derivative_data[header].values[t_idx-window_width:t_idx+window_width+1])):
                continue

            previous_val, posterior_val = derivative_data[header][t_idx-window_width:t_idx].median(), derivative_data[header][t_idx:t_idx+window_width+1].median()
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
    fig, axes = plt.subplots(nrows=raw_data.shape[1], ncols=1, sharex=True)

    for ax, header in zip(axes.flatten(), raw_data.columns.values):
        low_vals, high_vals = [], []
        ax.plot(range(t), raw_data[header].values, color='b')
        ax2 = ax.twinx()
        ax2.plot(range(t), derivative_data[header].values, color='g', linestyle='dashed')

        if len(edges[header]['positive_max']) == 0:
            ax.axvspan(0, t - 1, ymin=0.0, ymax=1.0, alpha=0.5, color='green')
            low_vals.extend(raw_data[header].values)
        else:
            for e_idx, edge in enumerate(edges[header]['positive_max']):
                ax.axvspan(0, edges[header]['positive_ini'][e_idx], ymin=0.0, ymax=1.0, alpha=0.5, color='green')
                low_vals.extend(raw_data[header].values[:edges[header]['positive_ini'][e_idx]])

                if len(edges[header]['negative_ini']) >= e_idx + 1:
                    ax.axvspan(edge, edges[header]['negative_ini'][e_idx], ymin=0.0, ymax=1.0, alpha=0.5, color='red')
                    high_vals.extend(raw_data[header].values[edge:edges[header]['negative_ini'][e_idx]])
                else:
                    ax.axvspan(edge, t - 1, ymin=0.0, ymax=1.0, alpha=0.5, color='red')
                    high_vals.extend(raw_data[header].values[edge:])

                if len(edges[header]['negative_min']) >= e_idx and len(edges[header]['negative_min']) > 0:
                    if len(edges[header]['positive_ini']) > e_idx + 1:
                        ax.axvspan(edges[header]['negative_min'][e_idx], edges[header]['positive_ini'][e_idx + 1], ymin=0.0, ymax=1.0, alpha=0.5, color='green')
                        low_vals.extend(raw_data[header].values[edges[header]['negative_min'][e_idx]:edges[header]['positive_ini'][e_idx + 1]])
                    else:
                        ax.axvspan(edges[header]['negative_min'][e_idx], t - 1, ymin=0.0, ymax=1.0, alpha=0.5, color='green')
                        low_vals.extend(raw_data[header].values[edges[header]['negative_min'][e_idx]:])

        ax.set_ylabel(header)

        high_val, low_val = np.nanmean(high_vals), np.nanmean(low_vals)
        print(f'{header} GAP:{high_val - low_val}, high_val: {high_val}, low_val: {low_val}')

    plt.show()

    # # Use seaborn style defaults and set the default figure size
    # sns.set(rc={'figure.figsize': (11, raw_data.shape[1])})
    #
    # # axes = raw_data[raw_data.columns.values].plot(figsize=(11, raw_data.shape[1]), subplots=True, sharex=True)
    # axes = raw_data.plot(sharex=True, subplots=True)
    # plt.xlabel('Time')
    #
    # # axes_smoothed = smoothed_data.plot(subplots=True, sharex=True)
    # axes_deriv = derivative_data.plot(subplots=True, sharex=True)
    #
    # plt.xlabel('Time')
    #
    # plt.show()


if __name__ == "__main__":
    # file_path = 'C:/Users/RI/Desktop/IA Micro5/data/TEST_WAT_2_W_Vcmin_DataFile.ods'
    file_path = 'C:/Users/RI/Desktop/IA Micro5/data/TEST_WAT_2_W_fmin_DataFile.ods'

    pc = get_pc_from_machining_file(file_path)