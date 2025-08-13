import camera_main.camera
import keyboard
import RPi.GPIO as GPIO
import socket
import threading
import time


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

    def __init__(self):
        self.speed     = 0
        self.direction = 0                          # 0 equals forward | 1 equals backwards
        self.left_wheels_speed = self.speed
        self.right_wheels_speed = self.speed

        # blip controls used with web interface.
        self.blip_fwd_speed  = 75
        self.blip_turn_speed = 75
        self.blip_fwd_time   = 0.5
        self.blip_turn_time  = 0.5

        # Thread events, these will be used for interprocess communication
        self.recording = threading.Event()          # Camera event

        # Attachment instances (Camera, LiDar, Motors)
        #self.camera = camera_main.camera.Camera(self.recording)   # Create camera instance
        self.initialize_motors()

        self.server_=None

    def initialize_server(self):
        self.server = socket.socket(socket.AF_inet, socket.SOCK_STREAM, 0)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((rover.ROVER_IP, rover.ROVER_PORT))
        self.server.listen(2)
        
        # Entry point into the server
        while True:
            cmd_ctr, cmd_addr = self.server.accept()    # cmd_ctr represents the socket the server and client are using to communicate
            print(f"Connection established: {cmd_addr[0]}:{cmd_addr[1]}")
            self.handle_CMD(cmd_ctr)                    # main command handling function

    def handle_CMD(self, cmd_ctrl):
        None

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
        self.back_left_motor   = motor(speed_pin_BL, left_motor_dir_pin1B, left_motor_dir_pin2B)
        self.motors = [self.front_right_motor, self.front_left_motor, self.back_right_motor, self.back_left_motor] # Create motor array

    def speed_up(self, direction_handler):                                  # direction is function object
        adjustment = rover.SPEED_INCREMENT
        if(self.speed + rover.SPEED_INCREMENT >= rover.MAX_SPEED): 
            adjustment = 0
        
        self.speed += adjustment 
        self.left_wheels_speed += adjustment 
        self.right_wheels_speed += adjustment 

        print(f"l: {self.left_wheels_speed} r: {self.right_wheels_speed} s: {self.speed}")
        direction_handler(self.speed)
        
    def slow_down(self, direction_handler):                                 # dir is a function object.
        adjustment = rover.SPEED_INCREMENT
        if(self.speed - rover.SPEED_INCREMENT <= rover.MIN_SPEED):
            self.direction = not self.direction     # Update direction of the rover
            adjustment = 0
        
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
        self.front_left_motor.update_motor_speed(speed)
        self.back_left_motor.update_motor_speed(speed)

    def turn_left(self):
        if self.left_wheels_speed - rover.SPEED_INCREMENT < rover.MIN_SPEED: 
            self.left_wheels_speed = rover.MIN_SPEED
        else:
            self.left_wheels_speed -= rover.SPEED_INCREMENT

        print(f"Left wheel speed: {self.left_wheels_speed}")
        self.turn_left_wheels(self.left_wheels_speed)

    def turn_right_wheels(self, speed):
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

    def keyboard_driver_interface(self):
        while 1:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                key = event.name

                if key == 'q':
                    print("Turning off engine.")
                    break

                if key == 'up':
                    print("Accelerate\n")
                    if not self.direction:          # If moving fwd, up = speed up ; if moving bwd, down = slow down
                        self.speed_up(self.move_fwd)
                    else:
                        self.slow_down(self.move_bwd)

                if key == 'down':                   # If moving fwd, down = slow down ; if moving bwd, up = speed up
                    print("Slowing down\n")
                    if not self.direction:
                        self.slow_down(self.move_fwd)
                    else:
                        self.speed_up(self.move_bwd)

                if key == 'left':
                    print("Turning left\n")
                    self.turn_left()

                if key == 'right':
                    print("Turning right\n")
                    self.turn_right()

                if key == 's':
                    print("Stopping.\n")
                    self.speed = rover.MIN_SPEED
                    self.stop_motors()

                if key == 'i':
                    self.straighten()

                if key == 'r':
                    if not self.recording.is_set():
                        print('Recording initiated.')
                        self.recording.set()
                        vid = threading.Thread(target=self.camera.rec)
                        vid.start()
                    else:
                        self.recording.clear()
                        print('Recording terminated.')
                    
    def web_blip_interface(self):
        while 1:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                key = event.name

                if key == 'q':
                    print("Turning off engine.")
                    break

                if key == 'up':
                    print("blip fwd")
                    self.blip_fwd()

                if key == 'down':                   # If moving fwd, down = slow down ; if moving bwd, up = speed up
                    print("blip fwd")
                    self.blip_bwd()

                if key == 'left':
                    print("blip left")
                    self.blip_left()

                if key == 'right':
                    print("blip right")
                    self.blip_right()

                if key == 's':
                    print("Stopping.\n")
                    self.speed = rover.MIN_SPEED
                    self.stop_motors()

                if key == 'i':
                    self.straighten()

                if key == 'r':
                    if not self.recording.is_set():
                        print('Recording initiated.')
                        self.recording.set()
                        vid = threading.Thread(target=self.camera.rec)
                        vid.start()
                    else:
                        self.recording.clear()
                        print('Recording terminated.')


    def turn_on(self, control_interface):
        print("Robot on...")
        control_interface()
            
robot = rover()
robot.turn_on(robot.web_blip_interface)

