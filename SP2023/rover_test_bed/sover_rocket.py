import camera_main.camera
import static_main.static_code
import RPi.GPIO as GPIO
import socket
import threading
import time
import serial

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class motor:
    def __init__(self, duty_cycle, bwd, fwd):
        self.duty_cycle = duty_cycle        # Duty cycle pin

        # Direction pins
        self.fwd = fwd                      
        self.bwd = bwd

        # Motor speed
        self.speed = 0
        self.initialize_connections()
        self.start_PWM()

    def initialize_connections(self):
        GPIO.setup(self.duty_cycle, GPIO.OUT)
        GPIO.setup(self.fwd, GPIO.OUT)   # Register motor connections with RPi
        GPIO.setup(self.bwd, GPIO.OUT)

    def start_PWM(self):
        self.motor_control = GPIO.PWM(self.duty_cycle, 1000) # Create PWM instance to drive motor.
        self.motor_control.start(0)

    def fwd_(self):
        GPIO.output(self.bwd, GPIO.LOW)
        GPIO.output(self.fwd, GPIO.HIGH)

    def bwd_(self):
        GPIO.output(self.fwd, GPIO.LOW)
        GPIO.output(self.bwd, GPIO.HIGH)

    def stop(self):
        self.motor_control.stop()
        self.motor_control.start(0)
        self.speed = 0

    def update_motor_speed(self, speed):
        self.motor_control.ChangeDutyCycle(speed)

class rover:
    MAX_SPEED = 90
    MIN_SPEED = 0
    SPEED_INCREMENT = 10
    ROVER_IP = '192.168.1.223'
    ROVER_PHONE_IP = '172.20.10.6'
    ROVER_PORT = 4422                              # rover command server port
    ROVER_STREAM_PORT = 4040                       # rover camera stream port

    def __init__(self):
        self.speed     = 0
        self.direction = 0                         # 0 equals forward | 1 equals backwards
        self.left_wheels_speed = self.speed
        self.right_wheels_speed = self.speed

        # Thread events, these will be used for interprocess communication
        self.streaming_thread_event= threading.Event()   
        self.static_thread_event= threading.Event()          # Camera event
       # Camera event
        #self.mapping = threading.Event()                       # LiDar event

        # blip controls used with web interface.
        self.blip_fwd_speed  = 75
        self.blip_turn_speed = 75
        self.blip_fwd_time   = 0.5
        self.blip_turn_time  = 0.5

        # Attachment instances (Camera, LiDar, Motors)
        self.ip = rover.ROVER_PHONE_IP              # Command server and camera operate out of this IP
        self.port = rover.ROVER_PORT                # Port used for cmd server

        self.camera = camera_main.camera.Camera(self.streaming_thread_event, self.ip, rover.ROVER_STREAM_PORT)   # Create camera instance
        self.initialize_motors()

        self.server_=None

    def initialize_cmd_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))
        self.server.listen(2)
        
        # Entry point into the server
        while True:
            print("Waiting for connection")
            cmd_ctr, cmd_addr = self.server.accept()    # cmd_ctr represents the socket the server and client are using to communicate
            print(f"Connection established: {cmd_addr[0]}:{cmd_addr[1]}")
            print("Waiting for command")
            self.handle_CMD(cmd_ctr)                    # main command handling function

    def start_streaming(self):
        if not self.streaming_thread_event.is_set():
            self.streaming_thread_event.set()
            print("Starting stream")
            stream = threading.Thread(target=self.camera.stream)
            stream.start()
        else:
            None
    # Web interface blip commands. Good for when using a mouse.

    def start_streaming_static(self):
        if not self.static_thread_event.is_set():
            self.static_thread_event.set()
            print("start static sensor stream")
            stream = threading.Thread(target = static_main.static_code.mymain)
            stream.start()
        else:
            None


    def blip_fwd(self):
        self.move_fwd(self.blip_fwd_speed)
        time.sleep(self.blip_fwd_time)
        self.stop_motors()

    def blip_bwd(self):
        self.move_bwd(self.blip_fwd_speed)
        time.sleep(self.blip_fwd_time)
        self.stop_motors()

    def blip_left(self):
        self.turn_left_wheels(self.blip_turn_speed)
        time.sleep(self.blip_turn_time)
        self.stop_motors()

    def blip_right(self):
        self.turn_right_wheels(self.blip_turn_speed)
        time.sleep(self.blip_turn_time)
        self.stop_motors()

    def handle_CMD(self, cmd_ctr):
        Arduino = serial.Serial("/dev/ttyACM0",9600,timeout=1) 
        while True:
            data = cmd_ctr.recv(16)
            print(f"CMD received: {data}")

            if data == b'QUIT\x00':
                print("Turning off engine.")
                break

            if data == b'FWD\x00':
                print("Moving fwd\n")
                self.blip_fwd()

            if data == b'CAMERA_D\x00':
                print("Cam Dwn\n")
                Arduino.write(b's')

            if data == b'CAMERA_U\x00':
                print("Cam Up\n")
                Arduino.write(b'w')

            if data == b'CAMERA_L\x00':
                print("Cam L\n")
                Arduino.write(b'a')

            if data == b'CAMERA_R\x00':
                print("Cam R\n")
                Arduino.write(b'd')

            if data == b'BWD\x00':                   # If moving fwd, down = slow down ; if moving bwd, up = speed up
                print("Moving back\n")
                self.blip_bwd()

            if data == b'LEFT\x00':
                print("Turning left\n")
                self.blip_left()

            if data == b'RIGHT\x00':
                print("Turning right\n")
                self.blip_right()

            if data == b'STOP\x00':
                print("Stopping.\n")
                self.speed = rover.MIN_SPEED
                self.stop_motors()

            if data == 'i':
                self.straighten()

            if data == b'REC_DISABLED\x00': # ****CURENTLY DISABLED**** Press REC on wp to initiate recording. Press REC again to terminate recording.
                if not self.recording.is_set():
                    print('Recording initiated.')
                    self.recording_thread_event.set()
                    vid = threading.Thread(target=self.camera.rec)
                    vid.start()
                else:
                    self.recording.clear()
                    print('Recording terminated.')

    def initialize_motors(self):       
        # Motor speed pins; Enable pins
        speed_pin_FR = 18
        speed_pin_FL = 12
        speed_pin_BR = 13
        speed_pin_BL = 19

        # Motor direction pins: (For duty cycle control)
        right_motor_dir_pin1F = 24 # Front
        right_motor_dir_pin2F = 23 # Front
        left_motor_dir_pin1F  = 8  # Front
        left_motor_dir_pin2F  = 25 # Front

        right_motor_dir_pin1B = 27 # Back
        right_motor_dir_pin2B = 22 # Back
        left_motor_dir_pin1B  = 6  # Back
        left_motor_dir_pin2B  = 5  # Back

        # Create motor instances 
        self.front_right_motor = motor(speed_pin_FR, right_motor_dir_pin1F, right_motor_dir_pin2F)
        self.front_left_motor  = motor(speed_pin_FL, left_motor_dir_pin1F, left_motor_dir_pin2F)
        self.back_right_motor  = motor(speed_pin_BR, right_motor_dir_pin1B, right_motor_dir_pin2B)
        self.back_left_motor   = motor(speed_pin_BL, left_motor_dir_pin1B, left_motor_dir_pin2B)    # verified
        self.motors = [self.front_right_motor, self.front_left_motor, self.back_right_motor, self.back_left_motor] # Create motor array

    def speed_up(self, direction_handler):                                  # direction is function object
        adjustment = rover.SPEED_INCREMENT
        if (self.speed + rover.SPEED_INCREMENT) >= rover.MAX_SPEED: 
            adjustment = 0
        
        self.speed += adjustment 
        if self.left_wheels_speed + adjustment >= rover.MAX_SPEED:
            None
        else:
            self.left_wheels_speed += adjustment 
        if self.right_wheels_speed + adjustment >= rover.MAX_SPEED:
            None
        else:
            self.right_wheels_speed += adjustment 

        print(f"l: {self.left_wheels_speed} r: {self.right_wheels_speed} s: {self.speed}")
        direction_handler(self.speed)
        
    def slow_down(self, direction_handler):                                 # dir is a function object.
        adjustment = rover.SPEED_INCREMENT
        if(self.speed - rover.SPEED_INCREMENT <= rover.MIN_SPEED):
            self.direction = not self.direction     # Update direction of the rover
            self.speed = self.left_wheels_speed = self.right_wheels_speed = 0
            adjustment = 0
        else:
            self.speed -= adjustment 
            self.left_wheels_speed -= adjustment 
            self.right_wheels_speed -= adjustment 

        print(f"l: {self.left_wheels_speed} r: {self.right_wheels_speed} s: {self.speed}")

        direction_handler(self.speed)

    def move_fwd(self, speed):
        for motor in self.motors:
            motor.fwd_()
        for motor in self.motors:
            motor.update_motor_speed(speed)

    def move_bwd(self, speed):
        for motor in self.motors:
            motor.bwd_()
        for motor in self.motors:
            motor.update_motor_speed(speed)

    def turn_left_wheels(self, speed):
        print(f'Updating left wheel speed: {speed}')
        self.front_left_motor.update_motor_speed(speed)
        self.back_left_motor.update_motor_speed(speed)

    def turn_left(self):
        if self.left_wheels_speed + rover.SPEED_INCREMENT > rover.MAX_SPEED: 
            self.left_wheels_speed = rover.MAX_SPEED
        else:
            self.left_wheels_speed += rover.SPEED_INCREMENT

        print(f"Left wheels speed: {self.left_wheels_speed}")
        self.turn_left_wheels(self.left_wheels_speed)

    def turn_right_wheels(self, speed):
        print(f'Updating right wheels speed: {speed}')
        self.front_right_motor.update_motor_speed(speed)
        self.back_right_motor.update_motor_speed(speed)

    def turn_right(self):
        if self.right_wheels_speed + rover.SPEED_INCREMENT > rover.MAX_SPEED: 
            self.right_wheels_speed = rover.MAX_SPEED
        else:
            self.right_wheels_speed += rover.SPEED_INCREMENT

        print(f"Right wheel speed: {self.right_wheels_speed}")
        self.turn_right_wheels(self.right_wheels_speed)
    
    def straighten(self):
        max_speed = max(self.left_wheels_speed, self.right_wheels_speed)
        self.left_wheels_speed = max_speed
        self.right_wheels_speed = max_speed
        
        self.turn_left_wheels(self.left_wheels_speed)
        self.turn_right_wheels(self.right_wheels_speed)

        print(f'LW speed: {self.left_wheels_speed}\nRW speed: {self.right_wheels_speed}')

    def stop_motors(self):
        for motor in self.motors:
            motor.stop()
        self.speed = self.left_wheels_speed = self.right_wheels_speed = 0
            
    def turn_on(self):
        print("Robot on...")
        self.start_streaming()
        
        self.initialize_cmd_server()
robot = rover()
robot.turn_on()
# while 1:
#     event = keyboard.read_event()
#     if event.event_type == keyboard.KEY_DOWN:
#         key = event.name
#         print(f"Pressed: {key}")
