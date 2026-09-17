from http.server import HTTPServer
from .config import HOST, PORT
from .handler import Handler

def serve():
    HTTPServer((HOST, PORT), Handler).serve_forever()
