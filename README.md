# IFsAutoTune
With user-selected parameters and coefficients along with their corresponding input ranges, this app auto-tunes the model performance of the International Futures (IFs) tool for its short-term (20-year) projection. 

# Notes
- Current testing runs on IFs8.10 with a base year of 1995.



# IFsCore folder structure

The IFsCore follows the same directory structure as the development version of IFs, but with a minimal set of files that ensures the model run. With the development version of IFs, please run the model with a base year of 1995 to do the historical validation & tuning.

* [IFsCore](./IFsCore)
  * [DATA](./IFsCore/DATA) make sure you have SAMBase.db file under the DATA folder
  * [netcoreapp2.2](./IFsCore/netcoreapp2.2) this is where the core model code lives
  * [RUNFILES](./IFsCore/RUNFILES) for safty, put all your files under the RUNFILES folder after model rebuilt (e.g., 1995)
  * [Scenario](./IFsCore/Scenario) empty by default, Working.sce will be added to run parameter & coefficient tuning during each model run
  * [Parquetnetcoreapp2.2](./IFsCore/Parquetnetcoreapp2.2) a .NET programe (.dll) that reads the .parquet file and convert it into CSV format
  * [Output](./IFsCore/Output) this is a default, yet optional, output folder that stores each model run's results and settings under the same place

* [README.md](./README.md)

# Getting Started

# Contributing
We welcome contributions and feedback. Here's how you can help:
- [Report issues](<[https://github.com/PardeeCenterDU/IFsAutoTune/issues]>)  
- [Contact us](<yutang.xiong@du.edu>)
