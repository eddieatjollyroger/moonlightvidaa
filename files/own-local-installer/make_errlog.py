"""Add startup error logging + before/after markers to the full JS9 bundle."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = (HERE / "ladder-js9.html").read_text(encoding="utf-8")

START = '<script>\nconst GATEWAY_PROTOCOL_VERSION = 1;'
if START not in BASE:
    raise SystemExit("app.js script start not found")

idx = BASE.index(START)
before = BASE[:idx]
rest = BASE[idx:]
end = rest.index("</script>") + len("</script>")
app_block = rest[:end]
after = rest[end:]

BEFORE = """<script>
(function () {
  var L = 'https://moonlight.joaopacheco.me:8444/api/log';
  function p(s) {
    try { fetch(L, {method:'POST', body:'MLDBG ' + s, mode:'no-cors', keepalive:true}); } catch (e) {}
  }
  window.onerror = function (m, s, l, c, e) {
    p('ONERROR ' + m + ' @' + l + ':' + c + (e && e.stack ? ' STACK ' + e.stack : ''));
  };
  window.addEventListener('error', function (e) {
    p('ERREV ' + (e.message || '') + ' ' + (e.filename || '') + ':' + e.lineno);
  }, true);
  window.addEventListener('unhandledrejection', function (e) {
    p('REJECT ' + String(e.reason && e.reason.message ? e.reason.message : e.reason));
  });
  p('BEFORE APP');
}());
</script>
"""

AFTER = """<script>
(function () {
  var L = 'https://moonlight.joaopacheco.me:8444/api/log';
  try { fetch(L, {method:'POST', body:'MLDBG AFTER APP', mode:'no-cors', keepalive:true}); } catch (e) {}
}());
</script>
"""

out = before + BEFORE + app_block + AFTER + after
name = "ladder-js9-errlog.html"
(HERE / name).write_text(out, encoding="utf-8")
print("wrote", name, len(out.encode("utf-8")), "bytes")
