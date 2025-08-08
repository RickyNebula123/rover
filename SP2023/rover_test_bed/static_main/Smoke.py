import serial.tools.list_ports
import requests 

ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()

serialInst.baudrate = 9600
serialInst.port = "/dev/ttyACM0"
serialInst.open()
ServerIp = '172.20.10.7'
ServerPort = 7777
url = 'http://' + ServerIp + ':' + str(ServerPort)+ '/sensor'
while True:
    if serialInst.in_waiting:
        packet = serialInst.readline()
        packet = (packet.decode('utf').rstrip('\n'))
        smoke= packet.split(',')[0]
        mono= packet.split(',')[1]
        s1= ''.join(c for c in smoke if c.isdecimal())
        s1 = int(s1)	
        m1= ''.join(c for c in mono if c.isdecimal())
        m1 = int(m1)
        response = requests.post(url, data={"smoke":f"{str(m1)} {str(s1)}"})
        print(f"Server response {response}")

	
## 		Smoke_out gives the smoke sensor string to be displayed on WebServer
##		Mono_out gives the monoxide sensor string to be displayed on WebServer



