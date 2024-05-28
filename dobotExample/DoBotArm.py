#!/usr/bin/env python

import sys
import os
from ctypes import CDLL, RTLD_GLOBAL

# Add the path to the DLL folder
dll_path = os.path.join(os.path.dirname(__file__), '..', 'DobotDll_win')
sys.path.insert(1, dll_path)
import DobotDllType as dType

"""-------The DoBot Control Class-------
Variables:
suction = Suction is currently on/off
picking: shows if the dobot is currently picking or dropping an item
api = variable for accessing the dobot .dll functions
home% = home position for %
                                  """

CON_STR = {
    dType.DobotConnect.DobotConnect_NoError:  "DobotConnect_NoError",
    dType.DobotConnect.DobotConnect_NotFound: "DobotConnect_NotFound",
    dType.DobotConnect.DobotConnect_Occupied: "DobotConnect_Occupied"
}

# Main control class for the DoBot Magician.
class DoBotArm:
    def __init__(self, homeX, homeY, homeZ):
        self.suction = False
        self.picking = False
        self.api = None
        self.homeX = homeX
        self.homeY = homeY
        self.homeZ = homeZ
        self.connected = False
        self.load_dobot_dll()
        self.dobotConnect()

    def load_dobot_dll(self):
        try:
            # Path to the macOS .dylib file
            library_path = os.path.join(os.path.dirname(__file__), '..', 'DobotDll_win', 'DobotDll.dll')
            print(f"Attempting to load library from: {library_path}")  # Debug print
            self.api = CDLL(library_path, RTLD_GLOBAL)
        except OSError as e:
            print(f"Failed to load Dobot DLL: {e}")
            self.api = None

    def __del__(self):
        if self.api:
            self.dobotDisconnect()

    # Attempts to connect to the dobot
    def dobotConnect(self):
        if self.api is None:
            print("API not initialized, cannot connect to Dobot.")
            return False
        if self.connected:
            print("You're already connected")
        else:
            state = dType.ConnectDobot(self.api, "", 115200)[0]
            if state == dType.DobotConnect.DobotConnect_NoError:
                print("Connect status:", CON_STR[state])
                dType.SetQueuedCmdClear(self.api)

                dType.SetHOMEParams(self.api, self.homeX, self.homeY, self.homeZ, 0, isQueued=1)
                dType.SetPTPJointParams(self.api, 200, 200, 200, 200, 200, 200, 200, 200, isQueued=1)
                dType.SetPTPCommonParams(self.api, 100, 100, isQueued=1)

                dType.SetHOMECmd(self.api, temp=0, isQueued=1)
                self.connected = True
                return self.connected
            else:
                print("Unable to connect")
                print("Connect status:", CON_STR[state])
                return self.connected

    # Returns to home location and then disconnects
    def dobotDisconnect(self):
        if self.api:
            self.moveHome()
            dType.DisconnectDobot(self.api)

    # Delays commands
    def commandDelay(self, lastIndex):
        if self.api:
            dType.SetQueuedCmdStartExec(self.api)
            while lastIndex > dType.GetQueuedCmdCurrentIndex(self.api)[0]:
                dType.dSleep(200)
            dType.SetQueuedCmdStopExec(self.api)

    # Toggles suction peripheral on/off
    def toggleSuction(self):
        if self.api:
            lastIndex = 0
            if self.suction:
                lastIndex = dType.SetEndEffectorSuctionCup(self.api, True, False, isQueued=0)[0]
                self.suction = False
            else:
                lastIndex = dType.SetEndEffectorSuctionCup(self.api, True, True, isQueued=0)[0]
                self.suction = True
            self.commandDelay(lastIndex)

    # Moves arm to X/Y/Z Location
    def moveArmXY(self, x, y):
        if self.api:
            lastIndex = dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVLXYZMode, x, y, self.homeZ, 0)[0]
            self.commandDelay(lastIndex)

    def moveArmXYZ(self, x, y, z):
        if self.api:
            lastIndex = dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVLXYZMode, x, y, z, 0)[0]
            self.commandDelay(lastIndex)

    # Returns to home location
    def moveHome(self):
        if self.api:
            lastIndex = dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVLXYZMode, self.homeX, self.homeY, self.homeZ, 0)[0]
            self.commandDelay(lastIndex)

    # Toggles between hover and item level
    def pickToggle(self, itemHeight):
        if self.api:
            lastIndex = 0
            positions = dType.GetPose(self.api)
            if self.picking:
                lastIndex = dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVLXYZMode, positions[0], positions[1], self.homeZ, 0)[0]
                self.picking = False
            else:
                lastIndex = dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVLXYZMode, positions[0], positions[1], itemHeight, 0)[0]
                self.picking = True
            self.commandDelay(lastIndex)
