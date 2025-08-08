import time
import threading
from picamera import PiCamera

class Camera:
    def __init__(self, thread_e, mode='video', preview=False):
        self.thread_e = thread_e    # Passed in from rover class (rover creates instance of camera)
        self.camera = Picamera2()
        self.config(mode)
        
    def config(self, mode):
        if mode == 'video':
            self.camera.configure(self.camera.create_video_configuration())
        
    def rec(self, preview=False):
        encoder = H264Encoder(bitrate=10000000)
        output='videos/mission.h264'
        #self.camera.start_preview(True)
        
        if self.thread_e.is_set(): # Check that the thread event is set
            self.camera.start_recording(encoder, output)
            while self.thread_e.is_set():
                None # Holds the video until mission over
            self.camera.stop_recording()
            self.camera.close()

        #self.camera.stop_preview()


# e = threading.Event()
# e.set()     # Trigger camera
# foo = Camera(e, preview=True)

# try:
#     foo.rec()
#     while True:
#         None
# except KeyboardInterrupt:
#     print('\nKeyboard Interrupt.')
# finally:
#     print('Terminating')