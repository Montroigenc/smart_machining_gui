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

from windows.windows import set_user_window


class UserGUI():
    def __init__(self):
        self.current_operation = ""
        self.app_name = "Logiciel COM Micro5"
        self.available_operations = "Tournage", "Perçage", "Fraisage"

    def __call__(self):
        # get operation type
        # operation = set_trioption_window(self.app_name, "Choix du type d'opération", "Tournage", "Perçage", "Fraisage")
        operation = "Fraisage"

        # set tools data from config file corresponding with previously selected operation
        # self.tools_data = load_tools_data(operation)

        # ask user to chose a tool from the predefined list in the config file
        # general_parameters = set_user_window(self.app_name, "Caractéristiques de l'usinage", available_operations=self.available_operations)

        # vc_min = set_trioption_window("vc_min", "Détermination Vc min", "ap, f", "D, f", "D, ap, ae, fz, Z")
        vcmin_operation_parameters = set_user_window(self.app_name, "Détermination de Vc min", operation=operation)
        # fh_min = set_trioption_window("vc_min", "Détermination fmin/hmin", "ap, Vc", "D, Vc", "D, ap, ae, Vc, Z")

        fmin_operation_parameters = set_user_input_parameters_window(self.app_name, "Détermination de f min", self.tools_data, operation)

        admax_operation_parameters = set_user_input_parameters_window(self.app_name, "Détermination de AD max", self.tools_data, operation)

        # vc_range = set_user_input_parameters_window("vc_range", "Définition de l'intervalle de mesure en Vc", self.tools_data, "vc_range")


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
