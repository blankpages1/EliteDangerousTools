#(C) Alan Young 2022

from multiprocessing.connection import Connection
from windowmodules import *
from constants import *

def windowProcess(pipe: Connection):
    #run window
    window = MainWindow(pipe)
    window.mainloop()

    #close program
    pipe.send({"type":"close"})