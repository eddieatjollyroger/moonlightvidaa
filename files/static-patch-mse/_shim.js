/* Force the Media Source fallback on VIDAA Chrome 111.
   WebCodecs is present but its decoder path fails on this TV, so remove it
   before the frontend queries pipe capabilities. The app then selects the
   built-in h264 MediaSource decoder (higher latency, but it works). */
(function () {
  try {
    if (typeof window !== 'undefined' && window.VideoDecoder) {
      delete window.VideoDecoder;
    }
  } catch (e) {
    try { window.VideoDecoder = undefined; } catch (e2) {}
  }
})();
