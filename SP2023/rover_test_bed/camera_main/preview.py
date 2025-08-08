from picamera2 import Picamera2, Preview
import time

picam2 = Picamera2()
config = picam2.create_video_configuration()
picam2.configure(config)
picam2.start(show_preview=False)
time.sleep(2)

picam2.stop_preview()
picam2.start_preview(Preview.QTGL, x=100, y=200, width=800, height=600)

try:
    while True:
        pass
except KeyboardInterrupt:
    picam2.close()