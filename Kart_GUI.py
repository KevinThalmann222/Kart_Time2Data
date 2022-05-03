# py 3.9 -m pip install

import tkinter as tk
from PIL import Image, ImageTk
from tkinter.filedialog import askopenfile 
import Karttime2Data 

root = tk.Tk()
root["bg"] = "white"
root.title('Karttimes2Data')

canvas =  tk.Canvas(root, width=500, height=200, bg='white', highlightthickness=0)
canvas.grid(columnspan=3, rowspan=3)

# LOGO 
logo = Image.open('Kartlogo2.jpg')
logo = ImageTk.PhotoImage(logo)
logo_label = tk.Label(image=logo)
logo_label.image = logo 
logo_label.grid(column=1, row=0)

instructions = tk.Label(root, text='Select a Picture of your Karttimes', font='Raleway', bg='white')
instructions.grid(columnspan=3, column=0, row=1)

class GUI:

    def _colors(self, r,g,b):
        return f'#{r:02x}{g:02x}{b:02x}'

    def open_file(self):
        browse_text.set('loading ...')
        file = askopenfile(parent=root, mode='rb', title="choose your picture")

        self.kartzeiten = Karttime2Data.Kartzeiten(file.name)
        self.kartzeiten.kart_change_analyse()
        laps = self.kartzeiten.show_laps()
        fastlap = self.kartzeiten.show_fasted_lap()

        if file.name:
            
            text_box =  tk.Text(root, height=20, width=50,  padx=15, pady=15, bg='white')
            
            for lap in reversed(laps):
                text_box.insert(1.0, lap)
                text_box.insert(1.0, '\n')
                text_box.tag_configure('left', justify='left', background='white')
                text_box.tag_add('left', 1.0, 'end')
                text_box.grid(column=1, row=3)

            if fastlap:
                text_box.insert(1.0, fastlap) 

            browse_text.set('Browse')
            

    def excel_export(self):
        excel_text.set('exporting ...')
        self.kartzeiten.export2csv()
        excel_text.set('Export Successfully')
        

    def show_diagramm(self):
        diagramm_text.set('loading ...')
        self.kartzeiten.plot_laps()
        diagramm_text.set('Show Diagramm')

if __name__ == '__main__':

    gui = GUI()
    # browser button
    browse_text = tk.StringVar()
    browse_btn = tk.Button(root, textvariable=browse_text, command=lambda:gui.open_file(), font="Raleway", bg=gui._colors(32,122,41), fg='white', height=2, width=20)
    browse_text.set('Browse')
    browse_btn.grid(column=1, row=2)

    canvas =  tk.Canvas(root, width=500, height=400, bg='white', highlightthickness=0)
    canvas.grid(columnspan=3, rowspan=6) 

    #excel button
    excel_text = tk.StringVar()
    excel_text.set('Export2Excel')
    excel_btn = tk.Button(root, textvariable=excel_text, command=lambda:gui.excel_export(), font="Raleway", bg=gui._colors(32,122,41), fg='white', height=2, width=20)
    excel_btn.grid(column=1, row=8)

    #diagramm button
    diagramm_text = tk.StringVar()
    diagramm_text.set('Show Diagramm')
    diagramm_btn = tk.Button(root, textvariable=diagramm_text, command=lambda:gui.show_diagramm(), font="Raleway", bg=gui._colors(32,122,41), fg='white', height=2, width=20)
    diagramm_btn.grid(column=1, row=9)

    root.mainloop()