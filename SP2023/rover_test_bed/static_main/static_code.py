import asyncio
import serial.tools.list_ports
from bleak import BleakClient
import requests 

address = "E0:2A:3B:0E:2C:06"
sensor = '00002a00-0000-1000-8000-00805f9b34fb'
ServerIp = '172.20.10.7'
ServerPort = 7777
url = 'http://' + ServerIp + ':' + str(ServerPort)+ '/sensor'
status = "none"
ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
serialInst.baudrate = 9600
serialInst.port = "/dev/ttyACM0"
serialInst.open()

async def nameGet(address):
    global status
    async with BleakClient(address) as client:
        name1 = await client.read_gatt_char(sensor)
        name = bytearray.decode(name1) 
        if(not name==status):
            status = name
            print("STATUS: "+ status)

        
def main():
    if serialInst.in_waiting:
        packet = serialInst.readline()
        packet = (packet.decode('utf').rstrip('\n'))
        smoke= packet.split(',')[0]
        mono= packet.split(',')[1]
        s1= ''.join(c for c in smoke if c.isdecimal())
        s1 = int(s1)	
        m1= ''.join(c for c in mono if c.isdecimal())
        m1 = int(m1)
        response = requests.post(url, data={"smoke":f"{str(m1)} {str(s1)} {str(status)}"})
        print(f"Server response {response}")
    try: 
        asyncio.run(nameGet(address))
    except Exception as e:
        exit
        print(e)
        print("STATUS: "+status)
     
if __name__ == "__main__":
    while(True):
        main()



