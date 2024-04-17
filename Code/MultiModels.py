#from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from itertools import product
from IFsCoreModel import *
from multiprocessing import Process, Queue, current_process, Manager
import multiprocessing
import time

def enqueuer(queue, combinations_generator, n_workers):
    for combo in combinations_generator:
        while queue.qsize() > 40:  # limit, adjust based on memory constraints
            time.sleep(60)  # Wait 60s before checking the queue size again
        queue.put(combo)
    # After all combinations are enqueued, add a stop signal for each worker
    for _ in range(n_workers):
        queue.put(None)

def model_runner(queue, model_path, output_varlist, param_dim_dict):
    model = IFsModel(root_dir = model_path, output_var =  output_varlist)
    model.get_param_dim(param_dim_dict)
    while True:
        param_coef_comb = queue.get()
        if param_coef_comb is None:
            break
        params, coeffs = param_coef_comb 
        model.get_param_coef(params, coeffs)
        scenario_id, scenario_path = model.create_sce() 
        model.update_beta_model()
        model.run_model()
        scenarioSavePath = model.save_run(scenario_id, scenario_path)
        model.read_var("Working.run.db", scenarioSavePath)
        model.parquetConvert(scenarioSavePath)

if __name__ == "__main__":
    start = time.time()
    ifs_input = ModelInputs()
    dir_init_excel = 'C:/Users/Public/BIGPOPA/ScenarioGuide.xlsx'
    ifs_input.load_parameters_excel(dir_init_excel, sheet_name='Para_Demo_Global')
    ifs_input.load_coefficients_excel(dir_init_excel, sheet_name='Coef_Demo_Global')
    varList = ifs_input.load_outputvars_excel(dir_init_excel, sheet_name = "Var_Output")
    param_dim_dict = ifs_input.get_param_dim()
    #
    queue = Queue()
    combinations_generator = ifs_input.param_coef_combo_generator()
    # Start runner, each with its own model instance
    model_paths = [f"C:/Users/Public/IFsCore0{i}/" for i in range(5)]
    processes = []
    for path in model_paths:
        p = Process(target=model_runner, args=(queue, path, varList, param_dim_dict))
        p.start()
        processes.append(p)
    # Feed all combinations into the queue
    for combo in combinations_generator:
        queue.put(combo)
    # Add sentinel values to the queue to signal to each worker to exit
    for _ in range(len(processes)):
        queue.put(None)
    # Wait for all workers' processes to finish
    for p in processes:
        p.join()
    end = time.time()
    print((end-start)/60)

