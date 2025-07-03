import numpy as np
import pandas as pd
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import filedialog, messagebox
import sys
from obspy import read
import os
from pathlib import Path

# Global state
waveforms = []
labels = []
n = 0
label_df = pd.DataFrame()
foldername = ""
file_name = ""
filename = ""
zoom_limits = {"xlim": None, "ylim": None}
current_index = 0
label_exists = False
new_path = ""
trace_file_paths = []
trace_metadata = []

def load_waveform_data(path):
    global waveforms, labels, n, label_df, foldername, file_name, label_exists, current_index, filename, zoom_limits
    waveforms = []
    trace_file_paths.clear()
    trace_metadata.clear()
    label_names = []
    label_exists = False
    zoom_limits = {"xlim": None, "ylim": None}

    if os.path.isfile(path):
        p = Path(path)
        file_name = p.stem
        run_num = p.parent.name
        exp_name = p.parent.parent.name
        st = read(path)
        waveforms = [tr.data for tr in st]
        n = len(waveforms)
        parts = file_name.split('_')
        event_id = '_'.join(parts[:2])
        trace_labels = [f'p_picks_{exp_name}_{run_num}_{event_id}_trace{i+1}' for i in range(n)]
        filename = f'{exp_name}_{run_num}_{event_id}'
        try:
            folder_path = os.path.join(os.path.dirname(__file__), 'picks_folder')
            file_path = os.path.join(folder_path, f'p_picks_{filename}.csv')
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
                print('No existing labels found. Creating new.')

            for root_dir, _, files in os.walk(path):
                for file_name in files:
                    full_path = os.path.join(root_dir, file_name)
                    try:
                        st = read(full_path)
                        print(f'Appended {full_path}')
                        p = Path(full_path)
                        run_num = p.parent.name
                        exp_name = p.parent.parent.name
                        file_base = p.stem
                        event_id = '_'.join(file_base.split('_')[:2])
                        for i, tr in enumerate(st):
                            waveforms.append(tr.data)
                            trace_file_paths.append(full_path)
                            trace_metadata.append(f"Experiment: {exp_name}, Run: {run_num}, Trace: trace{i+1}")
                        if not label_exists:
                            for i in range(len(st)):
                                local_trace_number = i + 1
                                trace_label = f'p_picks_{exp_name}_{run_num}_{event_id}_trace{local_trace_number}'
                                label_names.append(trace_label)
                    except Exception as e:
                        print(f"Skipped {full_path}: {e}")
            n = len(waveforms)
            if not label_exists:
                labels = np.full(n, -1)
                label_df = pd.DataFrame({'Name': label_names, 'marked_point': labels})
        except Exception as e:
            messagebox.showerror('Error', f'Unable to open folder: {str(e)}')

def rollout_viewer():
    def load_new_rollout():
        new_path = filedialog.askopenfilename(title='Select a .mseed file for rollout')
        if not new_path:
            return
        try:
            st = read(new_path)
            traces = [tr.data for tr in st]
            ax_rollout.clear()
            offset = 5
            for i, tr in enumerate(traces):
                ax_rollout.plot(tr + i * offset, label=f"Trace {i+1}")
            ax_rollout.set_title(f"Rollout: {os.path.basename(new_path)} (offset by 5)")
            ax_rollout.set_xlabel("Sample Index")
            ax_rollout.set_ylabel("Amplitude + Offset")
            ax_rollout.legend(loc='upper right', fontsize='small')
            canvas_rollout.draw()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    rollout_path = filedialog.askopenfilename(title='Select a .mseed file for rollout')
    if not rollout_path:
        return
    try:
        st = read(rollout_path)
        traces = [tr.data for tr in st]
        rollout_win = tk.Toplevel(root)
        rollout_win.title(f"Rollout: {os.path.basename(rollout_path)}")
        rollout_win.geometry("1000x800")
        fig_rollout, ax_rollout = plt.subplots()
        canvas_rollout = FigureCanvasTkAgg(fig_rollout, master=rollout_win)
        canvas_rollout.get_tk_widget().pack(fill='both', expand=True)
        offset = 5
        for i, tr in enumerate(traces):
            ax_rollout.plot(tr + i * offset, label=f"Trace {i+1}")
        ax_rollout.set_title(f"Rollout: {os.path.basename(rollout_path)} (offset by 5)")
        ax_rollout.set_xlabel("Sample Index")
        ax_rollout.set_ylabel("Amplitude + Offset")
        ax_rollout.legend(loc='upper right', fontsize='small')
        canvas_rollout.draw()
        toolbar_rollout = NavigationToolbar2Tk(canvas_rollout, rollout_win)
        toolbar_rollout.update()
        toolbar_rollout.pack(side=tk.TOP, fill=tk.X)
        load_button_frame = tk.Frame(rollout_win)
        load_button_frame.pack(pady=10)
        load_btn = tk.Button(load_button_frame, text="Load .mseed", command=load_new_rollout, width=15)
        load_btn.pack()
    except Exception as e:
        messagebox.showerror("Error", str(e))


def redraw_plot():
    global cursor_line, zoom_limits
    waveform = waveforms[current_index]
    current_xlim = ax.get_xlim() if zoom_limits["xlim"] else (0, len(waveform))
    current_ylim = ax.get_ylim() if zoom_limits["ylim"] else (waveform.min(), waveform.max())
    ax.clear()
    ax.plot(waveform, label='Waveform')
    if labels[current_index] != -1:
        ax.axvline(labels[current_index], color='red', linestyle='-', label='Marked Point')
        cursor_line = ax.axvline(labels[current_index], color='red', linestyle='--', alpha=0.4)
    else:
        cursor_line = ax.axvline(0, color='red', linestyle='--', alpha=0.4)
    ax.set_title(f"Waveform {current_index + 1}/{n}")
    ax.set_xlim(current_xlim)
    ax.set_ylim(current_ylim)
    fig.tight_layout()
    canvas.draw()
    zoom_limits["xlim"] = ax.get_xlim()
    zoom_limits["ylim"] = ax.get_ylim()
    if trace_file_paths:
        file_label.config(text=f"File: {os.path.basename(trace_file_paths[current_index])}")
    else:
        file_label.config(text=f"Source: {file_name}")
    if trace_metadata:
        metadata_label.config(text=trace_metadata[current_index])
    else:
        metadata_label.config(text="")
    update_button_states()

def rollout_viewer():
    def load_new_rollout():
        new_path = filedialog.askopenfilename(title='Select a .mseed file for rollout')
        if not new_path:
            return
        try:
            st = read(new_path)
            traces = [tr.data for tr in st]
            ax_rollout.clear()
            offset = 5
            for i, tr in enumerate(traces):
                ax_rollout.plot(tr + i * offset, label=f"Trace {i+1}")
            ax_rollout.set_title(f"Rollout: {os.path.basename(new_path)} (offset by 5)")
            ax_rollout.set_xlabel("Sample Index")
            ax_rollout.set_ylabel("Amplitude + Offset")
            ax_rollout.legend(loc='upper right', fontsize='small')
            canvas_rollout.draw()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    rollout_path = filedialog.askopenfilename(title='Select a .mseed file for rollout')
    if not rollout_path:
        return
    try:
        st = read(rollout_path)
        traces = [tr.data for tr in st]
        rollout_win = tk.Toplevel(root)
        rollout_win.title(f"Rollout: {os.path.basename(rollout_path)}")
        rollout_win.geometry("1000x800")
        fig_rollout, ax_rollout = plt.subplots()
        canvas_rollout = FigureCanvasTkAgg(fig_rollout, master=rollout_win)
        canvas_rollout.get_tk_widget().pack(fill='both', expand=True)
        offset = 5
        for i, tr in enumerate(traces):
            ax_rollout.plot(tr + i * offset, label=f"Trace {i+1}")
        ax_rollout.set_title(f"Rollout: {os.path.basename(rollout_path)} (offset by 5)")
        ax_rollout.set_xlabel("Sample Index")
        ax_rollout.set_ylabel("Amplitude + Offset")
        ax_rollout.legend(loc='upper right', fontsize='small')
        canvas_rollout.draw()
        toolbar_rollout = NavigationToolbar2Tk(canvas_rollout, rollout_win)
        toolbar_rollout.update()
        toolbar_rollout.pack(side=tk.TOP, fill=tk.X)
        load_button_frame = tk.Frame(rollout_win)
        load_button_frame.pack(pady=10)
        load_btn = tk.Button(load_button_frame, text="Load .mseed", command=load_new_rollout, width=15)
        load_btn.pack()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def uploadfile(folder=False):
    global current_index, new_path
    new_path = filedialog.askdirectory(title='Select folder') if folder else filedialog.askopenfilename(title='Select file')
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

def go_to_index():
    global current_index
    try:
        idx = int(goto_entry.get())
        if 0 < idx <= n:
            current_index = idx - 1
            redraw_plot()
        else:
            messagebox.showwarning("Invalid index", f"Please enter a number between 0 and {n}")
    except ValueError:
        messagebox.showwarning("Invalid input", "Enter an integer.")

def save_labels_csv():
    filename1 = f'p_picks_{foldername}.csv' if os.path.isdir(new_path) else f'p_picks_{filename}.csv'
    label_df['marked_point'] = labels
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename1)
    label_df.to_csv(file_path, index=False)
    messagebox.showinfo('Saved', f'Saved as {filename1} in {script_dir}')

def update_button_states():
    prev_btn.config(state=tk.DISABLED if current_index <= 0 else tk.NORMAL)
    next_btn.config(state=tk.DISABLED if current_index >= n - 1 else tk.NORMAL)

def on_click(event):
    if getattr(canvas.toolbar, 'mode', '') != '':
        return
    if event.inaxes and event.xdata is not None:
        labels[current_index] = int(event.xdata)
        redraw_plot()

def on_mouse_move(event):
    if event.inaxes and event.xdata is not None:
        try:
            cursor_line.set_xdata([event.xdata])
            canvas.draw_idle()
        except Exception:
            pass

def reset_zoom():
    global zoom_limits
    zoom_limits = {"xlim": None, "ylim": None}
    redraw_plot()

def on_scroll(event):
    if event.inaxes is None:
        return
    ax = event.inaxes
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    scale_x = 1.2 if event.button == 'up' else 0.8
    scale_y = 1.05 if event.button == 'up' else 0.95
    xdata = event.xdata
    ydata = event.ydata
    ctrl_pressed = event.key == 'control'
    if ctrl_pressed and ydata is not None:
        ax.set_ylim([ydata + (y - ydata) * scale_y for y in ylim])
    elif xdata is not None:
        ax.set_xlim([xdata + (x - xdata) * scale_x for x in xlim])
    canvas.draw_idle()

def on_draw(event):
    zoom_limits["xlim"] = ax.get_xlim()
    zoom_limits["ylim"] = ax.get_ylim()

def on_close():
    root.destroy()
    sys.exit()

def on_resize(event):
    if waveforms:
        redraw_plot()

root = tk.Tk()
root.title("Waveform Labeling")
root.geometry("1000x800")
root.protocol("WM_DELETE_WINDOW", on_close)
root.bind("<Configure>", on_resize)

top_frame = tk.Frame(root)
top_frame.pack(fill='x', pady=10)

file_label = tk.Label(top_frame, text="", font=("Arial", 12), fg="blue")
file_label.pack()
metadata_label = tk.Label(top_frame, text="", font=("Arial", 11))
metadata_label.pack()

instruction = tk.Label(top_frame, text="Click to mark. Use Next/Previous. Scroll to zoom x. Ctrl+scroll for y.", font=("Arial", 13))
instruction.pack()

button_frame = tk.Frame(top_frame)
button_frame.pack(pady=5)
tk.Button(button_frame, text="Load File", command=lambda: uploadfile(folder=False), width=12).pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Load Folder", command=lambda: uploadfile(folder=True), width=12).pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Rollout", command=rollout_viewer, width=12).pack(side=tk.LEFT, padx=5)

fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill='both', expand=True)
canvas.mpl_connect('button_press_event', on_click)
canvas.mpl_connect('motion_notify_event', on_mouse_move)
canvas.mpl_connect('scroll_event', on_scroll)
canvas.mpl_connect('draw_event', on_draw)

controls = tk.Frame(root)
controls.pack(pady=10)
prev_btn = tk.Button(controls, text="Previous", command=prev_waveform, width=12)
next_btn = tk.Button(controls, text="Next", command=next_waveform, width=12)
save_btn = tk.Button(controls, text="Save", command=save_labels_csv, width=12)
goto_entry = tk.Entry(controls, width=6)
goto_btn = tk.Button(controls, text="Go", command=go_to_index, width=6)
reset_btn = tk.Button(controls, text="Reset Zoom", command=reset_zoom, width=12)
reset_btn.pack(side=tk.LEFT, padx=5)
prev_btn.pack(side=tk.LEFT, padx=5)
next_btn.pack(side=tk.LEFT, padx=5)
save_btn.pack(side=tk.LEFT, padx=5)
goto_entry.pack(side=tk.LEFT, padx=5)
goto_btn.pack(side=tk.LEFT, padx=5)

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
toolbar.pack(side=tk.TOP, fill=tk.X)

root.mainloop()
