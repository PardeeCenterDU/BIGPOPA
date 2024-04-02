import numpy as np
import pandas as pd
from itertools import product

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
        self.outputvars = []

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
                yield (param_values, coef_values)

    def load_outputvars_excel(self, excel_path, sheet_name):
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        for index, row in df.iterrows():
            if row['AnalysisSwitch'].lower() == 'on':  # Only load coefficients with TuningSwitch 'on'
                self.outputvars.append(row['Variable'])
        return self.outputvars