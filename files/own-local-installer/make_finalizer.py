"""Generate the TV-side finalizer that builds the English packed bundle in place.

The bridge cannot create directories, and the metrics log only keeps the last
250 lines, so the full packed wrapper is not exported to the Mac. Instead this
page reads the existing packed clone on the TV, replaces only the moonlight
base64 blob, and writes one flat file with fileWrite.
"""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import translate_app  # noqa: E402

SRC_PACKED = ROOT / "backup" / "ownmoon-local.html"
SRC_EN = ROOT / "backup" / "ownmoon-en.html"
OUT = HERE / "finalize-english.html"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def js_string(value):
    return json.dumps(value, ensure_ascii=False)


def main():
    src_hash = sha(SRC_PACKED)
    en_hash = sha(SRC_EN)
    pairs_js = json.dumps(translate_app.PAIRS, ensure_ascii=False, indent=2)
    leftovers = [
        "Il tuo", "sulla TV", "trasmette", "porta ", "Indirizzo", "Connetti",
        "Riconnetti", "Cancella", "In attesa", "Qualità", "Preparazione",
        "Connessione", "Connesso", "Non connesso", "Disconnesso", "Verifica",
        "Accoppiamento", "Nuovo PIN", "Annulla", "scade", "(applicazioni)",
        "applicazioni", "Avvio", "In diretta", "Chiusura", "Rete ", "persi",
        "Indirizzo non valido", "Sidee+",
    ]

    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Finalize English Packed Bundle</title>
<style>
body{background:#111;color:#eee;font:17px sans-serif;margin:20px}
h1{font-size:26px}button{font:16px sans-serif;margin:3px 4px;padding:7px 10px}
pre{white-space:pre-wrap;word-break:break-all;background:#000;padding:16px;min-height:180px}
.ok{color:#7f7}.bad{color:#f77}.warn{color:#fc3}
</style>
</head>
<body>
<h1>FINALIZE ENGLISH PACKED BUNDLE</h1>
<p>READS THE WORKING PACKED CLONE. REPLACES ONLY THE MOONLIGHT BLOB. WRITES ONE FLAT FILE.</p>
<div>
<button id="build">1 BUILD + WRITE</button>
<button id="verify">2 VERIFY DEST</button>
</div>
<pre id="out">READY</pre>
<script>
var SRC='emanual/Local_ebook/ownmoon-local.html';
var DEST='emanual/Local_ebook/ownmoon-en-packed.html';
var SRC_SHA=__SRC_SHA__;
var EN_SHA=__EN_SHA__;
var PAIRS=__PAIRS__;
var LEFTOVER=__LEFTOVER__;

function out(s,cls){var d=document.createElement('div');if(cls)d.className=cls;d.textContent=s;document.getElementById('out').appendChild(d);return d;}
function clear(){document.getElementById('out').textContent='';}
function ok(s){out('OK '+s,'ok');}
function bad(s){out('FAIL '+s,'bad');}
function warn(s){out('NOTE '+s,'warn');}
function call(api,params){
  if(typeof HiUtils_createRequest!=='function')throw new Error('HIUTILS MISSING');
  return HiUtils_createRequest(api,params);
}
function isOk(r){return !!(r&&r.ret);}
function body(r){return (r&&typeof r.msg==='string')?r.msg:null;}
function read(path){
  var r=call('fileRead',{path:path,mode:6});
  if(!isOk(r))throw new Error('READ '+path+' '+JSON.stringify(r).slice(0,250));
  var t=body(r);if(t===null)throw new Error('NO BODY '+path);
  return t;
}
function write(path,text){
  var r=call('fileWrite',{path:path,mode:6,writedata:text});
  if(!isOk(r))throw new Error('WRITE '+path+' '+JSON.stringify(r).slice(0,250));
}
function byteLen(text){return new TextEncoder().encode(text).length;}
function b64ToBytes(s){
  var bin=atob(String(s));
  var a=new Uint8Array(bin.length);
  for(var i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);
  return a;
}
function bytesToB64(bytes){
  var bin='',step=8192;
  for(var i=0;i<bytes.length;i+=step)bin+=String.fromCharCode.apply(null,bytes.subarray(i,i+step));
  return btoa(bin);
}
async function gunzip(bytes){
  if(typeof DecompressionStream==='undefined')throw new Error('NO DECOMPRESSIONSTREAM');
  var stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}
async function gzip(bytes){
  if(typeof CompressionStream==='undefined')throw new Error('NO COMPRESSIONSTREAM');
  var stream=new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}
async function shaBytes(bytes){
  if(!window.crypto||!crypto.subtle)throw new Error('NO SUBTLECRYPTO');
  var buf=await crypto.subtle.digest('SHA-256',bytes);
  var arr=new Uint8Array(buf),hex='';
  for(var i=0;i<arr.length;i++)hex+=('0'+arr[i].toString(16)).slice(-2);
  return hex;
}
function findBlob(text){
  var marker='"moonlight":"';
  var m=text.indexOf(marker);
  if(m<0)throw new Error('NO MOONLIGHT BLOB');
  var start=m+marker.length;
  var end=text.indexOf('"',start);
  if(end<0)throw new Error('UNCLOSED MOONLIGHT BLOB');
  return {start:start,end:end,old:text.slice(start,end)};
}
function translate(text){
  for(var i=0;i<PAIRS.length;i++){
    var p=PAIRS[i];
    if(text.indexOf(p[0])>=0)text=text.split(p[0]).join(p[1]);
  }
  var left=[];
  for(var j=0;j<LEFTOVER.length;j++)if(text.indexOf(LEFTOVER[j])>=0)left.push(LEFTOVER[j]);
  if(left.length)throw new Error('ITALIAN LEFT '+left.join(','));
  return text;
}

document.getElementById('build').addEventListener('click',async function(){
  clear();
  try{
    var wrapper=read(SRC);
    out('READ PACKED '+byteLen(wrapper)+' BYTES','warn');
    var loc=findBlob(wrapper);
    out('BLOB CHARS '+(loc.end-loc.start),'warn');

    var raw=await gunzip(b64ToBytes(loc.old));
    var srcText=new TextDecoder('utf-8',{fatal:true}).decode(raw);
    var srcHash=await shaBytes(raw);
    if(srcHash!==SRC_SHA)throw new Error('SOURCE SHA '+srcHash+' != '+SRC_SHA);
    ok('SOURCE SHA OK '+srcHash);

    var enText=translate(srcText);
    var enBytes=new TextEncoder().encode(enText);
    var enHash=await shaBytes(enBytes);
    if(enHash!==EN_SHA)throw new Error('ENGLISH SHA '+enHash+' != '+EN_SHA);
    ok('ENGLISH SHA OK '+enHash);
    ok('ENGLISH BYTES '+enBytes.length);

    var newBlob=bytesToB64(await gzip(enBytes));
    var finalText=wrapper.slice(0,loc.start)+newBlob+wrapper.slice(loc.end);
    if(finalText.indexOf('"moonlight":"'+newBlob+'"')<0)throw new Error('REPLACE CHECK FAILED');
    if(finalText.indexOf('"emu":"')<0)throw new Error('EMU BLOB MISSING');
    out('FINAL CHARS '+finalText.length,'warn');

    write(DEST,finalText);
    var check=read(DEST);
    if(check!==finalText)throw new Error('READBACK MISMATCH');
    var finalHash=await shaBytes(new TextEncoder().encode(check));
    ok('FILE WRITTEN '+byteLen(check)+' BYTES');
    ok('SHA '+finalHash);
    warn('NEXT: PATCH INSTALLER TILE URL THEN REPOINT');
  }catch(e){bad(e.message);}
});

document.getElementById('verify').addEventListener('click',async function(){
  clear();
  try{
    var t=read(DEST);
    ok('BYTES '+byteLen(t));
    ok('SHA '+await shaBytes(new TextEncoder().encode(t)));
    if(t.indexOf('"moonlight":"')<0||t.indexOf('"emu":"')<0)throw new Error('NOT A PACKED WRAPPER');
    ok('PACKED MARKERS OK');
  }catch(e){bad(e.message);}
});
</script>
</body>
</html>
"""
    html = (html.replace("__SRC_SHA__", js_string(src_hash))
                .replace("__EN_SHA__", js_string(en_hash))
                .replace("__PAIRS__", pairs_js)
                .replace("__LEFTOVER__", js_string(leftovers)))
    OUT.write_text(html, encoding="utf-8")
    print("wrote", OUT, len(html.encode("utf-8")), "bytes")
    print("src", src_hash)
    print("en", en_hash)


if __name__ == "__main__":
    main()
