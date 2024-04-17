import os
import shutil
import subprocess
import ctypes
import uuid
import sqlite3
from datetime import datetime
from IFsCoreInput import ModelParameter, ModelCoefficient, ModelInputs

class IFsModel:
    def __init__(self, root_dir = "C:/Users/Public/IFsCore/", output_dir = "C:/Users/Public/BIGPOPA/Output/", pqconverter_dir = "C:/Users/Public/BIGPOPA/Parquetnetcoreapp2.2/",  
                 output_var =  ["TFR", "POP", "LIFEXP", "BIRTHS", "DEATHS"], yr_start = 1995, yr_end = 2025):
        self.root_dir = root_dir
        self.yr_base = yr_start
        self.yr_forecast = yr_end
        # core model
        self.dir_model = os.path.join(self.root_dir, 'netcoreapp2.2/')
        self.dir_model_dll = os.path.join(self.dir_model, 'ifs.dll')
        # folder structure
        self.dir_runfiles = os.path.join(self.root_dir, 'RUNFILES/')
        self.dir_scenario = os.path.join(self.root_dir, 'Scenario/')
        # output storage
        self.dir_output = output_dir
        if not os.path.exists(self.dir_output):
            os.makedirs(self.dir_output)
        # baserun
        self.dir_baserun = os.path.join(self.dir_runfiles,"IFsBase.run.db")
        # working run
        self.dir_workingrun = os.path.join(self.dir_runfiles,"Working.run.db")
        # parquet file converter 
        self.dir_parquetcv = pqconverter_dir
        self.dir_parquetcv_dll = os.path.join(self.dir_parquetcv, "ParquetReader.dll")
        # ... any other directories based on root_dir
        # dictionaries to store param & coef
        self.parameters = {}  
        self.coefficients = {} 
        self.param_dim = {}
        # list of output variables
        self.outputVars = output_var

    def get_param_coef(self, parameters, coefficients):
        self.parameters = parameters
        self.coefficients = coefficients

    def get_param_dim(self, param_setting):
        self.param_dim = param_setting  

    def generate_sce_id(self):
        """        
        Generate unique identifiers for each scenario run throug UUID; if timestamps are wanted, use  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S"); 
        For example '20220430_153000' for April 30, 2022, 3:30 PM, or with micro seconds datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        """
        #random_uuid = uuid.uuid4().hex[:6].upper() 
        #time_sce_id = f"{timestamp}_{random_uuid}"
        #return time_sce_id
        return uuid.uuid4().hex
                
    def create_sce(self):
        sce_id = self.generate_sce_id()
        # create Working.sce
        sce_file_path = os.path.join(self.dir_scenario, 'Working.sce')
        # removing existing/previous working.sce 
        if os.path.exists(sce_file_path):
            os.remove(sce_file_path)
        sce_par = []
        # add parameters
        for param in self.parameters:
            param_v = self.parameters[param]
            param_dim = self.param_dim[param]
            if round(param_v, 6)==0:
                val_par_formatted = "0" 
            else:
                val_par_formatted = format(param_v, '.6f')
                val_par_formatted = val_par_formatted.rstrip('0').rstrip('.')
            n_vals = self.yr_forecast - self.yr_base + 1
            if param_dim==1 :
                line_sce_par = "".join( [f"CUSTOM,{param},World,", ",".join([val_par_formatted] * n_vals), "\n"])
            elif param_dim==0 :
                line_sce_par = "".join( [f"CUSTOM,{param},", ",".join([val_par_formatted] * n_vals), "\n"])
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
        with open(f"{sce_file_path}", 'w') as file: 
            file.writelines(sce_par) 
        return sce_id, sce_file_path

    def update_beta_model(self):
        '''
        Use IFsBase.run to reset the Working.run; 
        And update beta values in the Working.run.db file.
        '''
        #shutil.copy(self.dir_baserun, self.dir_workingrun)
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

    def run_model(self, sce_batch = 5, sw_rebuild = 1, report_progress= 0):
        # Ensure the correct working directory
        os.chdir(self.dir_model)
        # Define the command and arguments
        cmd = ["dotnet", self.dir_model_dll, str(sce_batch), str(self.yr_forecast), "-1", 
               "false", "false", str(sw_rebuild), "False", "--log", "ifslog.txt"]
        if report_progress == 1:
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
            return process
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)      
            return result
        
    def save_run(self, scenario_id, scenario_path):   
        scenario_save_dir = os.path.join(self.dir_output, scenario_id)
        os.makedirs(scenario_save_dir, exist_ok=False)
        sce_save_dir = os.path.join(scenario_save_dir, f"{scenario_id}.sce")
        shutil.copy2(scenario_path, sce_save_dir)
        run_save_dir = os.path.join(scenario_save_dir, "Working.run.db") 
        shutil.copy2(self.dir_workingrun, run_save_dir) 
        return scenario_save_dir
    
    def read_var(self, outputFile, scenario_save_dir):
        '''
        Read an IFs output file (.run.db) and query user specified variables. Save the outputs of each 
        variable into .parquet files, under the corresponding output folder. Then remove the output file (.run.db) to save storage space.
        '''
        # read and write into .parquet files
        outputFile_dir = os.path.join(scenario_save_dir, outputFile)
        conn = sqlite3.connect(outputFile_dir)
        cursor = conn.cursor()
        for v in self.outputVars:
            cursor.execute("SELECT Data FROM ifs_var_blob WHERE VariableName=?;", (v,))
            v_blob = cursor.fetchall()
            v_blob = v_blob[0][0]
            if v_blob:
                with open(f'{scenario_save_dir}/{v}.parquet', 'wb') as f:
                    f.write(v_blob)
        conn.close()
        os.remove(f'{scenario_save_dir}/{outputFile}')
        return None

    def parquetConvert(self, scenario_save_dir):
        '''
        Invoke a .NET process that convert all the .parquet files 
        into .csv files under a user given folder
        '''  
        os.chdir(self.dir_parquetcv)
        # pass the abs path to the folder of parquet files
        cmd = ["dotnet", self.dir_parquetcv_dll, scenario_save_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result


    # def get_param_coef_set(self, parameters, coefficients):
    #     self.parameters = parameters
    #     self.coefficients = coefficients

    # def run_session(self, sce_batch = 5, num_session = -1, sw_rebuild = 1):
    #     '''num_session indicates the associated folder names'''
    #     os.chdir(self.dir_model)
    #     cmd = ["dotnet", self.dir_model_dll, str(sce_batch), str(self.yr_forecast),str(num_session), 
    #            "false", "false", str(sw_rebuild), "False"]
    #     # run session
    #     result = subprocess.run(cmd, capture_output=True, text=True) 
    #     return result