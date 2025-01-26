import http.server
import os
import socketserver
import threading

from .helper import local_path


class WebService(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        start_web()


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "map.html"
        return http.server.SimpleHTTPRequestHandler.do_GET(self)


def start_web():
    # Create an object of the above class
    os.chdir(local_path)
    handler_object = MyHttpRequestHandler

    PORT = 8000
    my_server = socketserver.TCPServer(("", PORT), handler_object)

    # Star the server
    my_server.serve_forever()
