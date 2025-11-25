import tkinter
root = tkinter.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.protocol("WM_DELETE_WINDOW", lambda: None)    #disable close button
root.bind("<Escape>", lambda e: root.destroy())
root.mainloop()
