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

try:
    current_index = len(pd.read_csv('marked_positions.csv'))
except:
    current_index = 0

def on_click(event):
    global labels
    if event.inaxes and event.xdata is not None:
        ix = int(event.xdata)
        labels[current_index] = ix
        redraw_plot()

def redraw_plot():
    ax.clear()
    ax.plot(waveforms[current_index])
    if labels[current_index] != -1:
        ax.axvline(labels[current_index], color='red', linestyle='--')
    ax.set_title(F"Waveform {current_index+1}/{n+1}")
    canvas.draw()
    update_button_states()

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

def save_labels_csv():
    marked_positions = pd.DataFrame({
        'waveform_index': np.arange(len(labels)),
        'marked_point': labels
    })
    marked_positions.to_csv('marked_positions.csv', index=False)


def update_button_states():
    if current_index <= 0:
        prev_btn.config(state=tk.DISABLED)
    else:
        prev_btn.config(state=tk.NORMAL)
    
    if current_index >= n-1:
        next_btn.config(state=tk.DISABLED)
    else:
        next_btn.config(state=tk.NORMAL)

root = tk.Tk()

#instructions at the top
root.title('Waveform Labeling')
top_frame = tk.Frame(root)
top_frame.pack(pady=10)
instruction_text = "Click on the waveform to mark a point of interest.\nUse Next/Previous to navigate. Save to export labels."
tk.Label(top_frame, text=instruction_text, justify=tk.LEFT, font=("Arial", 10)).pack(side=tk.LEFT)

#links matplotlib plot to tkinter
fig,ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.mpl_connect('button_press_event', on_click)
canvas.get_tk_widget().pack()
controls = tk.Frame(root)
controls.pack()

#screen controls
prev_btn = tk.Button(controls, text="Previous", command=prev_waveform)
prev_btn.pack(side=tk.LEFT, padx=5)

next_btn = tk.Button(controls, text="Next", command=next_waveform)
next_btn.pack(side=tk.LEFT, padx=5)

save_btn = tk.Button(controls, text="Save", command=save_labels_csv)
save_btn.pack(side=tk.LEFT, padx=5)


#main loop
redraw_plot()
update_button_states()
root.mainloop()