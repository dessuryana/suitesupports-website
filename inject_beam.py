import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('about-us.html', 'r', encoding='utf-8') as f:
    c = f.read()

# ── 1. Add setTimeout trigger inside the second rAF ──────────────────────────
OLD_RAF = (
    "        chars.forEach(function(s, i) {\n"
    "          var delay = i * 28 + Math.random() * 500;\n"
    "          var dur   = 8000 + Math.random() * 2000;\n"
    "          s.style.transition = 'transform ' + dur + 'ms cubic-bezier(0.16,1,0.3,1) ' + delay + 'ms';\n"
    "          s.style.transform  = 'translate(0,0)';\n"
    "        });\n"
    "      });\n"
    "    });\n"
    "  });"
)

NEW_RAF = (
    "        chars.forEach(function(s, i) {\n"
    "          var delay = i * 28 + Math.random() * 500;\n"
    "          var dur   = 8000 + Math.random() * 2000;\n"
    "          s.style.transition = 'transform ' + dur + 'ms cubic-bezier(0.16,1,0.3,1) ' + delay + 'ms';\n"
    "          s.style.transform  = 'translate(0,0)';\n"
    "        });\n"
    "        // Fire beam after all chars have settled\n"
    "        setTimeout(startBeamAnimation, 12500);\n"
    "      });\n"
    "    });\n"
    "  });"
)

if OLD_RAF in c:
    c = c.replace(OLD_RAF, NEW_RAF, 1)
    print('Trigger injected: OK')
else:
    print('ERROR: trigger pattern not found')

# ── 2. Build the beam function string ────────────────────────────────────────
BEAM_FN = r"""
  // ── GLOWING BEAM ANIMATION ────────────────────────────────────────────────
  // Path: B(Built) -> G(Get Started) -> S(SuiteSupports) -> C(Core Service Pillars) -> B
  function startBeamAnimation() {
    var bEl = document.querySelector('.hero-title .sc');
    var gEl = document.querySelector('.nav-cta');
    var sEl = document.querySelector('.nav-logo-text');
    var cEl = (function() {
      var all = document.querySelectorAll('.hero-stat-label');
      for (var i = 0; i < all.length; i++) {
        if (all[i].textContent.indexOf('Core') !== -1) return all[i];
      }
      return null;
    })();
    if (!bEl || !gEl || !sEl || !cEl) return;

    // Fixed canvas over page
    var cv = document.createElement('canvas');
    cv.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:997;';
    cv.width  = window.innerWidth;
    cv.height = window.innerHeight;
    document.body.appendChild(cv);
    var ctx = cv.getContext('2d');
    window.addEventListener('resize', function() {
      cv.width  = window.innerWidth;
      cv.height = window.innerHeight;
    }, { passive: true });

    function ctr(el) {
      var r = el.getBoundingClientRect();
      return { x: r.left + r.width * 0.5, y: r.top + r.height * 0.5 };
    }

    function buildPath(pts) {
      var segs = [], tot = 0;
      for (var i = 0; i < pts.length; i++) {
        var a = pts[i], b = pts[(i + 1) % pts.length];
        var dx = b.x - a.x, dy = b.y - a.y;
        var len = Math.sqrt(dx * dx + dy * dy);
        segs.push({ ax: a.x, ay: a.y, bx: b.x, by: b.y, len: len, start: tot });
        tot += len;
      }
      return { segs: segs, total: tot };
    }

    function posAt(path, d) {
      var tot = path.total;
      d = ((d % tot) + tot) % tot;
      for (var i = 0; i < path.segs.length; i++) {
        var s = path.segs[i];
        if (d < s.start + s.len) {
          var t = (d - s.start) / s.len;
          return { x: s.ax + t * (s.bx - s.ax), y: s.ay + t * (s.by - s.ay) };
        }
      }
      return { x: path.segs[0].ax, y: path.segs[0].ay };
    }

    var SPEED   = 220;   // px / s
    var TAIL    = 220;   // px of active bright tail
    var FADE_MS = 2800;  // ms for historical trail to fade
    var STEPS   = 55;    // subdivisions for tail gradient

    var dist    = 0;
    var prevTs  = 0;
    var history = [];    // { x, y, t }

    function frame(ts) {
      var dt = prevTs ? Math.min((ts - prevTs) / 1000, 0.05) : 0;
      prevTs = ts;
      dist  += SPEED * dt;

      var pts  = [ctr(bEl), ctr(gEl), ctr(sEl), ctr(cEl)];
      var path = buildPath(pts);
      var head = posAt(path, dist);

      history.push({ x: head.x, y: head.y, t: ts });
      while (history.length && ts - history[0].t > FADE_MS) history.shift();

      ctx.clearRect(0, 0, cv.width, cv.height);

      // Fading trail - glow that lingers after beam passes
      for (var i = 1; i < history.length; i++) {
        var p0 = history[i - 1], p1 = history[i];
        var age = (ts - p1.t) / FADE_MS;
        if (age >= 1) continue;
        var f = 1 - age;
        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.lineTo(p1.x, p1.y);
        ctx.strokeStyle = 'rgba(212,164,39,' + (f * 0.55) + ')';
        ctx.lineWidth   = f * 2 + 0.5;
        ctx.lineCap     = 'round';
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.lineTo(p1.x, p1.y);
        ctx.strokeStyle = 'rgba(255,200,80,' + (f * 0.15) + ')';
        ctx.lineWidth   = f * 8;
        ctx.stroke();
      }

      // Active bright tail
      for (var i = 0; i < STEPS; i++) {
        var d1 = dist - TAIL + (i / STEPS) * TAIL;
        var d2 = dist - TAIL + ((i + 1) / STEPS) * TAIL;
        var t  = (i + 1) / STEPS;
        var tt = t * t;
        var p1 = posAt(path, d1);
        var p2 = posAt(path, d2);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = 'rgba(236,200,74,' + (tt * 0.95) + ')';
        ctx.lineWidth   = 1 + tt * 4.5;
        ctx.lineCap     = 'round';
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = 'rgba(255,230,130,' + (tt * 0.28) + ')';
        ctx.lineWidth   = 5 + tt * 18;
        ctx.stroke();
      }

      // Beam head - large bright missile tip
      var aura = ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, 44);
      aura.addColorStop(0,    'rgba(255,255,210,0.88)');
      aura.addColorStop(0.18, 'rgba(255,210,60,0.70)');
      aura.addColorStop(0.45, 'rgba(212,164,39,0.28)');
      aura.addColorStop(1,    'rgba(212,164,39,0)');
      ctx.beginPath();
      ctx.arc(head.x, head.y, 44, 0, Math.PI * 2);
      ctx.fillStyle = aura;
      ctx.fill();

      var core = ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, 13);
      core.addColorStop(0,    'rgba(255,255,255,1)');
      core.addColorStop(0.35, 'rgba(255,248,200,0.95)');
      core.addColorStop(0.75, 'rgba(236,200,74,0.5)');
      core.addColorStop(1,    'rgba(212,164,39,0)');
      ctx.beginPath();
      ctx.arc(head.x, head.y, 13, 0, Math.PI * 2);
      ctx.fillStyle = core;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(head.x, head.y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.98)';
      ctx.fill();

      requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
  }

"""

if '  // Add star ratings to testimonials' in c:
    c = c.replace('  // Add star ratings to testimonials', BEAM_FN + '  // Add star ratings to testimonials', 1)
    print('Beam function inserted: OK')
else:
    print('ERROR: insertion point not found')

with open('about-us.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('File written.')
