import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
import numpy as np
import pandas as pd
from obspy import read
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

# --- Load Pick Data ---
hand_picks = pd.read_csv('p_picks_Data.csv')
noise_picks = pd.read_csv('p_picks_manual_noise.csv')
sta_picks = pd.read_csv('p_picks_sta_lta.csv')

# --- Merge Picks and Compute Max Residual ---
merged = hand_picks.merge(noise_picks, on='Name', suffixes=('_hand', '_noise'))
merged = merged.merge(sta_picks, on='Name')
merged.rename(columns={'marked_point': 'marked_point_sta'}, inplace=True)

def calc_max_residual(row):
    picks = [row['marked_point_hand'], row['marked_point_noise'], row['marked_point_sta']]
    return max(abs(p1 - p2) for i, p1 in enumerate(picks) for j, p2 in enumerate(picks) if i < j)

merged['max_residual'] = merged.apply(calc_max_residual, axis=1)
filtered = merged[merged['max_residual'] > 100].reset_index(drop=True)

print(f"Total mismatches with residual > 100: {len(filtered)}")

class ResidualViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("Waveform Residual Viewer")
        self.master.protocol("WM_DELETE_WINDOW", self.close_app)
        self.index = 0

        # --- Label Display ---
        self.label = tk.Label(master, text="", font=("Helvetica", 10, "bold"))
        self.label.pack(pady=5)

        # --- Plot Frame ---
        self.plot_frame = tk.Frame(master)
        self.plot_frame.pack(fill="both", expand=True)

        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Control Buttons ---
        self.btn_frame = tk.Frame(master)
        self.btn_frame.pack(pady=5)

        self.prev_btn = tk.Button(self.btn_frame, text="Prev", command=self.prev)
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = tk.Button(self.btn_frame, text="Next", command=self.next)
        self.next_btn.pack(side=tk.LEFT, padx=5)

        self.load_btn = tk.Button(self.btn_frame, text="Select root 'data' folder", command=self.select_folder)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.folder = None
        self.update_plot()

    def close_app(self):
        print("Closing application.")
        self.master.destroy()
        exit()

    def select_folder(self):
        self.folder = filedialog.askdirectory(title="Select root folder containing Exp_T folders")
        print(f"Selected folder: {self.folder}")
        self.update_plot()

    def parse_path_from_name(self, name):
        print(f"Parsing name: {name}")
        match = re.search(r'Exp_(T\d+)_Run(\d+)_EventID_(\d+)', name)
        if not match:
            print("Regex match failed.")
            return None
        exp, run, event = match.groups()
        folder_path = os.path.join(self.folder, f"Exp_{exp}", f"Run{run}")
        file_name = f"EventID_{event}_WindowSize_0.05s_Data.mseed"
        full_path = os.path.join(folder_path, file_name)
        print(f"Constructed path: {full_path}")
        return full_path

    def update_plot(self):
        if self.folder is None or self.index >= len(filtered):
            print("No folder selected or index out of range.")
            return

        row = filtered.iloc[self.index]
        name = row['Name']
        self.label.config(text=f"Viewing: {name} | Residual: {row['max_residual']:.1f}")

        mseed_path = self.parse_path_from_name(name)
        if not mseed_path or not os.path.isfile(mseed_path):
            print(f"File not found: {mseed_path}")
            messagebox.showwarning("File Not Found", f"Could not locate .mseed for: {name}")
            return

        try:
            st = read(mseed_path)
            print(f"Read {len(st)} trace(s) from {mseed_path}")
            tr = st[0]
            data = tr.data
            t = np.arange(len(data)) / tr.stats.sampling_rate
        except Exception as e:
            print(f"Error reading waveform: {e}")
            messagebox.showerror("Error", f"Failed to read waveform: {e}")
            return

        # Plotting
        self.ax.clear()
        self.ax.plot(t, data, label='Waveform', alpha=0.7)
        self.ax.axvline(row['marked_point_hand'] / tr.stats.sampling_rate, color='r', label='Hand')
        self.ax.axvline(row['marked_point_noise'] / tr.stats.sampling_rate, color='g', label='Noise')
        self.ax.axvline(row['marked_point_sta'] / tr.stats.sampling_rate, color='b', label='STA/LTA')
        self.ax.legend()
        self.ax.set_title(f"{name}")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Amplitude")
        self.canvas.draw()

    def next(self):
        if self.index < len(filtered) - 1:
            self.index += 1
            print(f"Moving to next index: {self.index}")
            self.update_plot()

    def prev(self):
        if self.index > 0:
            self.index -= 1
            print(f"Moving to previous index: {self.index}")
            self.update_plot()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x600")
    viewer = ResidualViewer(root)
    root.mainloop()
