import numpy as np
import pandas as pd
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import filedialog, messagebox 
import sys
from obspy import read
import os
from natsort import natsorted

# Global variables
current_index = 0
path_list = []
waveform = []
labels_list = []
labels = []

script_dir = os.path.dirname(os.path.abspath(__file__))

def load_waveform_paths(path):
    for root_dir, sub_dirs, files in os.walk(os.path.join(path, 'waveforms')):
        for file_name in natsorted(files):
            full_path = os.path.join(root_dir, file_name)
            path_list.append(full_path)

def load_waveform_data():
    global waveform, current_index
    waveform = []  # Clear previous waveform
    waveform_path = path_list[current_index]
    st = read(waveform_path)
    for i, tr in enumerate(st):
        waveform.append(tr.data + 5 * (i + 1))  # vertically offset each trace

def load_labels_paths(path):
    for root_dir, sub_dirs, files in os.walk(os.path.join(path, 'picks_folder')):
        for file_name in natsorted(files):
            full_path = os.path.join(root_dir, file_name)
            labels_list.append(full_path)

def load_labels_data():
    global labels_list, current_index, labels
    label_path = labels_list[current_index]
    labels_df = pd.read_csv(label_path)
    labels = labels_df['marked_point'].tolist()

def redraw_plot():
    global path_list, labels
    load_waveform_data()
    load_labels_data()
    ax.clear()
    for trace in waveform:
        ax.plot(trace, label='Waveform', color ='#1f77b4')
    for i, point in enumerate(labels):
        ax.plot([point, point], [-2+5*(i+1), 2+5*(i+1)], linestyle='-', color='red')
    ax.set_title(f'Waveform {current_index + 1} of {len(path_list)}')
    filename = os.path.basename(path_list[current_index])
    filename_label.config(text=f"File: {filename}")
    canvas.draw()
    update_button_states()

def prev_waveform():
    global current_index
    if current_index > 0:
        current_index -= 1
        redraw_plot()

def next_waveform():
    global current_index
    if current_index < len(path_list) - 1:
        current_index += 1
        redraw_plot()

def update_button_states():
    global path_list
    prev_btn.config(state=tk.DISABLED if current_index <= 0 else tk.NORMAL)
    next_btn.config(state=tk.DISABLED if current_index >= len(path_list) - 1 else tk.NORMAL)


# Setup Tkinter GUI
root = tk.Tk()
root.title('Waveform Roll Out')
root.geometry("1000x800")
root.minsize(1000, 800)

def on_close():
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW", on_close)

top_frame = tk.Frame(root)
top_frame.pack(fill='x', pady=10)

instruction_label = tk.Label(
    top_frame,
    text=f"Click next to see other waveforms",
    justify='center', font=("Arial", 15), anchor='center')
instruction_label.pack(anchor='center')

fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill='both', expand=True)

filename_label = tk.Label(top_frame, text="", font=("Arial", 12), fg="blue")
filename_label.pack(anchor='center')

controls = tk.Frame(root)
controls.pack(fill='x', pady=10)

prev_btn = tk.Button(controls, text="Previous", command=prev_waveform, width=12, height=2)
prev_btn.pack(side=tk.LEFT, padx=5)

next_btn = tk.Button(controls, text="Next", command=next_waveform, width=12, height=2)
next_btn.pack(side=tk.LEFT, padx=5)

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
toolbar.pack(side=tk.TOP, fill=tk.X)

# Load data and run GUI
load_waveform_paths(script_dir)
load_labels_paths(script_dir)
redraw_plot()
update_button_states()

root.mainloop()
