#(C) Alan Young 2022

from multiprocessing import Process
from multiprocessing import Pipe
from multiprocessing.connection import Connection
import string
from time import sleep

import psutil
import tkinter.messagebox
from logprocess import logfileProcess
from windowprocess import windowProcess
from constants import *

class ProgramState:
    __DISPLAY_LENGTH = 10

    def __init__(self):
        self.systemslist = []
        self.currentsystem = ""
        self.systemoffset = 0
        self.newsystem = True

    def loadRoute(self, filelocation):
        print("Loading route file " + filelocation)
        tempsystemslist = []

        try:
            with open(filelocation,"r") as csvfile:
                csvfile.readline() #remove leading header line
                
                #load each line   
                line = "" 
                lastsystem = ""
                lastindex = -1
                while(len(line := csvfile.readline().strip()) > 0):
                    sections = line.replace("\"","").split(",") #remove extra quotation marks
                    
                    #basic checks
                    if len(sections) != 8: return False

                    #load
                    system = sections[0]
                    body = sections[1]
                    distance = sections[4]
                    scanvalue = sections[5]
                    mapvalue = sections[6]
                    jumps = sections[7]

                    #add new system if nessesary
                    if system != lastsystem:
                        lastindex = lastindex + 1
                        lastsystem = system
                        tempsystemslist.append({"system":system,"jumps":jumps,"bodies":[]})
                    
                    #add body to system
                    tempsystemslist[lastindex]["bodies"].append({"name":body,"distance":distance,"scanvalue":scanvalue,"mapvalue":mapvalue, "scan":False, "map":False})
        
        except:
            return False

        print("Loaded route file " + filelocation)
        self.systemslist = tempsystemslist
        self.systemoffset = 0
        self.newsystem = True
        return True

    def updatecurrentsystem(self, newsystem: string):
        self.currentsystem = newsystem #always update system name
        
        newindex = -1
        for index in range(len(self.systemslist)):
            if self.currentsystem == self.systemslist[index]["system"]:
                newindex = index
                break
        if newindex > 0:
            self.systemoffset = newindex
            self.newsystem = True

    def __findbody(self, body):
        index = -1
        if len(self.systemslist) > 0:
            for i in range(len(self.systemslist[self.systemoffset]["bodies"])):
                if self.systemslist[self.systemoffset]["bodies"][i]["name"] == body:
                    index = i
                    
        return index

    def updatebody(self, body, mapped):     
        #search for body
        index = self.__findbody(body)
        if index > -1:
            if mapped: self.systemslist[self.systemoffset]["bodies"][index]["map"] = True
            else: self.systemslist[self.systemoffset]["bodies"][index]["scan"] = True

    #ui commands
    def uisendsystemdata(self, pipe: Connection):
        if self.newsystem:
            self.newsystem = False

            systems = []
            bodies = []

            if len(self.systemslist) > 0:
                bodies = self.systemslist[self.systemoffset]["bodies"]
            for index in range(self.systemoffset, min(self.systemoffset + self.__DISPLAY_LENGTH, len(self.systemslist))):
                tmpsys = self.systemslist[index]
                systems.append({"system": tmpsys["system"],"jumps":tmpsys["jumps"],"bodies":len(tmpsys["bodies"]),"active":(index == self.systemoffset)} )

            pipe.send({"type":"setsystems","systems":systems,"bodies":bodies,"progress":(self.systemoffset, len(self.systemslist))})
   

    def uisendscandata(self, pipe: Connection, body, mapping):
        index = self.__findbody(body)
        if index > -1:
            if mapping: pipe.send({"type":"mapbody", "index":index})
            else:  pipe.send({"type":"scanbody", "index":index})

        #force copy next destination TODO
    
    def uisendcopy(self, pipe: Connection, nextsystem = False):
        target = self.systemoffset
        if nextsystem: target += 1
        if (target) < len(self.systemslist):
            pipe.send({"type":"forcecopy","data":self.systemslist[target]["system"]})

    def uisendstatus(self, pipe: Connection, string: string):
        pipe.send({"type":"setstatus", "data":string})

def startprogram():

    #start logfile process
    [logfilepipe1, logfilepipe2] = Pipe(duplex=True)
    logfile = Process(target=logfileProcess, args=(logfilepipe2,))
    logfile.daemon = True
    logfile.start()

    #start window process
    [windowpipe1, windowpipe2] = Pipe(duplex=True)
    window = Process(target=windowProcess, args=(windowpipe2,))
    window.daemon = True
    window.start()

    state = ProgramState()

    #run internal state machine
    runloop = True
    while(runloop):
        #process logfile string
        if logfilepipe1.poll():
            logentry = logfilepipe1.recv()

            #system location events
            if(logentry["event"] == "Location" or logentry["event"] == "FSDJump"): 
                state.updatecurrentsystem(logentry["StarSystem"])
                state.uisendsystemdata(windowpipe1)
                state.uisendstatus(windowpipe1, "Entered system {0}".format(logentry["StarSystem"]))
                state.uisendcopy(windowpipe1, True)

            #scan events
            if(logentry["event"] == "Scan"): #normal scan
                if(logentry["ScanType"] == "Detailed" or logentry["ScanType"] == "AutoScan"): 
                    state.updatebody(logentry["BodyName"], False)
                    state.uisendscandata(windowpipe1, logentry["BodyName"], False)
                    state.uisendstatus(windowpipe1, "Scanned body {0}".format(logentry["BodyName"]))
            if(logentry["event"] == "SAAScanComplete"):
                state.updatebody(logentry["BodyName"], True)
                state.uisendscandata(windowpipe1, logentry["BodyName"], True)
                state.uisendstatus(windowpipe1, "Scanned body {0}".format(logentry["BodyName"]))

        #process window string
        if windowpipe1.poll():
            windowcommand = windowpipe1.recv()

            #handle server loadcsv request
            if windowcommand["type"] == "loadcsv":
                if state.loadRoute(windowcommand["data"]): 
                    state.updatecurrentsystem(state.currentsystem)
                    state.uisendsystemdata(windowpipe1)
                    state.uisendstatus(windowpipe1, "Loaded new route file")
                    state.uisendcopy(windowpipe1)
                else:
                    tkinter.messagebox.showerror(title="Error", message="Failed to load route file")
            
            #handle exit command
            if windowcommand["type"] == "close":
                runloop = False

        sleep(.001) #delay during loop (TODO: clear queues before loop)

    #close all child processes
    logfilepipe1.send({"type":"close", "data":None})
    logfile.join()
    windowpipe1.send({"type":"close", "data":None})
    window.join()

def main():
    
    #find process id
    active = 0
    for i in psutil.process_iter():
        if i.name() == "EliteDangerous64.exe":
            active = i.pid

    #start program
    if(active != 0):
        print("Elite Dangerous open - loading program")
        startprogram()
    else:
        tkinter.messagebox.showerror(title="Error", message="Elite Dangerous not open - exiting program")

if __name__ == '__main__':
    main()