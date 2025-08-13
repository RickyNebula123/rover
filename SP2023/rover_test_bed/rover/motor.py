import RPi.GPIO as GPIO

class Motor:
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