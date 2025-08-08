import io
import time
import threading
from picamera import PiCamera
from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIHandler, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from ws4py.websocket import WebSocket

class FrameBuffer:      # The main purpose of this class is to help with synchronization
    def __init__(self):
        self.frame     = None
        self.buffer    = io.BytesIO()
        self.condition = threading.Condition() # Threading condition used to synchronize camera and WebSocketServer

    def write(self, buf):
        if buf.startswith(b'\x00\x00\x00\x01'):
            with self.condition:
                self.buffer.seek(0)
                self.buffer.write(buf)
                self.buffer.truncate()
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()


class Camera:
    def __init__(self, thread_e, ip, port):
        self.thread_e = thread_e    # Passed in from rover class, used to manage threads.
        self.camera   = PiCamera(resolution='640x480', framerate=24)
        self.preview_ = False
        self.frame_buffer = FrameBuffer()
        self.ip_   = ip
        self.port_ = port
        self.server_WebSocket = None

        
    def initialize_stream_server(self):
        WebSocketWSGIHandler.http_version = 1.1  # Set class level attribute

        # Pass in classes from ws4py to gain different functionality.
        try:
            self.server_WebSocket = make_server(self.ip_, self.port_, server_class=WSGIServer,handler_class=WebSocketWSGIRequestHandler, app=WebSocketWSGIApplication(handler_cls=WebSocket))
            self.server_WebSocket.initialize_websockets_manager()
            self.websocket_thread = threading.Thread(target=self.server_WebSocket.serve_forever)
        except Exception as e:
            print(f'Error initializing WebSocket server: {e}')
            


    def stream(self):
        try:
            self.initialize_stream_server()
            self.streaming = True
            self.websocket_thread.start() # Spins websocket server on a separate thread.
            self.camera.start_recording(self.frame_buffer, format='h264', profile='baseline')
            print("Streaming")
            while self.thread_e.is_set():
                with self.frame_buffer.condition:
                    self.frame_buffer.condition.wait()
                    self.server_WebSocket.manager.broadcast(self.frame_buffer.frame, binary=True)
        except Exception as e:
            print(f"Stream Error: {e}")
        finally:
            print("Terminating stream")
            self.streaming = False
            self.camera.stop_recording()
            self.thread_e.clear()

    def rec(self):
        time__ = time.strftime('%y_%m_%d_%I_%M_%S_mission.h264')
        output_=f'camera_main/videos/{time__}' # Because thread event runs in ROVER_TEST_BED directory, we need to reference from here
        #self.camera.start_preview(True)
        
        if self.thread_e.is_set(): # Check that the thread event is set
            if self.preview_:
                self.camera.start_preview()
            self.camera.start_recording(output=output_, format='h264', profile='baseline')
            while self.thread_e.is_set():
                None # Holds the video until mission over
            if self.preview_:
                self.camera.stop_preview()
            self.camera.stop_recording()
            self.camera.close()




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