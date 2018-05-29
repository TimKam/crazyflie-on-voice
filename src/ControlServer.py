# Author: Christopher Blöcker, Timotheus Kampik, Tobias Sundqvist

from http.server import HTTPServer, BaseHTTPRequestHandler
from json import loads, dumps
from json.decoder import JSONDecodeError
from src.controller import *


class CrazyHandler(BaseHTTPRequestHandler):
    """
    The request handler for commands that should be sent to the crazyflie
    """
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request = self.rfile.read(content_length)

        try:
            json = loads(request.decode())
            print("[DEBUG] Received request: {}".format(str(json)))

            if "command" in json:
                if json["command"] == "start":
                    self.server.commandQueue.put(StartCommand())
                elif json["command"] == "stop":
                    self.server.commandQueue.put(StopCommand())
                elif json["command"] == "land":
                    self.server.commandQueue.put(LandComand())
                else:
                    raise Exception("Invalid command: {}".format(json["command"]))

            elif "distance" in json:
                [ dx, dy, dz ] = json["distance"]

                self.server.commandQueue.put(DistanceCommand(dx, dy, dz))

            else:
                raise Exception("Unexpected input: {}".format(json))

            reply = { "ok" : json }
        except Exception as e:
           reply = { "error" : str(e) }

        self._set_headers()
        self.wfile.write(dumps(reply).encode())


def run_server(hostname, port, commandQueue):
    """
    Runs a server and listen for commands sent to the crazyflie

    :param hostname:
    :param port:
    :param commandQueue:
    :return:
    """
    server = HTTPServer((hostname, port), CrazyHandler)
    server.commandQueue = commandQueue
    server.serve_forever()
