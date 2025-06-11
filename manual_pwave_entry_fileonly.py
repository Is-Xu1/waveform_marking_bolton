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
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk


# Global state variables
global waveforms, labels, n, label_df, foldername, file_name, zoom_limits
zoom_limits = {"xlim": None, "ylim": None}
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
    global waveforms, labels, n, label_df, foldername, file_name, label_exists, current_index, filename

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
        filename = f'{exp_name}_{run_num}_{event_id}'
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            folder = 'picks_folder'
            folder_path = os.path.join(script_dir, folder)
            file_path = os.path.join(folder_path,f'p_picks_{filename}.csv')
            label_df = pd.read_csv(file_path)
            labels = label_df['marked_point'].to_numpy()
            unlabeled = label_df[label_df['marked_point'] == -1]
            current_index = unlabeled.index[0] if not unlabeled.empty else 0
            label_exists = True
        except:
            labels = np.full(n, -1)
            label_df = pd.DataFrame({'Name': trace_labels, 'marked_point': labels})


    elif os.path.isdir(path):
        foldername = os.path.basename(path)
        file_name = foldername
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

root.withdraw()
top_frame = tk.Frame(root)
top_frame.pack(fill='x', pady=10)

file_label = tk.Label(top_frame, text="", wraplength=900, justify='center', font=("Arial", 12), fg="blue")
file_label.pack(anchor='center', pady=(5, 10))

path = filedialog.askopenfilename(title='Select waveform file or folder')
if not path:
    messagebox.showwarning('No file selected', 'You must select a waveform file or folder.')
    root.destroy()
    sys.exit()
else:
    load_waveform_data(path)
    file_label.config(text=f"Loaded: {file_name}")
    root.deiconify()

# Event and drawing logic
def on_click(event):
    global labels,current_index
    if event.inaxes and event.xdata is not None:
        ix = int(event.xdata)
        labels[current_index] = ix
        '''if current_index != len(waveforms)-1:
            current_index += 1'''
        redraw_plot()

def go_to_index():
    global current_index
    try:
        idx = int(goto_entry.get())
        if 0 < idx <= n:
            current_index = idx -1
            redraw_plot()
        else:
            messagebox.showwarning("Invalid index", f"Please enter a number between 0 and {n-1}")
    except ValueError:
        messagebox.showwarning("Invalid input", "Please enter a valid integer")

def redraw_plot():
    global cursor_line, zoom_limits
    ax.clear()
    waveform = waveforms[current_index]
    ax.plot(waveform, label='Waveform')
    if labels[current_index] != -1:
        ax.axvline(labels[current_index], color='red', linestyle='-', label='Marked Point')
        cursor_line = ax.axvline(labels[current_index], color='red', linestyle='--', alpha=0.4)
    else:
        cursor_line = ax.axvline(0, color='red', linestyle='--', alpha=0.4)
    ax.set_title(f"Waveform {current_index + 1}/{n}")
    if zoom_limits["xlim"] or zoom_limits['ylim']:
        ax.set_xlim(zoom_limits["xlim"])
        ax.set_xlim(zoom_limits['ylim'])
    else:
        # Set default full view for x-axis and auto y-axis
        ax.set_xlim(0, len(waveform))
        ax.autoscale(axis='y')
    canvas.draw()
    update_button_states()

def uploadfile():
    global current_index
    new_path = filedialog.askopenfilename(title='Select waveform file or folder')
    if new_path:
        load_waveform_data(new_path)
        current_index = 0
        redraw_plot()
        file_label.config(text=f"Loaded: {file_name}")


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
    global filename
    filename1 = f'p_picks_{foldername}.csv' if os.path.isdir(path) else f'p_picks_{filename}.csv'
    label_df['marked_point'] = labels

    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = 'picks_folder'
    folder_path = os.path.join(script_dir, folder)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path,filename1)
    label_df.to_csv(file_path, index=False)
    messagebox.showinfo('File saved', f'Saved as {filename} at {folder_path}')

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

def on_scroll(event):
    global zoom_limits
    if event.inaxes is None:
        return
    ax = event.inaxes
    scale_factor = 1.2 if event.button == 'up' else 0.8

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_center = event.ydata
    x_center = event.xdata
    new_xlim = [x_center + (x - x_center) * scale_factor for x in xlim]
    new_ylim = [y_center + (y - y_center) * scale_factor for y in xlim]
    ax.set_xlim(new_xlim)
    #ax.set_ylim(new_ylim)
    zoom_limits['xlim'] = new_xlim
    #zoom_limits['ylim'] = new_ylim
    canvas.draw_idle()

def on_close():
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW", on_close)

# GUI Layout


instruction_label = tk.Label(
    top_frame,
    text=f"Click on the waveform to mark a point of interest.\nUse Next/Previous to navigate. Save to export labels.",
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
canvas.mpl_connect('scroll_event', on_scroll)

goto_btn = tk.Button(controls, text="Go", command=go_to_index, width=6, height=2)
goto_btn.pack(side=tk.LEFT, padx=5)

goto_entry = tk.Entry(controls, width=6)
goto_entry.pack(side=tk.LEFT, padx=5)
toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
toolbar.pack(side=tk.TOP, fill=tk.X)


redraw_plot()
update_button_states()
root.mainloop()
