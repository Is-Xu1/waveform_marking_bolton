import numpy as np
import pandas as pd
import os
from obspy import read
from pathlib import Path
from obspy.signal.trigger import classic_sta_lta, trigger_onset
import matplotlib.pyplot as plt  # Optional: for visual debugging

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


def sta_lta_picker(path, sta_win=200, lta_win=7500, threshold_on=12, threshold_off=0.3):
    all_p_labels = []
    all_label_names = []

    print(f"Starting STA/LTA picking from: {path}")

    for root_dir, _, files in os.walk(path):
        for file_name in files:
            full_path, exp_name, run_num, event_id, file_stem = get_full_path_components(root_dir, file_name)

            try:
                st = read(full_path)
                st.detrend("demean")  # still remove DC offset
            except Exception as e:
                print(f"[ERROR] Failed to read {full_path}: {e}")
                continue

            for i, tr in enumerate(st):
                label_name_str = f'p_picks_{exp_name}_{run_num}_{event_id}_trace{i+1}'
                all_label_names.append(label_name_str)
                data = tr.data.astype(np.float32)

                try:
                    print(f"[DEBUG] Trace {label_name_str} length: {len(data)}")

                    if len(data) < lta_win * 2:
                        print(f"[WARN] Trace {label_name_str} too short ({len(data)} samples), skipping.")
                        all_p_labels.append(-1)
                        continue

                    if np.isnan(data).any() or np.isinf(data).any():
                        print(f"[WARN] Trace {label_name_str} contains NaNs or Infs, skipping.")
                        all_p_labels.append(-1)
                        continue

                    # No filter or normalization here
                    cft = classic_sta_lta(data, int(sta_win), int(lta_win))
                    max_cft = np.max(cft)
                    print(f"[DEBUG] Max STA/LTA for {label_name_str}: {max_cft:.2f}")

                    on_off = trigger_onset(cft, threshold_on, threshold_off)

                    if len(on_off) > 0:
                        first_trigger = on_off[0][0]
                        print(f"[DEBUG] Trigger at {first_trigger} for {label_name_str}")

                        if first_trigger >= int(lta_win * 0.8):  # allow early picks just past LTA start
                            all_p_labels.append(first_trigger)
                            print(f"[OK] Picked at {first_trigger} with threshold {threshold_on:.2f} for {label_name_str}")
                        else:
                            print(f"[INFO] Trigger at {first_trigger} too close to LTA start for {label_name_str}")
                            all_p_labels.append(-1)
                    else:
                        print(f"[INFO] No trigger found at threshold {threshold_on:.2f} for {label_name_str}")
                        all_p_labels.append(-1)

                except Exception as e:
                    print(f"[ERROR] STA/LTA failed on {label_name_str}: {e}")
                    all_p_labels.append(-1)
                    continue

            print(f"Finished processing {file_name}")

    labels_df = pd.DataFrame({
        'Name': all_label_names,
        'marked_point': all_p_labels
    })
    output_csv_path = 'p_picks_sta_lta.csv'
    labels_df.to_csv(output_csv_path, index=False)
    print(f"\nSTA/LTA picking complete. Results saved to {output_csv_path}")








if __name__ == "__main__":
    data_directory = r'F:\Data'
    print(f"Starting seismic data processing in {data_directory}")
    sta_lta_picker(data_directory)
    print("\nAll seismic picking operations completed.")

