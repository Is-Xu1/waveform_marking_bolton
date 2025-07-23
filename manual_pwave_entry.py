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
import ast

# Global state
waveforms = []
n = 0
picks_per_trace = []
max_picks = 5
foldername = ""
file_name = ""
filename = ""
zoom_limits = {"xlim": None, "ylim": None}
current_index = 0
new_path = ""
trace_file_paths = []
trace_metadata = []
ctrl_held = False
cursor_line = None
selected_pick_slot = 0
trace_names = []
csv_path = ""
label_map = {}  # Name -> list of picks

colors = ['red', 'green', 'blue', 'orange', 'purple']


def load_waveform_data(path):
    """
    Loads and caches the waveforms from a directory or file, this process can be quite RAM intensive - use smaller folders and combine later
    Input:
    -----
    - path (str) - absolute path to directory/file
    """
    global waveforms, picks_per_trace, n, foldername, file_name, filename, zoom_limits
    global trace_names, csv_path, label_map

    waveforms.clear()
    trace_file_paths.clear()
    trace_metadata.clear()
    trace_names.clear()
    picks_per_trace.clear()
    zoom_limits = {"xlim": None, "ylim": None}
    label_map.clear()

    #logic for file
    if os.path.isfile(path):
        p = Path(path)
        #this builds the name based on the directory
        file_name = p.stem
        run_num = p.parent.name
        exp_name = p.parent.parent.name
        st = read(path)
        waveforms[:] = [tr.data for tr in st]
        n = len(waveforms)
        picks_per_trace[:] = [[None] * max_picks for _ in range(n)]
        filename = f'{exp_name}_{run_num}_{file_name}'
        parts = file_name.split('_')
        event_id = '_'.join(parts[:2])
        trace_names[:] = [f'p_picks_{exp_name}_{run_num}_{event_id}_trace{i+1}' for i in range(n)]
        csv_path = os.path.join(os.path.dirname(__file__), f'p_picks_{filename}.csv')

    #logic for directory
    elif os.path.isdir(path):
        foldername = os.path.basename(path)
        for root_dir, _, files in os.walk(path):
            for file_name in files:
                full_path = os.path.join(root_dir, file_name)
                try:
                    st = read(full_path)
                    p = Path(full_path)
                    run_num = p.parent.name
                    exp_name = p.parent.parent.name
                    file_base = p.stem
                    event_id = '_'.join(file_base.split('_')[:2])
                    for i, tr in enumerate(st):
                        waveforms.append(tr.data)
                        trace_file_paths.append(full_path)
                        trace_metadata.append(f"Experiment: {exp_name}, Run: {run_num}, Trace: trace{i+1}")
                        trace_names.append(f'p_picks_{exp_name}_{run_num}_{event_id}_trace{i+1}')
                    picks_per_trace += [[None] * max_picks for _ in range(len(st))]
                except:
                    pass
        n = len(waveforms)
        csv_path = os.path.join(os.path.dirname(__file__), f'p_picks_{foldername}.csv')

    # Load previous picks if CSV exists
    if os.path.exists(csv_path):
        try:
            prev_df = pd.read_csv(csv_path)
            for _, row in prev_df.iterrows():
                name = row.get('Name', None)
                raw_val = row.get('marked_point', None)
                if name is None:
                    continue
                # Safely parse marked_point
                picks = []
                if isinstance(raw_val, str):
                    try:
                        parsed = ast.literal_eval(raw_val)
                        if isinstance(parsed, list):
                            picks = parsed
                        elif parsed is None:
                            picks = []
                        else:
                            picks = [parsed]
                    except:
                        picks = []
                elif pd.notna(raw_val):
                    # If it's a number directly
                    picks = [raw_val]
                else:
                    picks = []
                label_map[name] = picks
        except Exception as e:
            print(f"Error loading previous CSV: {e}")


        except Exception as e:
            print(f"Error loading previous CSV: {e}")

    # Apply existing picks where names match
    for i, name in enumerate(trace_names):
        if name in label_map:
            picks_list = label_map[name]
            for j, val in enumerate(picks_list):
                if j < max_picks:
                    picks_per_trace[i][j] = val


def redraw_plot():
    #Updates main waveform display
    global cursor_line
    waveform = waveforms[current_index]
    current_xlim = ax.get_xlim() if zoom_limits["xlim"] else (0, len(waveform))
    current_ylim = ax.get_ylim() if zoom_limits["ylim"] else (waveform.min(), waveform.max())
    ax.clear()
    ax.plot(waveform, label='Waveform')

    # Plot picks
    for i, pick in enumerate(picks_per_trace[current_index]):
        if pick is not None:
            color = colors[i % len(colors)]
            ax.axvline(pick, color=color, linestyle='-', label=f'Pick {i+1}')

    cursor_line = ax.axvline(0, color='black', linestyle='--', alpha=0.4)
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


def on_click(event):
    #plots x axis location that the user clicked
    if getattr(canvas.toolbar, 'mode', '') != '':
        return
    if event.inaxes and event.xdata is not None:
        if event.button == 1:
            picks_per_trace[current_index][selected_pick_slot] = int(event.xdata)
            redraw_plot()
        elif event.button == 3:
            tolerance = 15
            closest_index = None
            min_dist = float('inf')
            for i, pick in enumerate(picks_per_trace[current_index]):
                if pick is not None:
                    dist = abs(event.xdata - pick)
                    if dist < tolerance and dist < min_dist:
                        min_dist = dist
                        closest_index = i
            if closest_index is not None:
                picks_per_trace[current_index][closest_index] = None
                redraw_plot()


def on_mouse_move(event):
    #draws the dotted line
    if event.inaxes and event.xdata is not None:
        try:
            cursor_line.set_xdata([event.xdata])
            canvas.draw_idle()
        except:
            pass


def on_scroll(event):
    #zooms into the waveform
    if event.inaxes is None:
        return
    ax = event.inaxes
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    scale_x = 1.2 if event.button == 'up' else 0.8
    scale_y = 1.05 if event.button == 'up' else 0.95
    xdata = event.xdata
    ydata = event.ydata

    if ctrl_held and ydata is not None:
        ax.set_ylim([ydata + (y - ydata) * scale_y for y in ylim])
    elif xdata is not None:
        ax.set_xlim([xdata + (x - xdata) * scale_x for x in xlim])
    canvas.draw_idle()


def on_draw(event):
    zoom_limits["xlim"] = ax.get_xlim()
    zoom_limits["ylim"] = ax.get_ylim()


def save_labels_csv():
    data = []
    for i in range(n):
        picks = [p for p in picks_per_trace[i] if p is not None]
        row = {'Name': trace_names[i], 'marked_point': str(picks)}
        data.append(row)
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    messagebox.showinfo('Saved', f'Saved as {os.path.basename(csv_path)}')


def rollout_viewer():
    def load_new_rollout():
        new_path = filedialog.askopenfilename(title='Select a .mseed file for rollout')
        if not new_path:
            return
        try:
            st = read(new_path)
            traces = [tr.data for tr in st]
            ax_rollout.clear()
            min_val, max_val = np.min(traces[0]), np.max(traces[0])
            offset = (max_val - min_val) * 1.2
            for i, tr in enumerate(traces):
                ax_rollout.plot(tr + i * offset, label=f"Trace {i+1}")
            ax_rollout.set_title(f"Rollout: {os.path.basename(new_path)} (offset by range+20%)")
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
        min_val, max_val = np.min(traces[0]), np.max(traces[0])
        offset = (max_val - min_val) * 1.2
        for i, tr in enumerate(traces):
            ax_rollout.plot(tr + i * offset, label=f"Trace {i+1}")
        ax_rollout.set_title(f"Rollout: {os.path.basename(rollout_path)} (offset by range+20%)")
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
            messagebox.showwarning("Invalid index", f"Please enter a number between 1 and {n}")
    except ValueError:
        messagebox.showwarning("Invalid input", "Enter an integer.")


def reset_zoom():
    global zoom_limits
    zoom_limits = {"xlim": None, "ylim": None}
    redraw_plot()


def update_button_states():
    prev_btn.config(state=tk.DISABLED if current_index <= 0 else tk.NORMAL)
    next_btn.config(state=tk.DISABLED if current_index >= n - 1 else tk.NORMAL)


def on_close():
    root.destroy()
    sys.exit()


def on_resize(event):
    if waveforms:
        redraw_plot()


def on_ctrl_press(event):
    global ctrl_held
    ctrl_held = True


def on_ctrl_release(event):
    global ctrl_held
    ctrl_held = False


# --- UI ---
root = tk.Tk()
root.title("Waveform Labeling (Pick Slots + Resume CSV + Rollout + Delete Picks)")
root.geometry("1100x850")
root.protocol("WM_DELETE_WINDOW", on_close)
root.bind("<Configure>", on_resize)
root.bind_all("<Control_L>", on_ctrl_press)
root.bind_all("<KeyRelease-Control_L>", on_ctrl_release)

top_frame = tk.Frame(root)
top_frame.pack(fill='x', pady=10)

file_label = tk.Label(top_frame, text="", font=("Arial", 12), fg="blue")
file_label.pack()
metadata_label = tk.Label(top_frame, text="", font=("Arial", 11))
metadata_label.pack()

instruction = tk.Label(top_frame, text="Left-click: Set pick | Right-click: Delete pick | Scroll = Zoom X | Ctrl+Scroll = Zoom Y", font=("Arial", 13))
instruction.pack()

radio_frame = tk.Frame(root)
radio_frame.pack(pady=10)
pick_var = tk.IntVar(value=0)
for i in range(max_picks):
    rb = tk.Radiobutton(radio_frame, text=f"Pick {i+1}", variable=pick_var, value=i, command=lambda: set_pick_slot())
    rb.pack(side=tk.LEFT, padx=5)

def set_pick_slot():
    global selected_pick_slot
    selected_pick_slot = pick_var.get()

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
