from picamera import PiCamera
import time

cam = PiCamera(resolution='640x480', framerate=24)
cam.start_preview()
cam.start_recording('mission.h264', format='h264', profile='baseline')
print('Recording..')
try:
    while True:
        pass
except KeyboardInterrupt:
    cam.stop_recording()
    cam.stop_preview()
    cam.close()
print('Terminated.')