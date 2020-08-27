import os
import sys
import json
from datetime import datetime

from windows.windows_manager import set_user_window
from utils.utils import load_config


class UserGUI():
    def __init__(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)

        config_path = os.path.join(application_path, "config.ini")
        config_params = load_config(config_path)

        self.app_name = config_params['nom_application']
        self.available_operations = config_params['opérations_disponibles'].split(',')
        self.output_dir = config_params['output_dir']

    def __call__(self):
        general_parameters = {'operation': 'Fraisage', 'tool': 'Outil1', 'diameter': 1, 'n_teeth': 9, 'user_name': 'werth', 'date': '25/août/2020', 'lubrication': 'etz', 'comments': 'etzj'}

        operation_parameters = dict()

        step = 5
        while step < 5:
            if step == 0:
                # get operation type
                # operation = set_trioption_window(self.app_name, "Choix du type d'opération", "Tournage", "Perçage", "Fraisage")
                # operation = "Fraisage"

                # set tools data from config file corresponding with previously selected operation
                # self.tools_data = load_tools_data(operation)

                # ask user to chose a tool from the predefined list in the config file
                general_parameters, action = set_user_window(self.app_name, "Caractéristiques de l'usinage", available_operations=self.available_operations)
                # general_parameters = {'operation': 'Fraisage', 'tool': 'Outil1', 'diameter': 1, 'n_teeth': 9, 'user_name': 'werth', 'date': '25/août/2020', 'lubrication': 'etz', 'comments': 'etzj'}
                # action = "next"
                step = step + 1 if action == 'next' else step

            if step == 1:
                #  Determination of Vc,min
                operation_parameters['vcmin'], action = set_user_window(self.app_name, "Vc min", general_parameters=general_parameters)
                step = step + 1 if action == 'next' else step - 1

            if step == 2:
                # Determination of the range hmin – hmax
                operation_parameters['fmin'], action = set_user_window(self.app_name, "f min", general_parameters=general_parameters)
                step = step + 1 if action == 'next' else step - 1

            if step == 3:
                ''' Determination of limiting data '''
                #  high limit on cutting section (AD,max)
                operation_parameters['admax'], action = set_user_window(self.app_name, "AD max", general_parameters=general_parameters)
                step = step + 1 if action == 'next' else step - 1

            if step == 4:
                # high limit on chip removal rate (Qmax)
                operation_parameters['qmax'], action = set_user_window(self.app_name, "Q max", general_parameters=general_parameters)
                step = step + 1 if action == 'next' else step - 1

        with open(f"{self.output_dir}/{str(datetime.now()).replace(' ', '_').replace(':', '-').replace('.', 'c')}_data.txt", 'w') as f:
            # with open(f'output/data.txt', 'w') as f:
            json.dump(general_parameters, f, indent=2)
            json.dump(operation_parameters, f, indent=2)


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
