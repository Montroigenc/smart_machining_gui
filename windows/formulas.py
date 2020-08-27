import numpy as np


def compute_dynamic_table(target, win):
    res = {'x': [], 'y': [], 'statut': []}
    table_params = win.result['dynamic_parameters']

    for key, value in table_params.items():
        if 'fichier de mesure' in key and value != 'Parcourir':
            row_idx = int(key.replace('fichier de mesure_', ''))
            # row_idx = item.grid_info()['row']

            # just for debugging while not having the real machining file
            # file_path = item['text']
            # pcs.append(get_pc_from_machining_file(file_path))

            if target == 'f min':
                # ae, fz = 10 - row_idx, 10 - row_idx
                ae = float(win.result['input_parameters']['engagement radial ae (mm)'])
                fz = float(table_params[f'avance par dent fz (mm/tr)_{row_idx}'])
                d = win.general_parameters['diameter']

                # h = compute_h(ae, fz, d)
                h = 10 - row_idx

                Wc = (row_idx - 1) ** 2
                # Wc = float(table_params[f"wc (w)_{row_idx}"])

                res['x'].append(h)
                res['y'].append(Wc)

            if target == 'AD max':
                if table_params[f"statut_{row_idx}"] == 'OK':
                    # Pc = 10 - row_idx
                    # ap, ae = 2, 1
                    Pc = float(table_params[f"pc (w)_{row_idx}"])
                    ap = float(table_params[f"engagement axial ap(mm)_{row_idx}"])
                    ae = float(table_params[f"engagement radial ae(mm)_{row_idx}"])
                    AD = ap * ae
                    # statut = 'OK'

                    res['x'].append(Pc)
                    res['y'].append(AD)
                    # res['statut'].append(statut)

            if target == 'Q max':
                if table_params[f"statut_{row_idx}"] == 'OK':
                    # AD, Vf, fz, Zu, d, n, Vc = 3, 2, 1, 2, 3, 5, 4

                    ap = float(win.result['input_parameters']['engagement axial ap (mm)'])
                    ae = float(win.result['input_parameters']['engagement radial ae (mm)'])
                    AD = ap * ae

                    Zu = float(win.general_parameters['n_teeth'])
                    d = float(win.general_parameters['diameter'])
                    Vc = float(table_params[f"vitesse de coupe vc (m/min)_{row_idx}"])

                    h = float(table_params[f"epaisseur de coupe h (mm)_{row_idx}"])
                    fz = get_fz_from_h(d, h, ae)


                    # Q = AD * Vf / 1000
                    # or:
                    # Q = AD * fz * Zu * n / 1000
                    # or:
                    Q = AD * fz * Zu * Vc / np.pi / d

                    # Pc = 10 - row_idx
                    Pc = table_params[f"pc (w)_{row_idx}"]

                    res['x'].append(Pc)
                    res['y'].append(Q)
                    # res['statut'].append(statut)

            elif target == 'Vc min':
                Vc = row_idx - 1
                Pc = np.exp(-row_idx)

                # Vc = float(table_params[f"vitesse de coupe vc (m/min)_{row_idx}"])
                # Pc = float(table_params[f"pc (w)_{row_idx}"])

                res['x'].append(Vc)
                res['y'].append(Pc)

    dydx = np.diff(res['y']) / np.diff(res['x'])
    res['min_target_value'] = np.argmin(dydx)
    # res['best_range_max'] = res['best_range_min'] - 1
    # print(dydx)

    return res


def get_fz_from_h(d, h, ae):
    if ae < d:
        return h / 2 / np.square((ae / d) * (1 - ae / d))
    else:
        return h


def compute_h(ae, fz, d):
    if ae < d:
        return 2 * fz * np.square((ae / d) * (1 - ae / d))
    else:
        return fz


def compute_Q(Vc, ae, ap, h, d, z):
    # d = self.general_parameters['diameter']
    # z = self.general_parameters['n_teeth']  # number of effective teeth
    fz = get_fz_from_h(d, h, ae)
    AD = ae * ap

    N = 1000 * Vc / np.pi / d
    Vf = N * fz * z

    # AD, Vf, fz, Zu, d, n, Vc = 3, 2, 1, 2, 3, 5, 4
    Q = AD * Vf / 1000
    # or:
    # Q = AD * fz * Zu * n / 1000
    # or:
    # Q = AD * fz * Zu * Vc / np.pi / d

    return Q