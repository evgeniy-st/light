#!/usr/bin/python3
import subprocess
import dbus
import os
from time import sleep
from threading import Timer

IMAGE_PATH = '/home/stea/temp/cam.jpg'
BRIGHTNESS = [50, 50]
UPDATE_BRIGHTNESS_TIMEOUT = 3
UPDATE_DISPLAY_TIMEOUT = 5
UPDATE_KBD_TIMEOUT = 0.5
IDLE_KBD_TIMEOUT = 60000


def create_image_fswebcam(path):
    command = ['/usr/bin/fswebcam -q -r 1280x720 -D 1 --no-banner ' + path]
    subprocess.call(command, shell=True)


def calc_avgcolor(path):
    command = ['/usr/bin/convert ' + path + ' -colorspace GRAY -resize 1x1 txt:']
    s = subprocess.check_output(command, shell=True)
    s = s.decode('utf-8').split('\n')[1]
    s = s[s.find('gray(')+5:-1]
    value = int(s) // 2.55
    return value


def del_image(path):
    os.remove(path)


def updateBrightness():
    if len(BRIGHTNESS) >= 5:
        BRIGHTNESS.pop(0)
    create_image_fswebcam(IMAGE_PATH)
    BRIGHTNESS.append(calc_avgcolor(IMAGE_PATH))
    del_image(IMAGE_PATH)
    Timer(UPDATE_BRIGHTNESS_TIMEOUT, updateBrightness).start()


def getBrightnessValue():
    current_brightness = int(round(sum(BRIGHTNESS)/len(BRIGHTNESS), 0))
    return current_brightness


def setKbdBacklight(value):
    brightness = int(round(value/12, 0))
    idle = getPowerSaveStatus_dbus()
    idle_time = 60000
    if idle < idle_time:
        if brightness <= 3:
            if brightness == 0:
                brightness = 1
            if getKbdBacklight_dbus() != brightness:
                setKbdBacklight_dbus(brightness)
        else:
            if getKbdBacklight_dbus() != brightness:
                setKbdBacklight_dbus(0)
    else:
        setKbdBacklight_dbus(0)


def setKbdBacklight_dbus(value):
    bus = dbus.SystemBus()
    obj = bus.get_object('org.freedesktop.UPower',
                         '/org/freedesktop/UPower/KbdBacklight')
    interface = dbus.Interface(obj,
                               dbus_interface='org.freedesktop.UPower.KbdBacklight')
    if value in [0, 1, 2, 3]:
        interface.SetBrightness(dbus.Int32(value))


def getKbdBacklight_dbus():
    bus = dbus.SystemBus()
    obj = bus.get_object('org.freedesktop.UPower',
                         '/org/freedesktop/UPower/KbdBacklight')
    interface = dbus.Interface(obj,
                               dbus_interface='org.freedesktop.UPower.KbdBacklight')
    result = int(interface.GetBrightness())
    return result


def getPowerSaveStatus_dbus():
    bus = dbus.SessionBus()
    obj = bus.get_object('org.freedesktop.ScreenSaver',
                         '/org/freedesktop/ScreenSaver')
    interface = dbus.Interface(obj,
                               dbus_interface='org.freedesktop.ScreenSaver')
    result = int(interface.GetSessionIdleTime())
    return result


def updateKbd():
    idle = getPowerSaveStatus_dbus()
    if idle < IDLE_KBD_TIMEOUT:
        brightness = int(round(getBrightnessValue()/12, 0))
        if brightness <= 3:
            if brightness == 0:
                brightness = 1
            if getKbdBacklight_dbus() != brightness:
                setKbdBacklight_dbus(brightness)
        else:
            if getKbdBacklight_dbus() != brightness:
                setKbdBacklight_dbus(0)
    else:
        setKbdBacklight_dbus(0)
    Timer(UPDATE_KBD_TIMEOUT, updateKbd).start()


def setDisplayBacklight_dbus(value):
    bus = dbus.SessionBus()
    obj = bus.get_object('org.kde.Solid.PowerManagement',
                         '/org/kde/Solid/PowerManagement/Actions/BrightnessControl')
    interface = dbus.Interface(obj, dbus_interface='org.kde.Solid.PowerManagement.Actions.BrightnessControl')
    interface.setBrightness(dbus.Int32(value))


def getDisplayBacklight_dbus():
    bus = dbus.SessionBus()
    obj = bus.get_object('org.kde.Solid.PowerManagement',
                         '/org/kde/Solid/PowerManagement/Actions/BrightnessControl')
    interface = dbus.Interface(obj, dbus_interface='org.kde.Solid.PowerManagement.Actions.BrightnessControl')
    result = int(interface.brightness())
    return result


def setDisplayBacklight(value):
    if value <= 90:
        value += 10
    brightness = round(value, -1)
    if getDisplayBacklight_dbus() != brightness:
        setDisplayBacklight_dbus(brightness)


def updateDisplay():
    setDisplayBacklight(getBrightnessValue())
    Timer(UPDATE_DISPLAY_TIMEOUT, updateDisplay).start()

if __name__ == '__main__':
    updateBrightness()
    updateKbd()
    updateDisplay()
