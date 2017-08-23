import os, sys
import socket
import threading

import win32con
import win32console
import win32gui

from incidents import app

HOST = "localhost"
PORT = 5010

def run_browser():
    os.startfile("http://%s:%d" % (HOST, PORT))

if __name__ == '__main__':
    import threading
    threading.Timer(3.0, run_browser).start()
    #
    # If there's no instance of this app currently running, start it up
    #
    hWnd = win32console.GetConsoleWindow()
    win32gui.ShowWindow(hWnd, win32con.SW_MINIMIZE)
    try:
        socket.socket().connect((HOST, PORT))
    except socket.error:
        app.run(host=HOST, port=PORT, debug=False)
