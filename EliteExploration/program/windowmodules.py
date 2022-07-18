#(C) Alan Young 2022

from math import floor
from multiprocessing.connection import Connection
from tkinter import filedialog
from tkinter import *
from tkinter import ttk
from typing import List
from constants import *

class SystemWindow(ttk.Frame):
    def __init__(self, parent, systemobj):
        #setup base object
        super().__init__(parent, borderwidth=1, relief="groove")
        super().pack(fill="x",padx=1, pady=1)

        super().rowconfigure(0, weight=1)
        super().rowconfigure(1, weight=1)
        super().columnconfigure(0, weight=0)
        super().columnconfigure(1, weight=1)
        super().columnconfigure(2, weight=1)

        #active indicator
        ttk.Style().configure("ActiveInd.TFrame", background="green")
        ttk.Style().configure("InactiveInd.TFrame", background="lightyellow")
        activeindst = ""
        if systemobj["active"]: activeindst = "ActiveInd.TFrame"
        else: activeindst = "InactiveInd.TFrame"
        self.activeind = ttk.Frame(self, width=40, height=40, borderwidth=1, relief="sunken", style=activeindst)
        self.activeind.grid(row=0, column=0, rowspan=2, sticky="ns", padx=1, pady=1)

        #information
        self.system = ttk.Label(self, text=systemobj["system"], font=("Arial", 13));
        self.system.grid(row=0, column=1, columnspan=2, sticky="w")

        self.jumps = ttk.Label(self, text="{0} Jumps".format(systemobj["jumps"]), font=("Arial", 9));
        self.jumps.grid(row=1, column=1, sticky="wn", pady=2)

        self.bodies = ttk.Label(self, text="{0} Bodies".format(systemobj["bodies"]), font=("Arial", 9));
        self.bodies.grid(row=1, column=2, sticky="wn", pady=2)   

class BodyWindow(ttk.Frame):
    def __init__(self, parent, bodyobj):
        #setup base object
        super().__init__(parent, borderwidth=1, relief="groove", height=50)
        super().pack(fill="x",padx=1, pady=1)

        super().rowconfigure(0, weight=1)
        super().rowconfigure(1, weight=1)
        super().columnconfigure(0, weight=1)
        super().columnconfigure(1, weight=0)
        super().columnconfigure(2, weight=1)
        super().columnconfigure(3, weight=0)
        super().columnconfigure(4, weight=1)
        
        #indicators
        ttk.Style().configure("InactiveScan.TFrame", background="lightyellow")
        self.scanind = ttk.Frame(self, width=25, borderwidth=1, relief="sunken", style="InactiveScan.TFrame")
        self.scanind.grid(row=0, column=1, rowspan=2, sticky="ns", padx=1, pady=1)

        self.mapind = ttk.Frame(self, width=25, borderwidth=1, relief="sunken", style="InactiveScan.TFrame")
        self.mapind.grid(row=0, column=3, rowspan=2, sticky="ns", padx=1, pady=1)

        #information
        self.bodyadist = ttk.Label(self, text="{0} ➤ {1}".format(bodyobj["name"],bodyobj["distance"]), font=("Arial", 13))
        self.bodyadist.grid(row=0, column=0, sticky="w", pady=2, padx=2)

        self.jumps = ttk.Label(self, text="Scan Value: {0}".format(bodyobj["scanvalue"]), font=("Arial", 9))
        self.jumps.grid(row=0, column=2, sticky="w", pady=2)

        self.bodies = ttk.Label(self, text="Map Value: {0}".format(bodyobj["mapvalue"]), font=("Arial", 9))
        self.bodies.grid(row=0, column=4, sticky="w", pady=2)

    def setscancomplete(self, MapScanN):
        ttk.Style().configure("ActiveScan.TFrame", background="blue")
        if MapScanN: self.mapind.config(style="ActiveScan.TFrame")
        else: self.scanind.config(style="ActiveScan.TFrame")

class MainWindow:
    pipe: Connection

    root: Tk

    midframe: ttk.Frame
    systemlist: List[SystemWindow]
    bodylist: List[BodyWindow]
    r2rprogress: ttk.Progressbar

    infotext: StringVar

    def __init__(self, pipe: Connection):
        self.pipe = pipe

        self.root = Tk()
        self.root.title("Elite Dangerous R2R Helper")
        self.root.geometry('1200x600')

        #setup main window design
        self.root.rowconfigure(0, weight=0) #top row
        self.root.rowconfigure(1, weight=1) #main body
        self.root.rowconfigure(2, weight=0) #information panel
        self.root.columnconfigure(0, weight=1)

        #setup nav panel
        self.topframe = ttk.Frame(self.root)
        self.topframe.grid(row=0, column=0, sticky="nesw")

        #prepare main display
        self.midframe = ttk.Frame(self.root)
        self.midframe.grid(row=1, column=0, sticky="nesw")
        self.setupR2RView()

        #configure info panel
        ttk.Style().configure("infopane.TLabel", foreground="#8f8f8f", font=("times new roman", 8))
        self.lowframeheader = ttk.Label(text="Status", style="infopane.TLabel")
        self.lowframe = ttk.LabelFrame(self.root, padding=0, labelwidget=self.lowframeheader)
        self.lowframe.grid(row=2, column=0, sticky="nsew")

        self.lowframe.columnconfigure(0, weight=0)
        self.lowframe.columnconfigure(1, weight=1)

        self.infotext = StringVar(value="No file loaded")
        self.infolabel = ttk.Label(self.lowframe, textvariable=self.infotext)
        self.infolabel.grid(row=0, column=0, sticky="nsw")

        self.loadbutton = ttk.Button(self.lowframe, text="Load CSV", command=self.loadcsvbutton)
        self.loadbutton.grid(row=0, column=1, sticky="nes")

        self.integer = 0

    def setupR2RView(self):
        #setup panel style
        self.midframe.rowconfigure(0, weight=0)
        self.midframe.rowconfigure(1, weight=1)
        self.midframe.columnconfigure(0, weight=1)
        self.midframe.columnconfigure(1, weight=5)

        #create subpanels
        ttk.Style().configure("Subsections.TFrame", background="lightgray")

        self.r2rprogress = ttk.Progressbar(self.midframe)
        self.r2rprogress.grid(row=0, column=0, columnspan=2, sticky="nesw", padx=5, pady=2)

        self.r2rsystempane = ttk.Frame(self.midframe, style="Subsections.TFrame")
        self.r2rsystempane.grid(row=1, column=0, sticky="nesw", padx=2, pady=2)
        self.r2rsystempane.columnconfigure(0,weight=1)

        self.r2rbodypane = ttk.Frame(self.midframe, style="Subsections.TFrame")
        self.r2rbodypane.grid(row=1, column=1, sticky="nesw", padx=2, pady=2)
        self.r2rbodypane.columnconfigure(0,weight=1)

        #initialize lists
        self.systemlist = []
        self.bodylist = []

    def populatesystemspane(self, systems):
        #delete old
        for s in self.systemlist:
            s.destroy()
            del s
        self.systemlist = []

        #add new
        for system in systems:
            self.systemlist.append(SystemWindow(self.r2rsystempane, system))

    def populatebodiespane(self, bodies):
        #delete old
        for b in self.bodylist:
            b.destroy()
            del b
        self.bodylist = []

        #add new
        for body in bodies:
            self.bodylist.append(BodyWindow(self.r2rbodypane, body))

    def loadcsvbutton(self):
        filepath = filedialog.askopenfilename(initialdir=(USER_PATH+SEARCH_PATH), title="Select Exploration File", filetypes=(("CSV Files","*.csv"),("all files","*.*")))
        if filepath != "":
            self.pipe.send({"type":"loadcsv","data":filepath})

    def update(self):
        CCOUNT_MAX = 100
        ccount = 0
        while self.pipe.poll() and (ccount < CCOUNT_MAX):
            ccount += 1
            command = self.pipe.recv()

            #load new route data
            if(command["type"] == "setsystems"):
                self.r2rprogress["value"] = floor(((command["progress"][0] + 1)/max(command["progress"][1], 1))*100) #-2 to compensate for non index at 0
                self.populatesystemspane(command["systems"])
                self.populatebodiespane(command["bodies"])
                
            #set planets scanned/mapped
            if(command["type"] == "scanbody"):
                self.bodylist[command["index"]].setscancomplete(False)
            if(command["type"] == "mapbody"):
                self.bodylist[command["index"]].setscancomplete(True)

            #set state machine status message
            if(command["type"] == "setstatus"):
                self.infotext.set(command["data"])

            #copy data to clipboard
            if command["type"] == "forcecopy" and EN_COPY_TO_CLIPBOARD:
                self.root.clipboard_clear()
                self.root.clipboard_append(command["data"])
        
        self.root.after(10, self.update) #update again in 10 ms

    def mainloop(self):
        
        self.root.after(10, self.update)
        self.root.mainloop()