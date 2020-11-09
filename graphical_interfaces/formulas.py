import numpy as np


def compute_dynamic_table(target, win):
    res = {'x': [], 'y': [], 'statut': []}
    table_params = win.result['dynamic_parameters']

    if win.debug:
        if target == 'Vc min':
            res = np.asarray([[i for i in range(10)], [50 * np.exp(-i) for i in range(10)]])
        elif target == 'f min':
            res = np.asarray([[10 - i for i in range(10)], [(i - 1) ** 2 for i in range(10)]])

    else:
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
                    d = float(win.data['general_parameters']['diameter'])

                    # if win.debug:
                    #     h = 10 - row_idx
                    #     Wc = (row_idx - 1) ** 2
                    # else:
                    h = compute_h(ae, fz, d)
                    Wc = float(table_params[f"wc (w)_{row_idx}"])

                    res['x'].append(h)
                    res['y'].append(Wc)

                if target == 'AD max':
                    if table_params[f"statut_{row_idx}"] == 'OK':
                        # Pc = 10 - row_idx
                        # ap, ae = 2, 1
                        Pc = float(table_params[f"pc (w)_{row_idx}"])
                        ap = float(table_params[f"engagement axial ap (mm)_{row_idx}"])
                        ae = float(table_params[f"engagement radial ae (mm)_{row_idx}"])
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
                        # AD = ap * ae

                        z = float(win.data['general_parameters']['n_teeth'])
                        d = float(win.data['general_parameters']['diameter'])
                        Vc = float(table_params[f"vitesse de coupe vc (m/min)_{row_idx}"])

                        h = float(table_params[f"epaisseur de coupe h (mm)_{row_idx}"])
                        # fz = get_fz_from_h(d, h, ae)

                        Q = compute_Q(Vc, ae, ap, h, d, z)

                        # Pc = 10 - row_idx
                        Pc = table_params[f"pc (w)_{row_idx}"]

                        res['x'].append(Pc)
                        res['y'].append(Q)
                        # res['statut'].append(statut)

                elif target == 'Vc min':
                    # if win.debug:
                    #     Vc = row_idx
                    #     Pc = 50 * np.exp(-row_idx)  # + row_idx
                    # else:
                    Vc = float(table_params[f"vitesse de coupe vc (m/min)_{row_idx}"])
                    Pc = float(table_params[f"pc (w)_{row_idx}"])

                    res['x'].append(Vc)
                    res['y'].append(Pc)

        # dydx = np.diff(res['y']) / np.diff(res['x'])
        # res['min_target_value'] = np.argmin(dydx)
        # res['best_range_max'] = res['best_range_min'] - 1
        # print(dydx)

        res = np.asarray([res['x'], res['y']])
        order_idxs = np.argsort(res[0])
        res[0] = res[0][order_idxs]
        res[1] = res[1][order_idxs]

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


# def compute_Q(Vc, ae, ap, h, d, z):
def compute_Q(*args):
    if len(args) == 2:
        AD, Vf = args
        return AD * Vf / 1000
    else:
        Vc, ae, ap, h, d, z = args
        # d = self.general_parameters['diameter']
        # z = self.general_parameters['n_teeth']  # number of effective teeth
        fz = get_fz_from_h(d, h, ae)
        AD = ae * ap

        N = compute_N(Vc, d)
        Vf = compute_Vf(N, fz, z)

        # AD, Vf, fz, Zu, d, n, Vc = 3, 2, 1, 2, 3, 5, 4
        Q = AD * Vf / 1000
        # or:
        # Q = AD * fz * Zu * n / 1000
        # or:
        # Q = AD * fz * Zu * Vc / np.pi / d

        return Q


def compute_N(Vc, d):
    return 1000 * Vc / np.pi / d


def compute_Vf(N, fz, z):
    return N * fz * z


def compute_Wc(d, Pc, ap, ae, z, fz, Vc):
    return np.pi * d * Pc / ap / ae / z / fz / Vc