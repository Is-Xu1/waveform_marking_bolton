import numpy as np
import pandas as pd
import os
from obspy import read
from pathlib import Path
from scipy.signal import lfilter
import matplotlib.pyplot as plt # Import matplotlib for plotting

# --- Helper Function for Path Components ---
def get_full_path_components(root_dir, file_name):
    """
    Extracts relevant path components and file information.
    """
    full_path = os.path.join(root_dir, file_name)
    p = Path(full_path)
    file_stem = p.stem
    run_num = p.parent.name
    exp_name = p.parent.parent.name
    parts = file_stem.split('_')
    event_id = '_'.join(parts[:2])
    return full_path, exp_name, run_num, event_id, file_stem

# --- Noise Marker Function ---
def noise_marker(path, n_initial_samples):
    """
    Marks points based on deviation from initial noise range.
    
    Parameters:
        path (str): Root directory to search for seismic files.
        n_initial_samples (int): Number of initial samples to define the noise range.
    """
    all_labels = []
    all_label_names = []
    
    print(f"Starting Noise Marking from: {path}")
    
    for root_dir, _, files in os.walk(path):
        for file_name in files:
            full_path, exp_name, run_num, event_id, _ = get_full_path_components(root_dir, file_name)
            
            try:
                st = read(full_path)
            except Exception as e:
                print(f"Skipping file {full_path} due to read error: {e}")
                continue

            for i, tr in enumerate(st):
                trace_data = tr.data.flatten()
                
                label_name_str = f'p_picks_{exp_name}_{run_num}_{event_id}_trace{i+1}'
                all_label_names.append(label_name_str)

                if len(trace_data) < n_initial_samples:
                    print(f"Warning: Trace length ({len(trace_data)}) < n_initial_samples ({n_initial_samples}) for {label_name_str}. No noise marker set.")
                    all_labels.append(-1)
                    continue

                initial_segment = trace_data[:n_initial_samples]
                range_min = initial_segment.min()
                range_max = initial_segment.max()

                deviation_indices = np.where((trace_data > range_max) | (trace_data < range_min))[0]
                
                if len(deviation_indices) > 0:
                    idx = deviation_indices[0]
                    all_labels.append(idx)
                else:
                    all_labels.append(-1)

            print(f'Noise Marking in progress for {file_name}...')
            
    labels_df = pd.DataFrame({'Name': all_label_names, 'marked_point': all_labels})
    output_csv_path = 'p_picks_manual_noise.csv'
    labels_df.to_csv(output_csv_path, index=False)
    print(f"Noise marking complete. Results saved to {output_csv_path}")

# --- Execution Block ---
if __name__ == "__main__":
    # Ensure you have 'nolds', 'obspy', 'pandas', and 'matplotlib' installed:
    # pip install nolds obspy pandas matplotlib

    # Define the data path
    data_directory = r'F:\Data'

    # Noise marker parameters
    initial_noise_window_size = 100000 
    
    print(f"Starting seismic data processing in {data_directory}")

    # Run the noise marker
    noise_marker(data_directory, initial_noise_window_size)

    # --- AR Marker Parameters ---
    # Set debug_first_n_plots to a number (e.g., 5) to see plots for the first few traces.
    # Set to 0 to disable all plots during batch processing.
    debug_plots_count = 5 
    
    # Run the AR-based marker

    print("\nAll seismic picking operations completed.")