With user-selected parameters and coefficients along with their corresponding input ranges, this app auto-tunes the model performance of the International Futures (IFs) tool for its short-term (20-year) projection. 

# Getting Started

## Model Set up
Follow and create a same folder structure locally (IFsCore). With IFs development version, rebuild the base to a historical year (e.g., 1995), then copy and past required files to IFsCore.
#### IFsCore folder structure
The IFsCore follows the same directory structure as the development version of IFs, but with a minimal set of files that ensures the model run. With the development version of IFs, please run the model with a base year of 1995 to do the historical validation & tuning.
* [IFsCore](./IFsCore)
  * [IFsInit](./IFsCore/IFsInit.db) this is the IFsInit.db file after the model rebuilt (e.g., 1995), make sure you have the settings right
  * [DATA](./IFsCore/DATA) make sure you have SAMBase.db file under the DATA folder
  * [netcoreapp2.2](./IFsCore/netcoreapp2.2) this is where the core model code lives
  * [RUNFILES](./IFsCore/RUNFILES) for safty, put all your files under the RUNFILES folder after model rebuilt (e.g., 1995)
  * [Scenario](./IFsCore/Scenario) empty by default, Working.sce will be added to run parameter & coefficient tuning during each model run
* [Parquetnetcoreapp2.2](./IFsCore/Parquetnetcoreapp2.2) a .NET programe (.dll) that reads the .parquet file and convert it into CSV format. This can be put anywhere.
* [Output](./IFsCore/Output) this is a default output folder that stores each model run's results and settings under the same place. This can be put anywhere.

Now your model is set up and ready to be tuned.
## Input Set up
Using the ScenarioGuide file, you can toggle the parameters/coefficients to be tested in IFs historical validation. Other options are also available, such as limits & steps.

#### Multithreading
It is possible to run multiple IFs model runs in parallel. 
##### Method 1. Through session numbers in IFs CMD
1. Under RUNFILES folder, create "SessionXX" (XX represents session ID, e.g., Session00 is session 0) folder, and put following 17 files under the folder: AnalFunc.db; DataDict.db; IFs.db; IFsBase.run.db; IFsBaseHist.run.db; IFsHistSeries.db; IFsPop.db; IFsPopHist.db; IFsPopWork.db; IFsSmoking.db; IFsVar.db; IFsWVSCohort.db; Provinces.db; SAMBase.db; SAMWorking.db; TablFunc.db; Working.run.db
2. Under Scenario folder, create corresponding folders for each session (e.g., Session00 for session 0). Working.sce for each scenario should be put under this folder.
3. When running the model, input session number in the model call, and remove the --log parameter. Thus, in the default model call, </br>
   'dotnet.exe "C:/Users/Public/IFsCore/netcoreapp2.2/ifs.dll" 5 2030 **-1** false false 1 False **--log ifslog.txt**'</br>
   **--log** should be removed so multiple sessions won't interact with the same ifslog.txt file, and **-1** should be switched with the actual session number. Hence, for session 0, the right call would be</br>
   'dotnet.exe "C:/Users/Public/IFsCore/netcoreapp2.2/ifs.dll" 5 2030 **0** false false 1 False'
   
Through this method, you are able to retain the original files under the RUNFILES folder. Each model run will only occur under its associated session number. However, you will need to make changes to python classes and functions so that output of each model are properly handled. 
##### Method 2. Setting up multiple IFsCore in the device (current implementation)
This is a simpler approach as you are merely copying and pasting the same IFsCore structure. In the model initilization stage in Python, you will have to input different paths. The downside of this approach is you are wasting extra storage space (around 42.5mb for files under DATA/ folder).

# Contributing
We welcome contributions and feedback. Here's how you can help:
- [Report issues](<https://github.com/PardeeCenterDU/IFsAutoTune/issues>)  
- [Contact us](mailto:yutang.xiong@du.edu)
