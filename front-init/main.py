from http.server import HTTPServer, BaseHTTPRequestHandler
import pathlib
import urllib.parse
import mimetypes
import socket
import json
from threading import Thread
from datetime import datetime

# HTTP Server
class HttpHandler(BaseHTTPRequestHandler):
    
    def send_static(self):
        """Статичні ресурси"""
        # Обробіть під час роботи програми статичні ресурси: style.css, logo.png;
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())
            
    def do_GET(self):
        """Маршрутизація в застосунку"""
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                # У разі виникнення помилки 404 Not Found повертайте сторінку error.html
                self.send_html_file('error.html', 404)
                
    def do_POST(self):
        """Робота з формою"""
        # Організуйте роботу з формою на сторінці message.html;
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        
        # Відправка даних на UDP сервер
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_server_address = ('localhost', 5000)
        data_str = json.dumps(data_dict)
        udp_socket.sendto(data_str.encode(), udp_server_address)
        
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        """Для відповіді браузеру"""
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


# UDP Socket Server
class UdpServer:
    
    def __init__(self):
        self.data = {}
    
    def start_server(self):
        server_address = ('localhost', 5000)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(server_address)
        
        while True:
            data, addr = udp_socket.recvfrom(1024)
            data_dict = json.loads(data.decode())
            timestamp = str(datetime.now())
            self.data[timestamp] = data_dict
            self.save_data_to_json()
    

    def save_data_to_json(self):
        with open('storage/data.json', 'w', encoding='utf-8') as json_file:
            json.dump(self.data, json_file, ensure_ascii=False, indent=4)


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_udp_server():
    udp_server = UdpServer()
    udp_server.start_server()


if __name__ == '__main__':
    # Запускаємо HTTP сервер та UDP сервер в різних потоках
    http_server_thread = Thread(target=run_http_server)
    udp_server_thread = Thread(target=run_udp_server)
    
    http_server_thread.start()
    udp_server_thread.start()
