/* VIDAA patch for the open-source Moonlight WebRTC client.
   - force fullscreen when the video appears
   - accept VIDAA back keys (app.js also handles these directly)
   - log decoded/received FPS to the existing TubeTV metrics proxy
*/
(function () {
  'use strict';

  var video = document.getElementById('video');
  var pcs = [];
  var Orig = window.RTCPeerConnection;

  if (Orig) {
    window.RTCPeerConnection = function () {
      var pc = new Orig(...arguments);
      pcs.push(pc);
      return pc;
    };
    window.RTCPeerConnection.prototype = Orig.prototype;
    try { Object.keys(Orig).forEach(function (k) { window.RTCPeerConnection[k] = Orig[k]; }); } catch (e) {}
  }

  function fullscreen() {
    try {
      if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
        var p = document.documentElement.requestFullscreen();
        if (p && p.catch) { p.catch(function () {}); }
      }
    } catch (e) {}
  }

  if (video) {
    video.setAttribute('playsinline', '');
    if (window.MutationObserver) {
      new MutationObserver(function () {
        if (!video.hidden) { fullscreen(); }
      }).observe(video, { attributes: true, attributeFilter: ['hidden'] });
    }
  }

  function post(o) {
    try {
      if (window.fetch) {
        window.fetch('https://moonlight.joaopacheco.me:8444/api/log', {
          method: 'POST',
          body: 'MLOWN ' + JSON.stringify(o),
          mode: 'no-cors',
          keepalive: true
        });
      }
    } catch (e) {}
  }

  var lastDec = 0;
  var lastVTotal = 0;
  var lastTime = Date.now();

  setInterval(function () {
    if (!pcs.length || !video || video.hidden) { return; }
    pcs.forEach(function (pc) {
      if (!pc.getStats) { return; }
      pc.getStats().then(function (rep) {
        var o = {};
        rep.forEach(function (r) {
          if (r.type === 'inbound-rtp' && (r.kind === 'video' || r.mediaType === 'video')) {
            o.dec = Math.round(r.framesDecoded || 0);
            o.recv = Math.round(r.framesReceived || 0);
            o.lost = Math.round(r.packetsLost || 0);
            o.wh = (r.frameWidth || r.width || 0) + 'x' + (r.frameHeight || r.height || 0);
          }
        });
        var now = Date.now();
        var dt = now - lastTime;
        if (o.dec !== undefined && dt > 0) {
          o.decFps = Math.round((o.dec - lastDec) * 1000 / dt);
        }
        if (video.getVideoPlaybackQuality) {
          var q = video.getVideoPlaybackQuality();
          o.vTotal = q.totalVideoFrames;
          o.vDrop = q.droppedVideoFrames;
          if (dt > 0) { o.vFps = Math.round((q.totalVideoFrames - lastVTotal) * 1000 / dt); }
          lastVTotal = q.totalVideoFrames;
        }
        lastDec = o.dec || 0;
        lastTime = now;
        o.ready = video.readyState;
        o.paused = video.paused ? 1 : 0;
        post(o);
      }).catch(function () {});
    });
  }, 4000);
}());
