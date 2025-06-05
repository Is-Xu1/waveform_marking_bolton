import numpy as np
import pandas as pd
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox 
import h5py
import sys

# Make the root window resizable
root = tk.Tk()
root.title('Waveform Labeling')
root.geometry("1000x800")  # Optional starting size
root.minsize(1000,800)    # Optional minimum size


#initial file upload prompt, unless a file is uploaded, the rest of the code won't run properly
filename = filedialog.askopenfilename(
    title='Open waveform file',
    filetypes=(('All supported', '*.csv *.hdf5 *.h5'),
               ('CSV files', '*.csv'),
               ('HDF5 files', '*.hdf5 *.hf'),
               ('All files', '*.*'))
)
if filename:
    print(f'File selected: {filename}')
if filename.endswith('.csv'):
    try:
        waveforms = pd.read_csv(filename).to_numpy()
        n = len(waveforms)
        sampling_rate = 100
        component_order = ['Channel']
    except:
        messagebox.showerror('Error', 'Failed to open .csv {filename}')
elif filename.endswith('.hdf5') or filename.endswith('.hdf'):
    try:
        with h5py.File(filename) as file:
            dataset = file['data/bucket0']
            waveforms = dataset[:,0,:]
            sampling_rate = file['data_format/sampling_rate'][()]
            component_order = file['data_format/component_order'][()]
            n = waveforms.shape[0]
    except:
        messagebox.showerror('Error', 'Failed to open .hdf5 {filename}')
else:
    messagebox.showwarning('No file selected or unsupported file format')
    root.destroy()
    exit()

#test code
'''n = 100
waveforms = np.random.randn(n,n)
labels = np.full(n, -1)'''

#tries to open output file marked_positions.csv, if it doesn't open it creates a 
#1D numpy array filled with -1
try:
    labels = pd.read_csv(f'{filename}_marked.csv')
except:
    labels = np.full(n, -1)

#tries to open output file marked_positions.csv, if it is successful it will set the current index to the first unmarked waveform
#defaults to index 0 
try:
    marked_positions = pd.read_csv(f'{filename}_marked.csv')
    labels = marked_positions['marked_point'].to_numpy()
    unlabeled = marked_positions[marked_positions['marked_point'] == -1]
    current_index = unlabeled.index[0]
except:
    current_index = 0

#onclick event function, checks if the click is on the axis 
def on_click(event):
    global labels
    if event.inaxes and event.xdata is not None:
        ix = int(event.xdata)
        labels[current_index] = ix
        marker_set = True
        redraw_plot()

#redraw plot function, if at the index the position has been marked already, draws the mark
def redraw_plot():
    global cursor_line
    ax.clear()
    ax.plot(waveforms[current_index])

    if labels[current_index] != -1:
        ax.axvline(labels[current_index], color='red', linestyle='-')
        cursor_line = ax.axvline(labels[current_index], color='red', linestyle='--', alpha=0.4)
    else:
        # Create a faint red line at x=0 to start, store reference
        cursor_line = ax.axvline(0, color='red', linestyle='--', alpha=0.4)

    ax.set_title(f"Waveform {current_index+1}/{n}")
    canvas.draw()
    update_button_states()

def uploadfile():
    global labels, current_index
    filename = filedialog.askopenfilename(
        title='Open waveform file',
        filetypes=(('All supported', '*.csv *.hdf5 *.h5'),
                ('CSV files', '*.csv'),
                ('HDF5 files', '*.hdf5 *.hf'),
                ('All files', '*.*'))
    )
    if filename:
        print(f'File selected: {filename}')
    if filename.endswith('.csv'):
        try:
            waveforms = pd.read_csv(filename).to_numpy()
            n = len(waveforms)
            sampling_rate = 100
            component_order = ['Channel']
        except:
            messagebox.showerror('Error', 'Failed to open .csv {filename}')
    elif filename.endswith('.hdf5') or filename.endswith('.hdf'):
        try:
            with h5py.File(filename) as file:
                dataset = file['data/bucket0']
                waveforms = dataset[:,0,:]
                sampling_rate = file['data_format/sampling_rate'][()]
                component_order = file['data_format/component_order'][()]
                n = waveforms.shape[0] 
        except:
            messagebox.showerror('Error', 'Failed to open .hdf5 {filename}')
    else:
        messagebox.showwarning('Error', 'No file selected or unsupported file format')
    try:
        labels = pd.read_csv(f'{filename}_marked.csv')
    except:
        labels = np.full(n, -1)
    try:
        marked_positions = pd.read_csv(f'{filename}_marked.csv')
        labels = marked_positions['marked_point'].to_numpy()
        unlabeled = marked_positions[marked_positions['marked_point'] == -1]
        current_index = unlabeled.index[0]
        redraw_plot()
    except:
        current_index = 0

#functions for navigating waveforms
def prev_waveform():
    global current_index
    if current_index > 0:
        current_index -=1
        redraw_plot()
def next_waveform():
    global current_index
    if current_index < n-1:
        current_index += 1
        redraw_plot()

#function for saving the labels to a csv file
def save_labels_csv():
    marked_positions = pd.DataFrame({
        'marked_point': labels
    })
    marked_positions.to_csv(f'{filename}_marked.csv', index=False)

#updates the function os that if the index is at 0 or n, blanks out the buttons
def update_button_states():
    if current_index <= 0:
        prev_btn.config(state=tk.DISABLED)
    else:
        prev_btn.config(state=tk.NORMAL)
    
    if current_index >= n-1:
        next_btn.config(state=tk.DISABLED)
    else:
        next_btn.config(state=tk.NORMAL)

#draws a dotted red line so that user knows where approximate mark will be
def on_mouse_move(event):
    global cursor_line
    if event.inaxes and event.xdata is not None:
        try:
            cursor_line.set_xdata([event.xdata])  # Pass as list or 1D array
            canvas.draw_idle()
        except Exception as e:
            print("Error updating cursor line:", e)


def on_close():
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW", on_close)

# Instructions frame (static height)
top_frame = tk.Frame(root)
top_frame.pack(fill='x', pady=10)

instruction_text = "Click on the waveform to mark a point of interest.\nUse Next/Previous to navigate. Save to export labels."
instruction_label = tk.Label(
    top_frame,
    text=instruction_text,
    justify='center',
    font=("Arial", 15),
    anchor='center'
)
instruction_label.pack(anchor='center')

# Dynamic plot canvas
fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill='both', expand=True)  # <-- Makes it scale
canvas.mpl_connect('button_press_event', on_click)
canvas.mpl_connect('motion_notify_event', on_mouse_move)


# Controls (fixed height, but stretch horizontally)
controls = tk.Frame(root)
controls.pack(fill='x', pady=10)

prev_btn = tk.Button(controls, text="Previous", command=prev_waveform, width=12, height=2, font=("Arial", 10))
prev_btn.pack(side=tk.LEFT, padx=5, pady=5)

next_btn = tk.Button(controls, text="Next", command=next_waveform, width=12, height=2, font=("Arial", 10))
next_btn.pack(side=tk.LEFT, padx=5, pady=5)

save_btn = tk.Button(controls, text="Save", command=save_labels_csv, width=12, height=2, font=("Arial", 10))
save_btn.pack(side=tk.LEFT, padx=5, pady=5)

file_btn = tk.Button(controls, text="Import File", command=uploadfile, width=12, height=2, font=("Arial", 10))
file_btn.pack(side=tk.LEFT, padx=5, pady=5)


#main loop
redraw_plot()
update_button_states()
root.mainloop()