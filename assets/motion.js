/* ============================================================================
   SuiteSupports — shared motion (GSAP + ScrollTrigger + Lenis)
   Ported from the JK Legal sample: smooth scroll, word-cascade, scroll reveals,
   drawn gold line, stacking cards, magnetic buttons, header + mobile menu.
   Requires (loaded before this file):
     gsap, ScrollTrigger, Lenis  (via CDN)
   ============================================================================ */
(function () {
  var yEl = document.getElementById('year'); if (yEl) yEl.textContent = new Date().getFullYear();
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasGSAP = typeof gsap !== 'undefined';
  if (hasGSAP && typeof ScrollTrigger !== 'undefined') gsap.registerPlugin(ScrollTrigger);
  root.classList.add('js');

  function split(el, mode) {
    var words = el.textContent.trim().split(/\s+/);
    el.setAttribute('aria-label', el.textContent.trim());
    el.textContent = '';
    var inners = [];
    words.forEach(function (word, i) {
      var outer = document.createElement('span'); outer.setAttribute('aria-hidden', 'true');
      var clip = document.createElement('span'); clip.className = (mode === 'scrub' ? 'ws' : 'w');
      var wi = document.createElement('span'); wi.className = 'wi'; wi.textContent = word;
      clip.appendChild(wi); outer.appendChild(clip); el.appendChild(outer);
      if (i < words.length - 1) el.appendChild(document.createTextNode(' '));
      inners.push(wi);
    });
    return inners;
  }

  /* Lenis smooth scroll wired to GSAP ticker */
  var lenis = null;
  if (!reduce && typeof Lenis !== 'undefined') {
    lenis = new Lenis({ lerp: 0.09, smoothWheel: true });
    if (hasGSAP) {
      lenis.on('scroll', ScrollTrigger.update);
      gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
      gsap.ticker.lagSmoothing(0);
    } else {
      (function raf(t) { lenis.raf(t); requestAnimationFrame(raf); })(0);
    }
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]'); if (!a) return;
    var hash = a.getAttribute('href'); if (hash.length < 2) return;
    var target = document.querySelector(hash); if (!target) return;
    e.preventDefault();
    if (lenis) lenis.scrollTo(target, { offset: -88, duration: 1.3 });
    else target.scrollIntoView({ behavior: 'smooth' });
    var mm = document.querySelector('.mobile-menu'); if (mm) mm.classList.remove('open');
  });

  /* Header scrolled state + mobile menu (works with or without GSAP) */
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('scrolled', window.scrollY > 40); };
    onScroll(); window.addEventListener('scroll', onScroll, { passive: true });
    var burger = document.querySelector('.burger'), menu = document.querySelector('.mobile-menu');
    if (burger && menu) burger.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', open);
      header.classList.toggle('scrolled', open || window.scrollY > 40);
    });
  }

  if (!hasGSAP) { document.querySelectorAll('[data-reveal]').forEach(function (el) { el.style.opacity = 1; }); return; }

  /* SplitText cascade + scrub */
  document.querySelectorAll('.split-cascade').forEach(function (el) {
    var inners = split(el, 'cascade'); if (reduce) return;
    gsap.set(inners, { yPercent: 110 });
    var immediate = el.hasAttribute('data-immediate');
    var delay = parseFloat(el.getAttribute('data-delay') || '0');
    gsap.to(inners, { yPercent: 0, duration: 1.2, ease: 'power4.out', stagger: 0.045, delay: delay,
      scrollTrigger: immediate ? undefined : { trigger: el, start: 'top 88%', once: true } });
  });
  document.querySelectorAll('.split-scrub').forEach(function (el) {
    var inners = split(el, 'scrub'); if (reduce) return;
    gsap.set(inners, { opacity: 0.18 });
    gsap.to(inners, { opacity: 1, stagger: 0.05, ease: 'none',
      scrollTrigger: { trigger: el, start: 'top 80%', end: 'bottom 50%', scrub: 0.6 } });
  });

  /* Reveal: up / fade / mask / scale (+ optional stagger) */
  document.querySelectorAll('[data-reveal]').forEach(function (el) {
    if (reduce) { el.style.opacity = 1; return; }
    var variant = el.getAttribute('data-reveal') || 'up';
    var stagger = parseFloat(el.getAttribute('data-reveal-stagger') || '0');
    var delay = parseFloat(el.getAttribute('data-reveal-delay') || '0');
    var start = el.getAttribute('data-reveal-start') || 'top 86%';
    var targets = stagger ? el.children : el;
    if (stagger) el.style.opacity = 1;
    var from = variant === 'fade' ? { autoAlpha: 0 }
      : variant === 'mask' ? { clipPath: 'inset(100% 0 0 0)', autoAlpha: 1 }
      : variant === 'scale' ? { autoAlpha: 0, scale: 1.06 }
      : { autoAlpha: 0, y: 36 };
    var to = variant === 'mask' ? { clipPath: 'inset(0% 0 0 0)', autoAlpha: 1 } : { autoAlpha: 1, y: 0, scale: 1 };
    gsap.fromTo(targets, from, Object.assign({}, to, {
      duration: variant === 'mask' ? 1.3 : 1.1, ease: variant === 'mask' ? 'power4.inOut' : 'power3.out',
      stagger: stagger, delay: delay, scrollTrigger: { trigger: el, start: start, once: true } }));
  });

  /* HOME hero timeline + parallax + drawn gold line */
  (function () {
    var hero = document.querySelector('.hero'); if (!hero || reduce) return;
    var q = gsap.utils.selector(hero);
    gsap.timeline({ defaults: { ease: 'power3.out' } })
      .fromTo(q('.hero-img'), { scale: 1.18, autoAlpha: 0 }, { scale: 1.06, autoAlpha: 1, duration: 2.2, ease: 'power2.out' }, 0)
      .fromTo(q('.hero-line'), { strokeDashoffset: 1600 }, { strokeDashoffset: 0, duration: 2.4, ease: 'power3.inOut' }, 0.2)
      .fromTo(q('.hero-eyebrow'), { autoAlpha: 0, y: 14 }, { autoAlpha: 1, y: 0, duration: 0.9 }, 0.5)
      .fromTo(q('.hero-lede'), { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 1 }, 1.1)
      .fromTo(q('.hero-actions'), { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 1 }, 1.25)
      .fromTo(q('.hero-card'), { autoAlpha: 0, y: 40 }, { autoAlpha: 1, y: 0, duration: 1.1, stagger: 0.12 }, 1.35)
      .fromTo(q('.hero-scroll'), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.8 }, 1.8);
    gsap.to(q('.hero-img'), { yPercent: 18, ease: 'none', scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true } });
    gsap.to(q('.hero-copy'), { yPercent: -14, autoAlpha: 0.2, ease: 'none', scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true } });
    gsap.to(q('.hero-svg'), { yPercent: 10, ease: 'none', scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true } });
  })();

  /* INNER-PAGE hero: draw the gold line + fade copy + drift glows */
  (function () {
    var ph = document.querySelector('.page-hero'); if (!ph || reduce) return;
    var q = gsap.utils.selector(ph);
    gsap.timeline({ defaults: { ease: 'power3.out' } })
      .fromTo(q('.ph-line'), { strokeDashoffset: 1600 }, { strokeDashoffset: 0, duration: 2.4, ease: 'power3.inOut' }, 0.1)
      .fromTo(q('.eyebrow'), { autoAlpha: 0, y: 14 }, { autoAlpha: 1, y: 0, duration: 0.9 }, 0.35)
      .fromTo(q('.lede'), { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 1 }, 0.7);
    gsap.to(q('.ph-glow'), { yPercent: 12, ease: 'none', scrollTrigger: { trigger: ph, start: 'top top', end: 'bottom top', scrub: true } });
    gsap.to(q('.ph-svg'), { yPercent: 16, ease: 'none', scrollTrigger: { trigger: ph, start: 'top top', end: 'bottom top', scrub: true } });
  })();

  /* Stacking cards */
  document.querySelectorAll('.stack').forEach(function (el) {
    if (reduce) return;
    var cards = Array.prototype.slice.call(el.children);
    cards.forEach(function (card, i) {
      if (i === cards.length - 1) return;
      gsap.to(card, { scale: 0.93 - (cards.length - 2 - i) * 0.02, opacity: 0.5, filter: 'blur(2px)', ease: 'none',
        scrollTrigger: { trigger: cards[i + 1], start: 'top 92%', end: 'top 100px', scrub: true } });
    });
  });

  /* Parallax utility */
  document.querySelectorAll('[data-parallax]').forEach(function (el) {
    if (reduce) return;
    var speed = parseFloat(el.getAttribute('data-parallax') || '0.2');
    gsap.to(el, { yPercent: speed * 100, ease: 'none',
      scrollTrigger: { trigger: el.closest('section') || el, start: 'top bottom', end: 'bottom top', scrub: true } });
  });

  /* Magnetic buttons */
  if (!reduce && window.matchMedia('(hover:hover) and (pointer:fine)').matches) {
    document.querySelectorAll('.magnetic').forEach(function (el) {
      var xTo = gsap.quickTo(el, 'x', { duration: 0.5, ease: 'power3' });
      var yTo = gsap.quickTo(el, 'y', { duration: 0.5, ease: 'power3' });
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        xTo((e.clientX - (r.left + r.width / 2)) * 0.22); yTo((e.clientY - (r.top + r.height / 2)) * 0.3);
      });
      el.addEventListener('pointerleave', function () { xTo(0); yTo(0); });
    });
  }
})();

/* Animated code screens: lines "type" themselves in a loop (PMS card). */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function init() {
    document.querySelectorAll('.code-screen').forEach(function (cs) {
      var lines = Array.prototype.slice.call(cs.querySelectorAll('.cl'));
      if (!lines.length) return;
      if (reduce || typeof gsap === 'undefined') {
        lines.forEach(function (l) { var c = l.querySelector('.clip'); if (c) c.style.width = 'auto'; });
        return;
      }
      var widths = lines.map(function (l) {
        var clip = l.querySelector('.clip');
        clip.style.width = 'auto';
        var w = clip.getBoundingClientRect().width;
        clip.style.width = '0px';
        return w;
      });
      var tl = gsap.timeline({ repeat: -1, repeatDelay: 0.5,
        scrollTrigger: { trigger: cs, start: 'top 92%' } });
      lines.forEach(function (l, i) {
        var clip = l.querySelector('.clip'), caret = l.querySelector('.ccaret');
        var chars = Math.max(6, clip.textContent.length);
        tl.set(caret, { visibility: 'visible' })
          .to(clip, { width: widths[i], duration: chars * 0.045, ease: 'steps(' + chars + ')' })
          .set(caret, { visibility: 'hidden' }, '+=0.22');
      });
      tl.to({}, { duration: 2.6 });                                   /* hold on the finished screen */
      tl.set(lines.map(function (l) { return l.querySelector('.clip'); }), { width: 0 });
    });
  }
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(init); }
  else { window.addEventListener('load', init); }
})();

/* Hologram booking widget + guest chat animations (homepage cards). */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (typeof gsap === 'undefined') return;

  /* Hologram: fields materialize, confirm button glows; card floats on its beam. */
  document.querySelectorAll('.holo-screen').forEach(function (hs) {
    var wrap = hs.querySelector('.holo-wrap');
    var rows = hs.querySelectorAll('.holo-row');
    var btn = hs.querySelector('.holo-btn');
    if (reduce) { rows.forEach(function (r) { r.style.opacity = 1; }); if (btn) btn.style.opacity = 1; return; }
    gsap.to(wrap, { y: 7, duration: 2.8, yoyo: true, repeat: -1, ease: 'sine.inOut' });
    var tl = gsap.timeline({ repeat: -1, repeatDelay: 0.4,
      scrollTrigger: { trigger: hs, start: 'top 92%' } });
    tl.set([rows, btn], { autoAlpha: 0, y: 6 })
      .to(rows, { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.3, ease: 'power2.out' }, 0.2)
      .to(btn, { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '+=0.25')
      .to({}, { duration: 2.8 })
      .to([rows, btn], { autoAlpha: 0, duration: 0.45 });
  });

  /* Chat: bubbles pop in; hotel replies show typing dots first. */
  document.querySelectorAll('.chat-screen').forEach(function (cs) {
    var msgs = Array.prototype.slice.call(cs.querySelectorAll('.msg'));
    if (reduce) {
      msgs.forEach(function (m) {
        m.style.opacity = 1;
        var d = m.querySelector('.dots'), t = m.querySelector('.txt');
        if (d) d.style.display = 'none'; if (t) t.style.display = 'inline';
      });
      return;
    }
    var tl = gsap.timeline({ repeat: -1, repeatDelay: 0.6,
      scrollTrigger: { trigger: cs, start: 'top 92%' } });
    tl.set(msgs, { autoAlpha: 0, y: 10, scale: 0.96 });
    msgs.forEach(function (m) {
      var dots = m.querySelector('.dots'), txt = m.querySelector('.txt');
      if (dots && txt) tl.set(dots, { display: 'inline-flex' }).set(txt, { display: 'none' });
    });
    msgs.forEach(function (m, i) {
      var dots = m.querySelector('.dots'), txt = m.querySelector('.txt');
      tl.to(m, { autoAlpha: 1, y: 0, scale: 1, duration: 0.4, ease: 'back.out(1.6)' }, i === 0 ? 0.2 : '+=0.45');
      if (dots && txt) {
        tl.set(dots, { display: 'none' }, '+=0.95').set(txt, { display: 'inline' });
      }
    });
    tl.to({}, { duration: 2.6 })
      .to(msgs, { autoAlpha: 0, duration: 0.4, stagger: 0.04 });
  });
})();

/* Three-device showcase: each screen "builds" itself — desktop, then tablet, then phone. */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (typeof gsap === 'undefined') return;
  document.querySelectorAll('.devices-screen').forEach(function (ds) {
    var devs = ['.dev-mac', '.dev-pad', '.dev-phone'].map(function (s) { return ds.querySelector(s); }).filter(Boolean);
    if (reduce) {
      ds.querySelectorAll('.m-line').forEach(function (l) { l.style.width = '55%'; });
      ds.querySelectorAll('.m-bar,.m-block').forEach(function (e) { e.style.opacity = 1; });
      return;
    }
    gsap.to(ds.querySelector('.dev-pad'), { y: 5, duration: 3.1, yoyo: true, repeat: -1, ease: 'sine.inOut' });
    gsap.to(ds.querySelector('.dev-phone'), { y: 7, duration: 2.5, yoyo: true, repeat: -1, ease: 'sine.inOut' });
    var tl = gsap.timeline({ repeat: -1, repeatDelay: 0.4,
      scrollTrigger: { trigger: ds, start: 'top 92%' } });
    devs.forEach(function (dev, i) {
      var line = dev.querySelector('.m-line'), bars = dev.querySelectorAll('.m-bar'), blocks = dev.querySelectorAll('.m-block');
      var at = i === 0 ? 0.2 : '-=0.55';
      tl.set(line, { width: 0, autoAlpha: 1 }, i === 0 ? 0 : '<')
        .set([bars, blocks], { autoAlpha: 0, y: 4 }, '<');
      tl.to(line, { width: '55%', duration: 0.5, ease: 'power2.out' }, at)
        .to(bars, { autoAlpha: 1, y: 0, duration: 0.35, stagger: 0.12 }, '-=0.15')
        .to(blocks, { autoAlpha: 1, y: 0, duration: 0.3, stagger: 0.07 }, '-=0.1');
    });
    tl.to({}, { duration: 2.8 });
    tl.to(ds.querySelectorAll('.m-line,.m-bar,.m-block'), { autoAlpha: 0, duration: 0.4 });
  });
})();
