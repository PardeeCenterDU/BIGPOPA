import time
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
###
from IFsCoreModel import *

def run_sessions(num_session):
    ifs_model = IFsModel(root_dir="C:/Users/Public/IFsCore/", yr_start=1995, yr_end=2025)
    result = ifs_model.run_session(num_session=num_session)
    return result

if __name__ == '__main__':
    start = time.time()
    with ProcessPoolExecutor(max_workers=4) as e:
        e.submit(run_sessions, 0)
        e.submit(run_sessions, 1)
        e.submit(run_sessions, 2)
        e.submit(run_sessions, 3)
    end = time.time()
    print((end-start)/60)
