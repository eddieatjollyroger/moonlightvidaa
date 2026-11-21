#!/usr/bin/env python3
"""Tiny HTTPS server for the Moonlight capability test page.

Run on the Pi from this directory:
    python3 serve-capability.py

Then open https://192.168.1.69:8444/ on the TV browser.
The TV will warn about the self-signed certificate; choose to continue.
"""
import http.server
import os
import ssl

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(HERE, "capability"))

server = http.server.HTTPServer(("0.0.0.0", 8444), http.server.SimpleHTTPRequestHandler)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(os.path.join(HERE, "cert.pem"), os.path.join(HERE, "key.pem"))
server.socket = context.wrap_socket(server.socket, server_side=True)
print("Capability test: https://192.168.1.69:8444/")
server.serve_forever()
