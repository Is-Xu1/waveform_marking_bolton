import numpy as np
import pandas as pd
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, messagebox 
import sys
from obspy import read
import os
from pathlib import Path

# Global state variables
global waveforms, labels, n, label_df, foldername, file_name
waveforms = []
labels = []
n = 0
label_df = pd.DataFrame()
foldername = ""
file_name = ""
current_index = 0
label_exists = False

# Helper function to load waveform data
def load_waveform_data(path):
    global waveforms, labels, n, label_df, foldername, file_name, label_exists, current_index

    waveforms = []
    label_names = []
    label_exists = False

    if os.path.isfile(path):
        p = Path(path)
        file_name = p.stem
        run_num = p.parent.name
        exp_name = p.parent.parent.name
        st = read(path)
        waveform = np.array([tr.data for tr in st])
        waveforms = waveform
        n = len(waveforms)
        parts = file_name.split('_')
        event_id = '_'.join(parts[:2])
        trace_labels = np.array([f'p_picks_{exp_name}_{run_num}_{event_id}_trace{i+1}' for i in range(n)])
        try:
            label_df = pd.read_csv(f'p_picks_{file_name}.csv')
            labels = label_df['marked_point'].to_numpy()
            unlabeled = label_df[label_df['marked_point'] == -1]
            current_index = unlabeled.index[0] if not unlabeled.empty else 0
            label_exists = True
        except:
            labels = np.full(n, -1)
            label_df = pd.DataFrame({'Name': trace_labels, 'marked_point': labels})

    elif os.path.isdir(path):
        foldername = os.path.basename(path)
        try:
            try:
                label_df = pd.read_csv(f'p_picks_{foldername}.csv')
                labels = label_df['marked_point'].to_numpy()
                unlabeled = label_df[label_df['marked_point'] == -1]
                current_index = unlabeled.index[0] if not unlabeled.empty else 0
                label_exists = True
            except:
                print(f'No existing labels file found, creating a new one')

            for root_dir, sub_dirs, files in os.walk(path):
                for file_name in files:
                    full_path = os.path.join(root_dir, file_name)
                    try:
                        st = read(full_path)
                        print(f'Appended {full_path}')
                        p = Path(full_path)
                        run_num = p.parent.name
                        exp_name = p.parent.parent.name
                        file_base = p.stem
                        parts = file_base.split('_')
                        event_id = '_'.join(parts[:2])
                        for i, tr in enumerate(st):
                            waveforms.append(tr.data)
                            if not label_exists:
                                label_names.append(f'p_picks_{exp_name}_{run_num}_{event_id}_trace{i+1}')
                    except Exception as e:
                        print(f"Skipped {full_path}: {e}")
            waveforms = np.array(waveforms, dtype=object)
            n = len(waveforms)
            if not label_exists:
                labels = np.full(n, -1)
                label_df = pd.DataFrame({'Name': label_names, 'marked_point': labels})
        except Exception as e:
            messagebox.showerror('Error opening folder', f'Unable to open {path}, Error: {str(e)}')

# Initial file prompt
root = tk.Tk()
root.title('Waveform Labeling')
root.geometry("1000x800")
root.minsize(1000, 800)

path = filedialog.askdirectory(title='Select waveform file or folder')
if not path:
    messagebox.showwarning('No file selected', 'You must select a waveform file or folder.')
    root.destroy()
    sys.exit()
else:
    load_waveform_data(path)

# Event and drawing logic
def on_click(event):
    global labels
    if event.inaxes and event.xdata is not None:
        ix = int(event.xdata)
        labels[current_index] = ix
        redraw_plot()

def redraw_plot():
    global cursor_line
    ax.clear()
    waveform = waveforms[current_index]
    ax.plot(waveform, label='Waveform')
    if labels[current_index] != -1:
        ax.axvline(labels[current_index], color='red', linestyle='-', label='Marked Point')
        cursor_line = ax.axvline(labels[current_index], color='red', linestyle='--', alpha=0.4)
    else:
        cursor_line = ax.axvline(0, color='red', linestyle='--', alpha=0.4)
    ax.legend()
    ax.set_title(f"Waveform {current_index + 1}/{n}")
    canvas.draw()
    update_button_states()

def uploadfile():
    global current_index
    new_path = filedialog.askdirectory(title='Select waveform file or folder')
    if new_path:
        load_waveform_data(new_path)
        current_index = 0
        redraw_plot()

def prev_waveform():
    global current_index
    if current_index > 0:
        current_index -= 1
        redraw_plot()

def next_waveform():
    global current_index
    if current_index < n - 1:
        current_index += 1
        redraw_plot()

def save_labels_csv():
    filename = f'p_picks_{foldername}.csv' if os.path.isdir(path) else f'p_picks_{file_name}.csv'
    label_df['marked_point'] = labels
    label_df.to_csv(filename, index=False)
    messagebox.showinfo('File saved', f'Saved to {filename}')

def update_button_states():
    prev_btn.config(state=tk.DISABLED if current_index <= 0 else tk.NORMAL)
    next_btn.config(state=tk.DISABLED if current_index >= n - 1 else tk.NORMAL)

def on_mouse_move(event):
    global cursor_line
    if event.inaxes and event.xdata is not None:
        try:
            cursor_line.set_xdata([event.xdata])
            canvas.draw_idle()
        except Exception as e:
            print("Cursor update error:", e)

def on_close():
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW", on_close)

# GUI Layout

top_frame = tk.Frame(root)
top_frame.pack(fill='x', pady=10)

instruction_label = tk.Label(
    top_frame,
    text="Click on the waveform to mark a point of interest.\nUse Next/Previous to navigate. Save to export labels.",
    justify='center', font=("Arial", 15), anchor='center')
instruction_label.pack(anchor='center')

fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill='both', expand=True)
canvas.mpl_connect('button_press_event', on_click)
canvas.mpl_connect('motion_notify_event', on_mouse_move)

controls = tk.Frame(root)
controls.pack(fill='x', pady=10)

prev_btn = tk.Button(controls, text="Previous", command=prev_waveform, width=12, height=2)
prev_btn.pack(side=tk.LEFT, padx=5)

next_btn = tk.Button(controls, text="Next", command=next_waveform, width=12, height=2)
next_btn.pack(side=tk.LEFT, padx=5)

save_btn = tk.Button(controls, text="Save", command=save_labels_csv, width=12, height=2)
save_btn.pack(side=tk.LEFT, padx=5)

file_btn = tk.Button(controls, text="Import File", command=uploadfile, width=12, height=2)
file_btn.pack(side=tk.LEFT, padx=5)

redraw_plot()
update_button_states()
root.mainloop()
