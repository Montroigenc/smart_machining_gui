import tkinter as tk
import tkinter.ttk as TTK
from tkinter import messagebox, filedialog
import cv2
import PIL.Image, PIL.ImageTk
import pyautogui
import numpy as np
import os
import glob
import ntpath
import datetime
import time
import sys
import traceback
import shutil

from windows.windows import set_trioption_window, set_user_input_parameters_window
from utils.utils import load_tools_data


class UserGUI():
    def __init__(self):
        self.current_operation = ""

    def __call__(self):
        # get operation type
        # operation = set_trioption_window("operation", "Choix du type d'opération et de ses caractéristiques", "Tournage", "Perçage", "Fraisage")
        operation = "Fraisage"

        # set tools data from config file corresponding with previously selected operation
        self.tools_data = load_tools_data(operation)

        # ask user to chose a tool from the predefined list in the config file
        # general_parameters = set_user_input_parameters_window("operation_parameters", "Caractéristiques de l'usinage", self.tools_data)

        # vc_min = set_trioption_window("vc_min", "Détermination Vc min", "ap, f", "D, f", "D, ap, ae, fz, Z")
        vcmin_operation_parameters = set_user_input_parameters_window("vcmin_operation_parameters", "Paràmetres d'operation", self.tools_data, operation)
        # fh_min = set_trioption_window("vc_min", "Détermination fmin/hmin", "ap, Vc", "D, Vc", "D, ap, ae, Vc, Z")

        fmin_operation_parameters = set_user_input_parameters_window("fmin_operation_parameters", "Paràmetres d'operation", self.tools_data, operation)

        admax_operation_parameters = set_user_input_parameters_window("admax_operation_parameters", "Paràmetres d'operation", self.tools_data, operation)

        vc_range = set_user_input_parameters_window("vc_range", "Définition de l'intervalle de mesure en Vc", self.tools_data, "vc_range")


if __name__ == "__main__":
    # try:
    print("LOCOMO (LOgiciel COm MicrO5) app launched")
    gui = UserGUI()
    gui()
    # except:
    #     root = tk.Tk()
    #     root.withdraw()
    #     messagebox.showerror("Error", traceback.format_exc())
    #     raise Exception(traceback.format_exc())
