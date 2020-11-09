import os
import sys
import json
from datetime import datetime
import logging

from graphical_interfaces.windows_manager import set_user_window
from utils.utils import load_config
# import traceback
# import tkinter as tk


class UserGUI:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            config_path = os.path.join(application_path, "../config.ini")
        elif __file__:
            application_path = os.path.dirname(__file__)
            config_path = os.path.join(application_path, "config.ini")

        config_params = load_config(config_path)

        self.app_name = config_params['nom_application']
        self.available_operations = config_params['opérations_disponibles'].split(',')
        self.output_dir = config_params['output_dir']
        self.debug_level = int(config_params['debug_level'])

        if self.debug_level > 0:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        self.data_file_name = f"{self.output_dir}/{str(datetime.now()).replace(' ', '_').replace(':', '-').replace('.', 'c')}_data.txt"

    def write_json(self, data):
        with open(self.data_file_name, 'w') as f:
            json.dump(data, f, indent=2)

    def __call__(self):
        data = {"general_parameters": dict(), "operation_parameters": dict(), "debug": int(self.debug_level)}

        step = 0
        while step < 5:
            logging.debug(f'Step {step}')
            if step == 0:
                # ask user to chose a tool from the predefined list in the config file
                data["general_parameters"], action = set_user_window(self.app_name, "Caractéristiques de l'usinage", available_operations=self.available_operations, data=data)

                if 'file_name' in data["general_parameters"]:
                    self.data_file_name = data["general_parameters"]["file_name"]

                    with open(data["general_parameters"]["file_name"]) as json_file:
                        data = json.load(json_file)

                step = step + 1 if action == 'next' else step

            elif step == 1:
                #  Determination of Vc,min
                data["operation_parameters"]['vcmin'], action = set_user_window(self.app_name, "Vc min", data=data)
                step = step + 1 if action == 'next' else step - 1

            elif step == 2:
                # Determination of the range hmin – hmax
                data["operation_parameters"]['fmin'], action = set_user_window(self.app_name, "f min", data=data)
                step = step + 1 if action == 'next' else step - 1

            elif step == 3:
                ''' Determination of limiting data '''
                #  high limit on cutting section (AD,max)
                data["operation_parameters"]['admax'], action = set_user_window(self.app_name, "AD max", data=data)
                step = step + 1 if action == 'next' else step - 1

            elif step == 4:
                # high limit on chip removal rate (Qmax)
                data["operation_parameters"]['qmax'], action = set_user_window(self.app_name, "Q max", data=data)
                step = step + 1 if action == 'next' else step - 1

            self.write_json(data)


if __name__ == "__main__":
    # try:
    logging.info("LOCOMO (LOgiciel COm MicrO5) app launched")
    gui = UserGUI()
    gui()
    # except:
    #     root = tk.Tk()
    #     root.withdraw()
    #     tk.messagebox.showerror("Error", traceback.format_exc())
    #     raise Exception(traceback.format_exc())
