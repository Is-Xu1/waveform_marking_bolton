import numpy as np
import pandas as pd
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

#waveforms = pd.read_csv('waveforms.csv')
#n = len(waveforms)
n = 100
waveforms = np.random.randn(n,n)
labels = np.full(n, -1)

#tries to open output file marked_positions.csv, if it doesn't open it creates a 
#1D numpy array filled with -1
try:
    labels = pd.read_csv('marked_positions.csv')
except:
    labels = np.full(n, -1)

#tries to open output file marked_positions.csv, if it is successful it will set the current index to the first unmarked waveform
#defaults to index 0 
try:
    marked_positions = pd.read_csv('marked_positions.csv')
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
    global cursor_line, marker_set
    ax.clear()
    ax.plot(waveforms[current_index])

    if labels[current_index] != -1:
        ax.axvline(labels[current_index], color='red', linestyle='-')
        cursor_line = ax.axvline(0, color='red', linestyle='--', alpha=0.4)
    else:
        # Create a faint red line at x=0 to start, store reference
        cursor_line = ax.axvline(0, color='red', linestyle='--', alpha=0.4)

    ax.set_title(f"Waveform {current_index+1}/{n}")
    canvas.draw()
    update_button_states()


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
    marked_positions.to_csv('marked_positions.csv', index=False)

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

def on_mouse_move(event):
    global cursor_line
    if event.inaxes and event.xdata is not None:
        try:
            cursor_line.set_xdata([event.xdata])  # Pass as list or 1D array
            canvas.draw_idle()
        except Exception as e:
            print("Error updating cursor line:", e)


# Make the root window resizable
root = tk.Tk()
root.title('Waveform Labeling')
root.geometry("1000x800")  # Optional starting size
root.minsize(1000,800)    # Optional minimum size

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



#main loop
redraw_plot()
update_button_states()
root.mainloop()