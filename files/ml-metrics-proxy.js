// Tiny LAN-only HTTPS -> HTTP forwarder for Moonlight stream metrics.
// The stream page is HTTPS, so it cannot POST to TubeTV's plain HTTP /api/log
// directly. This forwards /api/log to 127.0.0.1:8484 using the existing cert.
const fs = require('fs');
const http = require('http');
const https = require('https');

const options = {
  key: fs.readFileSync('/certs/key.pem'),
  cert: fs.readFileSync('/certs/cert.pem'),
};

https.createServer(options, (req, res) => {
  let body = '';
  req.on('data', (chunk) => { body += chunk; });
  req.on('end', () => {
    const upstream = http.request(
      {
        host: '127.0.0.1',
        port: 8484,
        path: req.url,
        method: req.method,
        headers: {
          'content-type': 'text/plain',
          'content-length': Buffer.byteLength(body),
        },
      },
      (r) => {
        res.writeHead(r.statusCode, {
          'content-type': 'application/json',
          'access-control-allow-origin': '*',
        });
        r.pipe(res);
      }
    );
    upstream.on('error', () => {
      res.writeHead(502, { 'content-type': 'text/plain' });
      res.end('bad gateway');
    });
    upstream.end(body);
  });
}).listen(8444, '0.0.0.0', () => console.log('ml-metrics-proxy on 8444'));
