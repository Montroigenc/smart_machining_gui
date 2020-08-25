import pandas as pd
import os, sys
from tkinter import messagebox, filedialog
import tkinter as tk


def load_tools_data(operation):
    tools_dict = None

    if getattr(sys, 'frozen', False):
        file_path = os.path.dirname(sys.executable).replace('utils', '') + 'outils.csv'
    elif __file__:
        file_path = os.path.dirname(__file__).replace('utils', '') + 'outils.csv'

    if os.path.isfile(file_path):
        df = pd.read_csv(file_path, encoding="ISO-8859-1")

        tools_dict = {}
        for t in df.values:
            if t[1] == operation:
                tools_dict[t[0]] = t[1:]

    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", "Le fichier de configuration n'est pas présent dans {}".format(file_path))

    return tools_dict


def load_config(filePath):
    if os.path.isfile(filePath):
        f = open(filePath, "r", encoding='utf-8')
        data = f.read().replace("\ufeff", "")
        data = data.split("\n")

        config_params = dict()
        for l in data:
            l = l.split(" = ")
            config_params["{}".format(l[0])] = l[1]

        print("{} config file loaded".format(filePath))
        return config_params
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", "Le fichier de configuration n'est pas présent dans {}".format(filePath))


if __name__ == "__main__":
    load_tools_data("Fraisage")