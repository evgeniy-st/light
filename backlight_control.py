#!/usr/bin/python3
import subprocess
import dbus
import os
from threading import Timer

IMAGE_PATH = '/home/stea/temp/cam.jpg'
BRIGHTNESS = [50]
UPDATE_BRIGHTNESS_TIMEOUT = 3
UPDATE_DISPLAY_TIMEOUT = 5
UPDATE_KBD_TIMEOUT = 0.5
MAX_USER_IDLE = 30000


def createImageFswebcam(path):
    command = ['/usr/bin/fswebcam -q -r 1280x720 -D 1 --no-banner ' + path]
    subprocess.call(command, shell=True)


def calcAVGColor(path):
    command = ['/usr/bin/convert ' + path + ' -colorspace GRAY -resize 1x1 txt:']
    s = subprocess.check_output(command, shell=True)
    s = s.decode('utf-8').split('\n')[1]
    s = s[s.find('gray(')+5:-1]
    value = int(s) // 2.55
    return value


def deleteImage(path):
    os.remove(path)


def updateBrightness():
    if len(BRIGHTNESS) >= 5:
        BRIGHTNESS.pop(0)
    createImageFswebcam(IMAGE_PATH)
    avg = calcAVGColor(IMAGE_PATH)
    deleteImage(IMAGE_PATH)
    BRIGHTNESS.append(avg)
    Timer(UPDATE_BRIGHTNESS_TIMEOUT, updateBrightness).start()


def getBrightnessValue():
    current_brightness = int(round(sum(BRIGHTNESS)/len(BRIGHTNESS), 0))
    return current_brightness


def setKbdBacklight(value):
    bus = dbus.SystemBus()
    obj = bus.get_object('org.freedesktop.UPower',
                         '/org/freedesktop/UPower/KbdBacklight')
    interface = dbus.Interface(obj,
                               dbus_interface='org.freedesktop.UPower.KbdBacklight')
    if value in [0, 1, 2, 3]:
        interface.SetBrightness(dbus.Int32(value))


def getKbdBacklight():
    bus = dbus.SystemBus()
    obj = bus.get_object('org.freedesktop.UPower',
                         '/org/freedesktop/UPower/KbdBacklight')
    interface = dbus.Interface(obj,
                               dbus_interface='org.freedesktop.UPower.KbdBacklight')
    result = int(interface.GetBrightness())
    return result


def getPowerSaveStatus():
    bus = dbus.SessionBus()
    obj = bus.get_object('org.freedesktop.ScreenSaver',
                         '/org/freedesktop/ScreenSaver')
    interface = dbus.Interface(obj,
                               dbus_interface='org.freedesktop.ScreenSaver')
    result = int(interface.GetSessionIdleTime())
    return result


def updateKbd():
    idle = getPowerSaveStatus()
    if idle < MAX_USER_IDLE:
        brightness = int(round(getBrightnessValue()/12, 0))
        if brightness <= 3:
            if brightness == 0:
                brightness = 1
            if getKbdBacklight() != brightness:
                setKbdBacklight(brightness)
        else:
            if getKbdBacklight() != brightness:
                setKbdBacklight(0)
    else:
        setKbdBacklight(0)
    Timer(UPDATE_KBD_TIMEOUT, updateKbd).start()


def setDisplayBacklight(value):
    bus = dbus.SessionBus()
    obj = bus.get_object('org.kde.Solid.PowerManagement',
                         '/org/kde/Solid/PowerManagement/Actions/BrightnessControl')
    interface = dbus.Interface(obj, dbus_interface='org.kde.Solid.PowerManagement.Actions.BrightnessControl')
    interface.setBrightness(dbus.Int32(value))


def getDisplayBacklight():
    bus = dbus.SessionBus()
    obj = bus.get_object('org.kde.Solid.PowerManagement',
                         '/org/kde/Solid/PowerManagement/Actions/BrightnessControl')
    interface = dbus.Interface(obj, dbus_interface='org.kde.Solid.PowerManagement.Actions.BrightnessControl')
    result = int(interface.brightness())
    return result


def updateDisplay():
    value = getBrightnessValue()
    if value <= 90:
        value += 10
    brightness = round(value, -1)
    if getDisplayBacklight() != brightness:
        setDisplayBacklight(brightness)
    Timer(UPDATE_DISPLAY_TIMEOUT, updateDisplay).start()

if __name__ == '__main__':
    updateBrightness()
    updateKbd()
    updateDisplay()
