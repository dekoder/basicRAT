#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import win32api, win32con
import win32ui
import threading
import time
import os,sys

def btnClose():
    time.sleep(20)
    try:
        hd = win32ui.FindWindow(None, "scan")
        hd.SendMessage(win32con.WM_CLOSE)
    except:
        pass
    win32api.MessageBox(0, "The scan is complete, no virus was not found",  "scan", win32con.MB_OK) #u"扫描完成，未发现病毒！"

def pop():
    thread = threading.Thread(target=btnClose)
    thread.start()

    win32api.MessageBox(0, u"Background scanning...", "scan", win32con.MB_OK)

    thread.join()



