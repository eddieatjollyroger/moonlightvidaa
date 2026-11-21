/* TV-safe WebCodecs probe: never let isConfigSupported throw. */
(function () {
  try {
    if (typeof window !== 'undefined' && window.VideoDecoder &&
        typeof VideoDecoder.isConfigSupported === 'function') {
      var orig = VideoDecoder.isConfigSupported;
      try {
        VideoDecoder.isConfigSupported = function (c) {
          try {
            return Promise.resolve(orig.call(VideoDecoder, c)).catch(function () {
              return { supported: false };
            });
          } catch (e) {
            return Promise.resolve({ supported: false });
          }
        };
      } catch (e) {}
    }
  } catch (e) {}
})();
