import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from xml.etree.ElementTree import Element, ElementTree, tostring

HOST = ''
DELL = "192.168.1.249"
LOOPBACK = "127.0.0.1"
PORT = 7777

ROBOT_SERVER = LOOPBACK      # IP of our target computer
ROBOT_PORT   = 4422          # Port of our robot server
NETWORK_PATH = "/home/pi/rover/SP2023/network_server/web_interface"

class Robot_Server_Connection:
    def __init__(self, ROBOT_SERVER='', PORT=5555):
        self.ROBOT_SERVER=ROBOT_SERVER
        self.ROBOT_PORT=PORT
        self.server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

        self.CONNECTION_STATUS = False

    def init_connection(self):
        try:
            self.server_connection.connect((self.ROBOT_SERVER, self.ROBOT_PORT))
            self.CONNECTION_STATUS = True # Will use this in the future to ensure connection fidelity.
            print("Connected to rover server")
        except:
            print("Could not establish connection")
    
    def fwd_to_rover(self, data):
        try:
            self.server_connection.sendall(data[b'cmd'][0])
        except:
            self.CONNECTION_STATUS = False
            self.init_connection()
            self.server_connection.sendall(data[b'cmd'][0])


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def do_GET(self): # Serves videos, maps, pictures, logs.
        if self.path == '/':
            self.path = 'index.html'
            try:
                file_to_open = open(self.path).read()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes(file_to_open, 'utf-8'))
            except:
                file_to_open = "File not found."
                self.send_response(404)
        elif self.path.endswith('.wasm'):
            with open('avc.wasm', 'rb') as wasm_file:
                file_contents = wasm_file.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/wasm') # Set appropriate MIME headers
                self.end_headers()

                self.wfile.write(bytes(file_contents))
        elif self.path == '/Decoder.js':
            with open(NETWORK_PATH + '/Decoder.js','rb') as file:
                print(f"opening: {self.path}")
                file_contents = file.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript') # Set appropriate MIME types for JavaScript
                self.end_headers()

                # Send contents
                self.wfile.write(bytes(file_contents))# Send contents of the JavaScript file
        elif self.path.endswith('.js'):
            try:
                with open(self.path, 'rb') as file:
                    print(f"opening: {self.path}")
                    file_contents = file.read()

                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/javascript') # Set appropriate MIME types for JavaScript
                    self.end_headers()

                    # Send contents
                    self.wfile.write(bytes(file_contents))# Send contents of the JavaScript file
            except Exception as e:
                print(f"Error opening {self.path} file: {e}")

        
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length'))
        data_ = self.rfile.read(content_length)
        extracted = parse_qs(data_)         # No input sanitation. Take care of this before deploying on WWW
        '''
            Use these in the future if you need to debug
            or if you need to remind yourself how to communicate in webspeak
            print(f'Type of data_ = {type(data_)}')
            print(f"Type of extracted: {type(extracted)}")
            print(extracted)
        '''

        print(f"Path received to post: {self.path}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes('OK', 'utf-8'))

        if self.path == '/':
            try:
                print(extracted)
                rover_socket.fwd_to_rover(extracted)
            except:
                print("Could not forward data to rover.")
                
        if self.path == '/sensor':
            global SENSORS
            print(f"Sensor data received: {extracted}")

            SENSORS.mono, SENSORS.smoke, SENSORS.door = extracted[b'smoke'][0].split()
            SENSORS.convert_to_string()
            print(f"MONO: {SENSORS.mono} - SMOKE: {SENSORS.smoke} - DOOR: {SENSORS.door}")


rover_socket = Robot_Server_Connection('172.20.10.6', ROBOT_PORT)
rover_socket.init_connection()

httpd = HTTPServer((HOST, PORT), Handler)
httpd.serve_forever()