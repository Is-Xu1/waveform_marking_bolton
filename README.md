# Python Interactive UI for Manual Waveform Marking <br>
## University of Texas at Austin
Created by Isaac Xu and Dr. Chas Bolton
# Download instructions
Download python file and run requirements.txt 
# Overview
Created for marking p-wave arrivals for waveforms using manual user input, saves user clicked x axis positions as a separate csv file for further analysis. Also included are several scripts for validating the rollout of the waveforms with the hand picks for the entire stream as well as some scripts for automatic manual marking such as noise deviation algorithms and STA/LTA and reading the residuals off of those datasets
# Manual User Input Scripts
manual_pwave_entry_fileonly.py and manual_pwave_entry.py
<br>
Accepted waveform file formats are .mseed
<br> 
The script treats each trace in the stream as separate for marking, it takes in a folder or file of .mseed files and uses the structure of the folder for naming. The folder should be structured as 
data/experiment_name/run_num/.mseed_files_here for the automatic labeling to be accurate. The output csv will be named p_picks_experiment name_run number_event id.csv where foldername is the name of the folder
selected and in the csv there are two columns, one is the marked x position in the original x axis and the other is the label for the exact experiment, run number, and trace number to 
idenitify which pick corresponds to which trace. 
<br>
there are two files, one for reading a folder full of data, and another for individual files
# Waveform Validation
waveform_rollout_display.py
<br>
within the waveform validation folder, it reads into the picks_folder and the waveforms folder and plots each trace displaced above each other and the picks to validate the rollout is reasonable
# Pick Validation
residual_visualizer.py
<br>
within the pick_validation folder, it takes the three .csv files and calculates the maximum residuals between picks and plots any that are above 100
