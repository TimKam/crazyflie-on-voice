from http.server import BaseHTTPRequestHandler, HTTPServer
from json import *

port = 8081


class TestServer(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

    @staticmethod
    def is_request_valid(data):
        """
        Determines if request data is valid; it needs to have:
        * either property "command" or property "distance"
        * only acceptable value if "command" is "stop"
        * "distance" needs to be array of length 3 containing only ints/floats
        :param data: request data as dictionary
        :return: True or False
        """
        if len(data) != 1:
            return False
        if 'command' in data and data['command'] == 'stop':
            return True
        if 'distance' not in data:
            return False
        has_correct_length = len(data['distance']) == 3
        has_correct_type = all(isinstance(n, float) or isinstance(n, int)
                               for n in data['distance'])
        if has_correct_length and has_correct_type:
            return True
        return False

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(  # return HTML redirect
            bytes('<strong>Server is running!</strong>', 'utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request = self.rfile.read(content_length)

        try:
            json = loads(request.decode())
            if self.is_request_valid(json):
                self.send_response(200)
                reply = {"success": json}
            else:
                self.send_response(400)
                reply = {"invalid request data": json}
        except JSONDecodeError as e:
            self.send_response(400)
            reply = {"error": str(e)}

        self._set_headers()
        self.wfile.write(dumps(reply).encode())


def run():
    server_address = ('', port)
    server = HTTPServer(server_address, TestServer)
    print(f'Running test server on port {port}...')
    server.serve_forever()


run()
