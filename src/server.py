from http.server  import HTTPServer, BaseHTTPRequestHandler
from json         import loads, dumps
from json.decoder import JSONDecodeError
from controller   import *

class CrazyHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request        = self.rfile.read(content_length)

        try:
            json = loads(request.decode())
            print("[DEBUG] Received request: {}".format(str(json)))

            if "command" in json:
                if json["command"] == "start":
                    self.server.commandQueue.put(StartCommand())
                elif json["command"] == "stop":
                    self.server.commandQueue.put(StopCommand())
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


def runServer(hostname, port, commandQueue):
    server              = HTTPServer((hostname, port), CrazyHandler)
    server.commandQueue = commandQueue
    server.serve_forever()


class PathPlanner(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request        = self.rfile.read(content_length)

        try:
            json = loads(request.decode())
            print("[DEBUG] Received request: {}".format(str(json)))

            start, target = json["start"], json["target"]

            start  = Point(start[0],  start[1],  start[2])
            target = Point(target[0], target[1], target[2])

            planningStart = time.time()
            path = self.server.scene.planPath(start, target)
            print("[DEBUG] Found path: {:s}".format(str(path)))
            print("[DEBUG] Path planning took {:.2f}s.".format(time.time() - planningStart))
            for waypoint in path:
                self.server.commandQueue.put(PositionCommand(waypoint.x, waypoint.y, waypoint.z))

            else:
                raise Exception("Unexpected input: {}".format(json))

            reply = { "ok" : json }
        except Exception as e:
           reply = { "error" : str(e) }

        self._set_headers()
        self.wfile.write(dumps(reply).encode())


def runPathPlanner(hostname, port, commandQueue):
    # the static scene
    table1 = Translate(Scale(Cube(), 1.30, 0.65, 0.75), 1.35, 0.68, 0.00)
    table2 = Translate(Scale(Cube(), 1.30, 0.65, 0.75), 1.35, 2.68, 0.00)

    obstacle = Translate(Scale(Cube(), 1.60, 0.8, 2.20), 1.25, 1.70, 0.00)

    server              = HTTPServer((hostname, port), PathPlanner)
    server.commandQueue = commandQueue
    server.scene        = Scene(4.0, 4.0, 2.6, 0.1, [table1, table2, obstacle])
    server.serve_forever()
