import os
import subprocess
import ctypes
import uuid
import sqlite3
import pandas as pd
import numpy as np
from itertools import product
from datetime import datetime

class ModelParameter:
    '''A class to store individual parameter'''
    def __init__(self, param_name, default_val, min_val, max_val, steps = 20):
        self.param_name = param_name
        self.default_val = default_val
        self.min_val = min_val
        self.max_val = max_val
        self.steps_test = steps
        self.test_values = self._generate_test_values(self.steps_test)
                
    def _generate_test_values(self, steps_test):
        return np.linspace(self.min_val, self.max_val, num=steps_test)

class ModelCoefficient:
    '''A class to store individual coefficient'''
    def __init__(self, func_name, coef_name, seq_func, y_var, x_var, default_val, min_val, max_val, steps = 20):
        self.coef_id = f"{func_name}_{seq_func}_{coef_name}"
        self.func_name = func_name
        self.coef_name = coef_name
        self.seq_func = seq_func
        self.y_var = y_var
        self.x_var = x_var
        self.default_val = default_val
        self.min_val = min_val
        self.max_val = max_val
        self.steps_test = steps
        self.test_values = self._generate_test_values(self.steps_test)

    def _generate_test_values(self, steps_test):
        return np.linspace(self.min_val, self.max_val, num=steps_test)

class ModelInputs:
    '''Load parameters & coefficients for the model run and generate combinations as an iterator'''
    def __init__(self):
        self.parameters = {}  
        self.coefficients = {} 

    def add_parameter(self, param_name, default_val, min_val, max_val, steps=20):
        self.parameters[param_name] = ModelParameter(param_name, default_val, min_val, max_val, steps)

    def add_coefficient(self, func_name, coef_name, seq_func, y_var, x_var, default_val, min_val, max_val, steps=20):
        # Assuming a unique identifier for each coefficient is needed, you could use `coef_name` or a combination of attributes
        self.coefficients[f"{func_name}_{seq_func}_{coef_name}"] = ModelCoefficient(func_name, coef_name, seq_func, y_var, x_var, default_val, min_val, max_val, steps)

    def load_parameters_excel(self, excel_path, sheet_name):
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        for index, row in df.iterrows():
            if row['TuningSwitch'].lower() == 'on':  # Only load parameters with TuningSwitch 'on'
                self.add_parameter(param_name=row['Drivers'], default_val=row['Default'], 
                                   min_val=row['Min'], max_val=row['Max'],steps=row['Steps'])

    def load_coefficients_excel(self, excel_path, sheet_name):
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        for index, row in df.iterrows():
            if row['TuningSwitch'].lower() == 'on':  # Only load coefficients with TuningSwitch 'on'
                self.add_coefficient(func_name=row['Function'],coef_name=row['Coefficient'],seq_func=row['Seq'],
                    y_var=row['YVariable'],x_var=row['XVariable'],default_val=row['Default'],min_val=row['Min'],
                    max_val=row['Max'],steps=row['Steps'])
                
    def param_coef_combo_generator(self):
        param_test_values = {p.param_name: p.test_values for p in self.parameters.values()}
        coef_test_values = {c.coef_id: c.test_values for c in self.coefficients.values()}
        for param_combination in product(*param_test_values.values()):
            for coef_combination in product(*coef_test_values.values()):
                # Yield a dictionary with parameter names as keys and chosen test values as values
                param_values = dict(zip(param_test_values.keys(), param_combination))
                coef_values = dict(zip(coef_test_values.keys(), coef_combination))
                yield param_values, coef_values

class IFsModel:
    def __init__(self, root_dir = "C:/Users/Public/IFsCore/", yr_start = 1995, yr_end = 2025):
        self.root_dir = root_dir
        self.yr_base = yr_start
        self.yr_forecast = yr_end
        # core model
        self.dir_model = os.path.join(self.root_dir, 'netcoreapp2.2/')
        self.dir_model_dll = os.path.join(self.dir_model, 'ifs.dll')
        # folder structure
        self.dir_runfiles = os.path.join(self.root_dir, 'RUNFILES/')
        self.dir_scenario = os.path.join(self.root_dir, 'Scenario/')
        self.dir_output = os.path.join(self.root_dir, 'Output/')
        if not os.path.exists(self.dir_output):
            os.makedirs(self.dir_output)
        # baserun
        self.dir_baserun = os.path.join(self.dir_runfiles,"IFsBase.run.db")
        # parquet file converter 
        self.dir_parquetcv = os.path.join(self.root_dir, "Parquetnetcoreapp2.2/")
        self.dir_parquetcv_dll = os.path.join(self.dir_parquetcv, "ParquetReader.dll")
        # ... any other directories based on root_dir
        # dictionaries to store param & coef
        self.parameters = {}  
        self.coefficients = {} 

    def get_param_coef(self, parameters, coefficients):
        self.parameters = parameters
        self.coefficients = coefficients

    def generate_sce_id(self):
        # Generate a timestamp in a specific format, for example '20220430_153000' for April 30, 2022, 3:30 PM
        # or with micro seconds datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # add UUID 
        random_uuid = uuid.uuid4().hex[:6].upper()
        sce_id = f"{timestamp}_{random_uuid}"
        return sce_id
                
    def create_sce(self):
        sce_id = self.generate_sce_id()
        assert not os.listdir(self.dir_scenario) 
        # create Working.sce
        sce_file_path = os.path.join(self.dir_scenario, 'Working.sce')
        sce_par = []
        # add parameters
        for param in self.parameters:
            if round(self.parameters[param], 6)==0:
                val_par_formatted = "0" 
            else:
                val_par_formatted = format(self.parameters[param], '.6f')
                val_par_formatted = val_par_formatted.rstrip('0').rstrip('.')
            n_vals = self.yr_forecast - self.yr_base + 1
            line_sce_par = "".join( [f"CUSTOM,{param},World,", ",".join([val_par_formatted] * n_vals), "\n"])
            sce_par.append(line_sce_par)
        # add coef in the comments
        sce_par.append("COMMENT,START\n") 
        for coef in self.coefficients:
            if round(self.coefficients[coef], 6)==0:
                val_coef_formatted = "0" 
            else:
                val_coef_formatted = format(self.coefficients[coef], '.6f')
                val_coef_formatted = val_coef_formatted.rstrip('0').rstrip('.')
            line_sce_coef = f"Coefficient,{coef},{val_coef_formatted}\n" 
            sce_par.append(line_sce_coef)  
        # add sce_id
        sce_par.append(f'Scenario_ID:{sce_id}')     
        with open(f"{sce_file_path}", 'a') as file: 
            file.writelines(sce_par) 

    def update_beta(self):
        '''Update beta values in the IFsBase.run.db file'''
        conn = sqlite3.connect(self.dir_baserun)
        for coef_id in self.coefficients:
            val_coef = round(self.coefficients[coef_id], 5)
            # coef_id = f'{func_name}_{seq_func}_{coef_name}'
            coef_id_sp = coef_id.split("_")
            func_name = coef_id_sp[0]
            seq_func = coef_id_sp[1]
            coef_name = coef_id_sp[2]
            cursor = conn.cursor()
            q_update = f"""UPDATE [ifs_reg_coeff] SET Value = {val_coef} WHERE 
                    RegressionName = '{func_name}' AND RegressionSeq = {seq_func} AND Name = '{coef_name}';"""
            cursor.execute(q_update)
            conn.commit()
        conn.close()  

    def run_model(self, sce_batch = 5, num_session = -1, sw_rebuild = 1):
        # Ensure the correct working directory
        os.chdir(self.dir_model)
        # Define the command and arguments
        cmd = ["dotnet", self.dir_model_dll, str(sce_batch), str(self.yr_forecast), str(num_session), 
               "false", "false", str(sw_rebuild), "False", "--log", "ifslog.txt"]
        # Model run
        # result = subprocess.run(cmd, capture_output=True, text=True)
        # Model run with stdout on the fly
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              text=True, bufsize=1, universal_newlines=True) as process:
            print("Model Run Start")
            # Read the process output line by line
            for line in process.stdout:
                if line.startswith('Year'):
                    # Print & refesh the year
                    print(f'{line.strip()}', end='\r', flush=True)
            # If there was any stderr, print it out after the process is done
            stderr = process.stderr.read()
            if stderr:
                print("\nError:", stderr.strip())
            else:
                print("\nModel Run Complete")
        return process.returncode