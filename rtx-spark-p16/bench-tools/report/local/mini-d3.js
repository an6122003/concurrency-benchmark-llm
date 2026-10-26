// A small stand-in for the parts of d3 v7 the report's charts use (selections, linear/point/log
// scales, line paths, max/extent, ',' format, pointer), so the offline report needs no network.
(() => {
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const value = (v, n, i) => (typeof v === 'function' ? v.call(n, n.__data__, i) : v);
  const make = (parent, tag) => (tag === 'svg' || parent.namespaceURI === SVG_NS
    ? document.createElementNS(SVG_NS, tag) : document.createElement(tag));

  class Selection {
    constructor(nodes) { this.nodes = nodes; }
    append(tag) {
      return new Selection(this.nodes.map((n) => {
        const child = make(n, tag);
        if (n.__data__ !== undefined) child.__data__ = n.__data__;
        n.appendChild(child);
        return child;
      }));
    }
    attr(name, v) {
      this.nodes.forEach((n, i) => {
        const val = value(v, n, i);
        if (val == null) n.removeAttribute(name);
        else n.setAttribute(name, val);
      });
      return this;
    }
    style(name, v) {
      this.nodes.forEach((n, i) => {
        const val = value(v, n, i);
        if (val == null) n.style.removeProperty(name);
        else n.style.setProperty(name, String(val));
      });
      return this;
    }
    text(t) { this.nodes.forEach((n, i) => { n.textContent = value(t, n, i); }); return this; }
    classed(name, on) { this.nodes.forEach((n) => n.classList.toggle(name, !!on)); return this; }
    on(type, fn) { this.nodes.forEach((n) => n.addEventListener(type, (e) => fn.call(n, e, n.__data__))); return this; }
    each(fn) { this.nodes.forEach((n, i) => fn.call(n, n.__data__, i)); return this; }
    node() { return this.nodes[0] || null; }
    remove() { this.nodes.forEach((n) => n.remove()); return this; }
    // Only the enter pattern the charts use: selectAll(null).data(rows).join(tag).
    selectAll() {
      const parent = this.nodes[0];
      return {
        data(rows) {
          return {
            join(tag) {
              return new Selection(rows.map((d) => {
                const child = make(parent, tag);
                child.__data__ = d;
                parent.appendChild(child);
                return child;
              }));
            },
          };
        },
      };
    }
  }

  function tickStep(start, stop, count) {
    const step0 = Math.abs(stop - start) / Math.max(1, count);
    let step = 10 ** Math.floor(Math.log10(step0 || 1));
    const error = step0 / step;
    if (error >= Math.sqrt(50)) step *= 10;
    else if (error >= Math.sqrt(10)) step *= 5;
    else if (error >= Math.sqrt(2)) step *= 2;
    return step;
  }

  function scaleLinear(domain, range) {
    let [d0, d1] = domain.map(Number);
    const [r0, r1] = range;
    const s = (v) => r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);
    s.nice = (count = 10) => {
      for (let k = 0; k < 3; k++) {
        const step = tickStep(d0, d1, count);
        d0 = Math.floor(d0 / step) * step;
        d1 = Math.ceil(d1 / step) * step;
      }
      return s;
    };
    s.ticks = (count = 10) => {
      const step = tickStep(d0, d1, count);
      const out = [];
      for (let i = Math.ceil(d0 / step); i <= Math.floor(d1 / step); i++) out.push(+(i * step).toFixed(10));
      return out;
    };
    s.domain = () => [d0, d1];
    return s;
  }

  function scalePoint(domain, range) {
    const [r0, r1] = range;
    const n = domain.length;
    return (v) => {
      const i = domain.indexOf(v);
      if (i < 0) return undefined;
      return n > 1 ? r0 + (i * (r1 - r0)) / (n - 1) : (r0 + r1) / 2;
    };
  }

  function scaleLog(domain, range) {
    const [l0, l1] = domain.map((d) => Math.log(d));
    const [r0, r1] = range;
    const s = (v) => r0 + ((Math.log(v) - l0) / (l1 - l0 || 1)) * (r1 - r0);
    s.base = () => s;
    return s;
  }

  function line() {
    let fx = (d) => d[0];
    let fy = (d) => d[1];
    const path = (pts) => pts.map((p, i) => `${i ? 'L' : 'M'}${fx(p, i)},${fy(p, i)}`).join('');
    path.x = (f) => { fx = f; return path; };
    path.y = (f) => { fy = f; return path; };
    return path;
  }

  function max(rows, f) {
    let m;
    rows.forEach((d, i) => {
      const v = f ? f(d, i) : d;
      if (v != null && !Number.isNaN(+v) && (m === undefined || +v > m)) m = +v;
    });
    return m;
  }

  function extent(rows) {
    const v = rows.filter((x) => x != null && !Number.isNaN(+x)).map(Number);
    return v.length ? [Math.min(...v), Math.max(...v)] : [undefined, undefined];
  }

  const format = () => (v) => Number(v).toLocaleString('en-US', { maximumFractionDigits: 12 });

  function pointer(event, target) {
    const svg = target.ownerSVGElement || (target.tagName === 'svg' ? target : null);
    if (svg) {
      const pt = svg.createSVGPoint();
      pt.x = event.clientX;
      pt.y = event.clientY;
      const p = pt.matrixTransform(target.getScreenCTM().inverse());
      return [p.x, p.y];
    }
    const rect = target.getBoundingClientRect();
    return [event.clientX - rect.left - target.clientLeft, event.clientY - rect.top - target.clientTop];
  }

  window.d3 = { select: (n) => new Selection([n]), scaleLinear, scalePoint, scaleLog, line, max, extent, format, pointer };
})();
