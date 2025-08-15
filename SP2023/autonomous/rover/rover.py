import camera.camera as cam
import config.network_pins as npins
import config.pins as pins
import rover.motor as motor
import RPi.GPIO as GPIO
import serial
import socket
import threading
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class rover:
    MAX_SPEED = 90
    MIN_SPEED = 0
    SPEED_INCREMENT = 10

    def __init__(self):
        self.speed     = 0
        self.direction = 0                          # 0 equals forward | 1 equals backwards
        self.left_wheels_speed = self.speed # Possible bug here since we are using one speed to reference two wheels?
        self.right_wheels_speed = self.speed

        # Thread events, these will be used for interprocess communication
        self.streaming_thread_event= threading.Event()   
        self.static_thread_event= threading.Event()          # Camera event

        # blip controls used with web interface.
        self.blip_fwd_speed  = 75
        self.blip_turn_speed = 75
        self.blip_fwd_time   = 0.5
        self.blip_turn_time  = 0.5

        # Thread events, these will be used for interprocess communication
        self.recording = threading.Event()          # Camera event

        self.ip   = npins.ROVER_IP_PIN      # Command server and camera operate out of this IP
        self.port = npins.ROVER_PORT_PIN    # Port used for cmd server

        self.camera = cam.Camera(self.streaming_thread_event, self.ip, npins.ROVER_CAMERA_STREAM_PORT_PIN) # Create camera instance
        self.initialize_motors()

    def initialize_cmd_server(self):
        self.server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        
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
                   # main command handling function

    def start_streaming(self):
        if not self.streaming_thread_event.is_set():
            self.streaming_thread_event.set()
            print("Starting stream")
            stream = threading.Thread(target=self.camera.stream)
            stream.start()
        else:
            None

    def start_streaming_static(self):
        if not self.static_thread_event.is_set():
            self.static_thread_event.set()
            print("start static sensor stream")
            stream = threading.Thread(target = static_main.static_code.mymain)
            stream.start()
        else:
            None

    # Web interface blip commands. Good for when using a mouse.
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
        # Create motor instances 
        self.front_right_motor = motor.Motor(pins.DUTYCYCLE_FR_FR, pins.MOTOR_FRONT_RIGHT_A, pins.MOTOR_FRONT_RIGHT_B)
        self.front_left_motor  = motor.Motor(pins.DUTYCYCLE_FR_FL, pins.MOTOR_FRONT_LEFT_A, pins.MOTOR_FRONT_LEFT_B)
        self.back_right_motor  = motor.Motor(pins.DUTYCYCLE_FR_BR, pins.MOTOR_BACK_RIGHT_A, pins.MOTOR_BACK_RIGHT_B)
        self.back_left_motor   = motor.Motor(pins.DUTYCYCLE_FR_BL, pins.MOTOR_BACK_LEFT_A, pins.MOTOR_BACK_LEFT_B)
        
        # Motor array 
        self.motors = [self.front_right_motor, self.front_left_motor, self.back_right_motor, self.back_left_motor]

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
        if self.right_wheels_speed - rover.SPEED_INCREMENT < rover.MIN_SPEED: 
            self.right_wheels_speed = rover.MIN_SPEED
        else:
            self.right_wheels_speed -= rover.SPEED_INCREMENT

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

    # Web interface blip commands. Good for when using a mouse.
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

    def turn_on(self, control_interface):
        print("Robot on...")
        self.start_streaming()
        self.initialize_cmd_server()

robot = rover()
robot.turn_on()

'''
Boot sequence:
    1. Initialize rover object
    2. run Rover.turn_on()
        a. rover creates a localized server instance where it receives commands
        b. rover creates a camera object on the
        a. Connects to server
'''