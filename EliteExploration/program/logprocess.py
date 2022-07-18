#(C) Alan Young 2022

import json
from multiprocessing.connection import Connection
import os
from time import sleep
from constants import *

def createLogPath(lognumber, partnumber):
    filename = "/Journal.{0}.{1:02}.log".format(lognumber, partnumber)
    return USER_PATH + LOGS_PATH + filename

def logfileRead(lognumber, partnumber, pipe: Connection):
    nextpartnumber = 0
    logfile = open(createLogPath(lognumber, partnumber), "r")

    if not logfile.closed:
        #load data until break condition
        while(1): 
            #process incoming commands
            if pipe.poll():
                command = pipe.recv()
                if command["type"] == "close":
                    break

            #read data
            line = logfile.readline().strip()

            #packet is available
            if(len(line) > 0):
                packet = json.loads(line)

                #process internally managed packets
                if packet["event"] == "Continued":
                    nextpartnumber = int(packet.Part)
                    break
                if packet["event"] == "Shutdown":
                    break

                #send packet if applicable
                pipe.send(packet)

            sleep(.001) #delay during loop (TODO: clear queues before loop)

        logfile.close()

    return nextpartnumber
                
def logfileProcess(pipe: Connection):
    #detect file
    currentlognumber = "0"
    for logfile in os.listdir(USER_PATH + LOGS_PATH):
        if logfile.endswith(".log"):
            lognumber = logfile.split(".")[1]
            if(int(lognumber) > int(currentlognumber)): currentlognumber = lognumber

    #process file
    partnumber = 1
    while(1):
        print("Loading Logfile: " + createLogPath(currentlognumber, partnumber))
        partnumber = logfileRead(currentlognumber, partnumber, pipe)

        #exit if no new logfile is available
        if partnumber == 0:
            break

