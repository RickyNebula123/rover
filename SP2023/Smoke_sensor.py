import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()

serialInst.baudrate = 9600
serialInst.port = "/dev/ttyACM0"
serialInst.open()

while True:
	if serialInst.in_waiting:
		packet = serialInst.readline()
		packet = (packet.decode('utf').rstrip('\n'))
		smoke= packet.split(',')[0]
		mono= packet.split(',')[1]
		s1= ''.join(c for c in smoke if c.isdecimal())
		s1 = int(s1)
		if s1 < 200:
			s_out = 'Normal reading'
		if s1 > 220:
			s_out = 'High reading'
		if s1 < 220 and s1 > 200:
			s_out = 'Moderate reading'
		Smoke_out = ("Smoke " + s_out + " " +str(s1))	
		m1= ''.join(c for c in mono if c.isdecimal())
		m1 = int(m1)
		if m1 < 100:
			m_out = 'Normal reading'
		if m1 > 150:
			s_out = 'High reading'
		if m1 < 150 and m1 > 100:
			m_out = 'Moderate reading'
		Mono_out = ("Monoxoide " +m_out+ " "+ str(m1))
## 		Smoke_out gives the smoke sensor string to be displayed on WebServer
##		Mono_out gives the monoxide sensor string to be displayed on WebServer
