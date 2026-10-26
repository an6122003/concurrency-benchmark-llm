/* The film's own clock. setTimeout runs on video time, so the chip's delayed effects land on the
   same frame in every render, however long a frame takes to capture. */
(function () {
  'use strict';
  const queue = [];
  let now = 0, seq = 0;
  window.setTimeout = function (fn, ms) {
    const id = ++seq;
    queue.push({id, at: now + (Number(ms) || 0) / 1000, fn});
    return id;
  };
  window.clearTimeout = function (id) {
    const i = queue.findIndex(j => j.id === id);
    if (i >= 0) queue.splice(i, 1);
  };
  window.VT = {
    advanceTo(t) {  // run every timer that is due, earliest first
      now = t;
      for (;;) {
        let k = -1;
        for (let i = 0; i < queue.length; i++) if (queue[i].at <= t && (k < 0 || queue[i].at < queue[k].at)) k = i;
        if (k < 0) break;
        queue.splice(k, 1)[0].fn();
      }
    },
    get now() { return now; },
  };
})();
