# Python Interactive UI for Manual Waveform Marking <br>
## University of Texas at Austin
Created by Isaac Xu and Dr. Chas Bolton
# Download instructions
Download python file and run requirements.txt 
# Overview
Created for marking p-wave arrivals for waveforms using manual user input, saves user clicked x axis positions as a separate csv file for further analysis. 
Accepted waveform file formats are .mseed
<br> 
The script treats each trace in the stream as separate for marking, it takes in a folder of .mseed files and uses the structure of the folder for naming. The folder should be structure as 
data/experiment_name/run_num/.mseed_files_here for the automatic labeling to be accurate. 
