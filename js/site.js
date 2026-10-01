/* Twenty4 — motion.
   One rAF loop drives everything continuous (dial, pointer, scroll scenes) and
   only runs while something on screen needs it. Intro and one-shot reveals are CSS. */
(function () {
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = matchMedia('(pointer: fine)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var ease = function (t) { return 1 - Math.pow(1 - t, 3); };
  var inOut = function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };

  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ---------- Clock: blue steps round the 24 markers, once a minute (2.5s each) ---------- */
  var clock = $('[data-clock]');
  var ticks = $$('.tick');
  var fmt = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Guernsey', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' });
  var lastStep = -1, stepReady = false;
  function readClock() {
    var o = {};
    fmt.formatToParts(new Date()).forEach(function (x) { o[x.type] = x.value; });
    if (clock) clock.textContent = o.hour + ':' + o.minute + ' Guernsey';
    if (!stepReady || !ticks.length) return;
    var step = Math.floor(((+o.second) * 1000 + Date.now() % 1000) / 2500) % 24;
    if (step === lastStep) return;
    lastStep = step;
    ticks.forEach(function (l) { l.classList.remove('sec', 'trail-1'); });
    ticks[step].classList.add('sec');
    ticks[(step + 23) % 24].classList.add('trail-1');
  }
  readClock();
  setInterval(readClock, 100);
  setTimeout(function () { stepReady = true; readClock(); }, 2300); // first light after the intro

  /* ---------- Smooth scroll: a light, Lenis-style glide on wheel and trackpad only ----------
     Keyboard, scrollbar and touch stay native; anchors glide too. Off for reduced motion and touch. */
  if (!reduce && fine) (function () {
    var target = scrollY, current = scrollY, running = false, ours = false;
    var max = function () { return document.documentElement.scrollHeight - innerHeight; };
    function tick() {
      current += (target - current) * 0.11;
      if (Math.abs(target - current) < 0.4) current = target;
      ours = true; window.scrollTo(0, current);
      running = current !== target; if (running) requestAnimationFrame(tick);
    }
    addEventListener('wheel', function (e) {
      if (document.documentElement.classList.contains('gated')) { e.preventDefault(); return; } // behind the preview gate
      if (e.ctrlKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;           // pinch-zoom and sideways gestures stay native
      e.preventDefault();
      var d = e.deltaMode === 1 ? e.deltaY * 32 : e.deltaY;
      target = clamp(target + d, 0, max());
      if (!running) { running = true; requestAnimationFrame(tick); }
    }, { passive: false });
    addEventListener('scroll', function () {                                        // keys, scrollbar, find-in-page: follow them
      if (ours) { ours = false; return; }
      if (!running) { target = current = scrollY; }
    }, { passive: true });
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a) return;
      var el = document.querySelector(a.getAttribute('href')); if (!el) return;
      e.preventDefault(); target = clamp(el.getBoundingClientRect().top + scrollY, 0, max());
      if (!running) { running = true; requestAnimationFrame(tick); }
      history.replaceState(null, '', a.getAttribute('href'));
    });
  })();

  /* ---------- Cursor: glowing blue dot; the native pointer is hidden, so it tracks with almost no lag ---------- */
  if (fine) (function () {
    var dot = document.createElement('div'); dot.className = 'cursor'; dot.setAttribute('aria-hidden', 'true'); document.body.appendChild(dot);
    document.documentElement.classList.add('has-cursor');
    var x = -100, y = -100, cx = -100, cy = -100, k = reduce ? 1 : 0.7;
    addEventListener('pointermove', function (e) { x = e.clientX; y = e.clientY; dot.classList.add('on'); }, { passive: true });
    document.addEventListener('pointerleave', function () { dot.classList.remove('on'); });
    addEventListener('pointerdown', function () { dot.classList.add('down'); });
    addEventListener('pointerup', function () { dot.classList.remove('down'); });
    document.addEventListener('pointerover', function (e) { dot.classList.toggle('hover', !!(e.target.closest && e.target.closest('a, button, [role=button]'))); });
    (function loop() { cx += (x - cx) * k; cy += (y - cy) * k; dot.style.transform = 'translate3d(' + cx.toFixed(1) + 'px,' + cy.toFixed(1) + 'px,0)'; requestAnimationFrame(loop); })();
  })();

  /* ---------- Hero lockup: the 4+ spans exactly cap height of line 1 to baseline of line 3 ---------- */
  function alignHero() {
    var dialEl = $('.dial'), title = $('.display'), fourEl = $('.dial .four');
    if (!dialEl || !title || !fourEl) return;
    if (innerWidth <= 900) { dialEl.style.width = ''; dialEl.style.top = ''; return; }
    var spans = $$('.display .line'); if (spans.length < 3) return;   // the line boxes, not the animated spans inside them
    var cs = getComputedStyle(title), fs = parseFloat(cs.fontSize), lh = parseFloat(cs.lineHeight) || fs * 0.96;
    var c = document.createElement('canvas').getContext('2d'); c.font = cs.fontWeight + ' ' + fs + 'px ' + cs.fontFamily;
    var mB = c.measureText('B'), fa = mB.fontBoundingBoxAscent, fd = mB.fontBoundingBoxDescent, cap = mB.actualBoundingBoxAscent;
    function baseline(el) { return el.getBoundingClientRect().top + (lh - (fa + fd)) / 2 + fa; }
    var capTop = baseline(spans[0]) - cap, base = baseline(spans[2]);
    var want = base - capTop;
    // the mark's share of the dial is fixed by the SVG, so size the dial from it
    dialEl.style.top = '0px';
    var ratio = fourEl.getBoundingClientRect().height / dialEl.getBoundingClientRect().width;
    dialEl.style.width = (want / ratio).toFixed(1) + 'px';
    var f = fourEl.getBoundingClientRect();
    dialEl.style.top = (capTop - f.top).toFixed(1) + 'px';
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(alignHero); else alignHero();
  addEventListener('resize', alignHero);

  /* ---------- One-shot reveals ---------- */
  $$('.cards').forEach(function (list) { $$('[data-card]', list).forEach(function (c, i) { c.style.setProperty('--k', i); }); });
  var once = $$('[data-reveal], [data-ed]');
  // Cards replay: they reset once they're back below the screen, so scrolling down to them again re-plays the entrance
  if ('IntersectionObserver' in window && !reduce) {
    var cin = new IntersectionObserver(function (es) {   // plays as it comes into view
      es.forEach(function (e) { if (e.isIntersecting) e.target.classList.add('in'); });
    }, { rootMargin: '0px 0px -10% 0px' });
    var cout = new IntersectionObserver(function (es) {  // resets only once fully gone below the screen
      es.forEach(function (e) { if (!e.isIntersecting && e.boundingClientRect.top > 0) e.target.classList.remove('in'); });
    });
    $$('[data-card]').forEach(function (t) { cin.observe(t); cout.observe(t); });
  } else $$('[data-card]').forEach(function (t) { t.classList.add('in'); });
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -10% 0px' });
    once.forEach(function (t) { io.observe(t); });
  } else { once.forEach(function (t) { t.classList.add('in'); }); }

  /* ---------- Card pointer light ---------- */
  if (fine) $$('.card').forEach(function (c) {
    c.addEventListener('pointermove', function (e) {
      var b = c.getBoundingClientRect();
      c.style.setProperty('--mx', (e.clientX - b.left) + 'px');
      c.style.setProperty('--my', (e.clientY - b.top) + 'px');
    });
  });

  /* ---------- Photo tilt targets (eased in the frame loop) ---------- */
  if (fine) $$('.ed-img').forEach(function (el) {
    el.addEventListener('pointermove', function (e) {
      var b = el.getBoundingClientRect(), st = el._tilt || (el._tilt = { x: 0, y: 0, tx: 0, ty: 0 });
      st.ty = ((e.clientX - b.left) / b.width - 0.5) * 3;
      st.tx = -((e.clientY - b.top) / b.height - 0.5) * 3;
    }, { passive: true });
    el.addEventListener('pointerleave', function () { if (el._tilt) el._tilt.tx = el._tilt.ty = 0; });
  });

  /* ---------- Cursor light on photos, sign-off and contact ---------- */
  if (fine) $$('.ed-img, .so-stick, .contact').forEach(function (s) {
    var l = document.createElement('span'); l.className = 'lit'; l.setAttribute('aria-hidden', 'true');
    s.insertBefore(l, s.querySelector('.so-copy, .wrap, .ed-mark'));
    s.addEventListener('pointerenter', function () { s.classList.add('is-lit'); });
    s.addEventListener('pointerleave', function () { s.classList.remove('is-lit'); });
    s.addEventListener('pointermove', function (e) {
      var b = s.getBoundingClientRect();
      s.style.setProperty('--mx', (e.clientX - b.left) + 'px');
      s.style.setProperty('--my', (e.clientY - b.top) + 'px');
    }, { passive: true });
  });

  // Reduced motion: no film playback, but always show its still frame
  if (reduce) { var still = $('.film-v.a'); if (still && still.dataset.poster) still.poster = still.dataset.poster; return; }

  /* ---------- Lead: words light up as you read down ---------- */
  var lead = $('[data-words]');
  var words = [];
  if (lead) {
    (function split(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(part)); return; }
            var s = document.createElement('span'); s.className = 'w'; s.textContent = part; frag.appendChild(s); words.push(s);
          });
          node.replaceChild(frag, n);
        } else if (n.nodeType === 1) split(n);
      });
    })(lead);
    lead.setAttribute('aria-label', lead.textContent.replace(/\s+/g, ' ').trim());
  }

  /* ---------- Film line: each word sits in its own mask ---------- */
  var fline = $('[data-film-words]');
  if (fline) {
    var txt = fline.textContent.trim();
    fline.setAttribute('aria-label', txt);
    fline.innerHTML = txt.split(/\s+/).map(function (w) { return '<span class="fw" aria-hidden="true"><span>' + w + '</span></span>'; }).join(' ');
  }

  /* ---------- Elements driven by the loop ---------- */
  var hero = $('.hero'), dial = $('.dial'), tilt = $('.dial-tilt'), copy = $('.hero-copy');
  var ring = $('.dial .ring'), mark = $('.dial .mark'), glow = $('.dial .glow'), pool = $('.dial .pool');
  var grad = document.getElementById('lit');
  var heroP = 0, hs = hero ? hero.style : null, flead = $('.film-lead');
  var heroLines = $$('.display .line > span'), ticks = $$('.dial .tick'), foot = $('.hero-foot'), footPs = foot ? $$('.hero-foot p') : [];
  function dialBase() { // the dial's centre in the viewport, ignoring our own transform
    var w = dial.offsetParent.getBoundingClientRect();
    return { x: w.left + dial.offsetLeft + dial.offsetWidth / 2, y: w.top + dial.offsetTop + dial.offsetWidth / 2 };
  }
  function slitTop() { // % from the top where the slit sits: centred, lowered on short screens so the announcement fits
    var le = flead && flead.querySelector('.lead'); if (!le) return 50;
    var gap = Math.min(100, Math.max(64, innerWidth * 0.07));
    return clamp((le.offsetHeight + gap + 28) / innerHeight * 100, 50, 80);
  }
  function leadGut() { // the text column's left edge: where the film's slit begins
    if (!flead) return innerWidth * 0.06;
    return flead.getBoundingClientRect().left + parseFloat(getComputedStyle(flead).paddingLeft);
  }
  var film = $('.film-scene'), fstick = $('.film-stick');
  var vids = $$('.film-v'), fwords = $$('.film-copy .fw > span');

  /* Film playback: right size for the screen, loaded just before it's needed,
     slowed for weight, and looped on a hard cut like the edit itself. */
  var RATE = 0.8, XF = 0.8, front = 0, filmOn = false;
  if (vids.length) {
    var src = (innerWidth * (devicePixelRatio || 1) > 1500) ? 'assets/video/film-1080.mp4' : 'assets/video/film-720.mp4';
    // Fetch the film only once the visitor is on their way to it — never on page load
    var armed = false;
    var vio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting && !vids[0].src) vids.forEach(function (v, i) {
          if (i === 0) v.poster = v.dataset.poster;
          v.src = src; v.preload = 'auto'; v.loop = true; v.playbackRate = RATE; v.defaultPlaybackRate = RATE;
        });
        filmOn = e.isIntersecting;
        if (filmOn) { var v = vids[front]; v.playbackRate = RATE; v.play().catch(function () {}); }
        else vids.forEach(function (v) { v.pause(); });
      });
    }, { rootMargin: '0px 0px 40% 0px' });
    function arm() { if (armed) return; armed = true; vio.observe(film); removeEventListener('scroll', arm); }
    addEventListener('scroll', arm, { passive: true });
    if (scrollY > 0) arm();
  }
  function loopFilm() {
    return; // the edit loops on a hard cut via the native loop — no crossfade
    var a = vids[front], b = vids[1 - front];
    if (!a.duration) return;
    var left = a.duration - a.currentTime;
    if (left < XF) {
      if (b.paused) { b.currentTime = 0; b.playbackRate = RATE; b.style.zIndex = 2; a.style.zIndex = 1; b.play().catch(function () {}); }
      b.style.opacity = (1 - left / XF).toFixed(3);
    }
    if (a.ended || left < 0.04) { a.pause(); b.style.opacity = 1; a.style.opacity = 0; front = 1 - front; }
  }
  var eds = $$('.ed-img');
  var cardsEl = document.querySelector('.services .cards');
  var servicesEl = document.querySelector('.services');
  var so = $('.signoff'), soStick = $('.so-stick'), soLines = $$('.so-lines span');
  var endMark = $('.end-mark'), endSecs = [$('#contact'), $('.site-footer.over-film')].filter(Boolean);
  /* Contact and footer: each element eases in as its section arrives, in reading order; replays from below */
  endSecs.forEach(function (sec) { $$('.end-el', sec).forEach(function (el, i) { el.style.setProperty('--n', i); }); });
  if ('IntersectionObserver' in window) {
    var ein = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) e.target.classList.add('in'); }); }, { rootMargin: '0px 0px -12% 0px' });
    var eout = new IntersectionObserver(function (es) { es.forEach(function (e) { if (!e.isIntersecting && e.boundingClientRect.top > 0) e.target.classList.remove('in'); }); });
    endSecs.forEach(function (sec) { ein.observe(sec); eout.observe(sec); });
  } else endSecs.forEach(function (sec) { sec.classList.add('in'); });
  // Keyboard: tabbing in reveals at once, so focus never lands on something invisible
  endSecs.forEach(function (sec) { sec.addEventListener('focusin', function () { sec.classList.add('in'); }); });

  /* Keylines draw their full outline exactly once: stroke width is set in the mark's own units
     (a non-scaling stroke would distort the dash lengths) */
  function keylineWidths() {
    $$('.ed-mark, .end-mark').forEach(function (svg) {
      var k = svg.getBoundingClientRect().width / 151;   // viewBox is 151 units wide
      if (k > 0) svg.style.setProperty('--sw', (1.4 / k).toFixed(3));
    });
  }
  keylineWidths(); addEventListener('resize', keylineWidths); addEventListener('load', keylineWidths);
  /* Sign-off: the 4+ rises once as the section arrives, then hands over to a seamless idle loop
     (the mark floating, fine rings drifting out). Time-based, never tied to the scroll. */
  var soRise = $('.so-rise'), soLoop = $('.so-loop');
  if (soRise && soLoop) {
    var big = innerWidth * (devicePixelRatio || 1) >= 1000;
    var started = false;
    function soLoad() {
      if (soRise.src) return;
      soRise.src = 'assets/video/rise-' + (big ? '1600' : '960') + '.mp4';
      soLoop.src = 'assets/video/float-' + (big ? '1600' : '960') + '.mp4';
      soRise.preload = soLoop.preload = 'auto'; soLoop.loop = true;
    }
    function toLoop() { // cross-fade into the loop just before the rise ends
      if (soLoop.classList.contains('on')) return;
      soLoop.currentTime = 0; soLoop.play().catch(function () {});
      soLoop.classList.add('on'); setTimeout(function () { soRise.classList.remove('on'); }, 700);
    }
    soRise.addEventListener('timeupdate', function () { if (soRise.duration && soRise.currentTime > soRise.duration - 0.5) toLoop(); });
    soRise.addEventListener('ended', toLoop);
    var lio = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { soLoad(); lio.disconnect(); } }, { rootMargin: '0px 0px 120% 0px' });
    var pio = new IntersectionObserver(function (es) {   // play when it's properly in view; pause off screen
      var e = es[0];
      if (e.isIntersecting) {
        if (!started) { started = true; soRise.classList.add('on'); soRise.play().catch(function () { toLoop(); }); }
        else if (soLoop.classList.contains('on')) soLoop.play().catch(function () {});
      } else { soLoop.pause(); }
    }, { threshold: 0.35 });
    addEventListener('scroll', function arm2() { lio.observe(so); pio.observe(soStick); removeEventListener('scroll', arm2); }, { passive: true });
  }
  var marks = $$('.ed-mark');
  var deboss = $('.deboss'), contact = $('.contact');

  var introDone = false;
  function startIntroClock() { // intro finished: hand the glow over from its CSS animation to the scroll
    setTimeout(function () {
      introDone = true;
      [glow, pool].forEach(function (el) { if (!el) return; el.style.opacity = getComputedStyle(el).opacity; el.style.animation = 'none'; });
    }, 2600);
  }
  // Behind the preview gate the intro waits, then plays from the start once the visitor is let in
  if (document.documentElement.classList.contains('gated')) document.addEventListener('t4:unlock', startIntroClock, { once: true });
  else startIntroClock();

  var ptr = { x: 0, y: 0 }, cur = { x: 0, y: 0 };
  if (fine) addEventListener('pointermove', function (e) {
    ptr.x = (e.clientX / innerWidth) * 2 - 1;
    ptr.y = (e.clientY / innerHeight) * 2 - 1;
  }, { passive: true });

  var vh = innerHeight;
  addEventListener('resize', function () { vh = innerHeight; });

  function progress(el, start, end) { // 0 when el top hits `start` (px from top), 1 when it hits `end`
    var t = el.getBoundingClientRect().top;
    return clamp((start - t) / (start - end), 0, 1);
  }

  var t0 = performance.now();
  function frameLoop(t) {
    var time = (t - t0) / 1000;
    cur.x = lerp(cur.x, ptr.x, 0.06);
    cur.y = lerp(cur.y, ptr.y, 0.06);

    /* Hero: pinned while one continuous move plays out. The title leaves line by line, the clock
       winds down anticlockwise, the 4+ travels to the centre and flattens into a horizon of light,
       and that horizon is the slit the film opens from. */
    var hb = hero ? hero.getBoundingClientRect() : null;
    if (hb && hb.bottom > 0) {
      var p = clamp(-hb.top / Math.max(1, hb.height - vh), 0, 1);  // pin progress
      var e = inOut(p);

      // Glow breathes; flares as it flattens
      var flat = inOut(clamp((p - 0.46) / 0.24, 0, 1));
      if (introDone) {
        // the glow leaves first, so only the crisp mark is left to flatten
        var dim = 1 - inOut(clamp((p - 0.3) / 0.16, 0, 1));
        glow.style.opacity = ((0.82 + Math.sin(time * 1.05) * 0.08) * dim).toFixed(3);
        pool.style.opacity = dim.toFixed(3);
      }

      // Room light leans towards the cursor and dims as the scene empties
      var lr = dialBase();
      hs.setProperty('--lx', ((lr.x / innerWidth) * 100 + cur.x * 7).toFixed(2) + '%');
      hs.setProperty('--ly', ((lr.y / vh) * 100 + cur.y * 7).toFixed(2) + '%');
      hs.setProperty('--hl', (1 - inOut(clamp((p - 0.3) / 0.45, 0, 1))).toFixed(3));

      // Pointer: the dial tilts in 3D, settling flat as it leaves
      var calm = 1 - e;
      tilt.style.transform = 'rotateX(' + (-cur.y * 9 * calm).toFixed(2) + 'deg) rotateY(' + (cur.x * 12 * calm).toFixed(2) + 'deg)';
      mark.setAttribute('transform', 'translate(' + (cur.x * 6 * calm).toFixed(2) + ' ' + (cur.y * 6 * calm).toFixed(2) + ')');
      grad.setAttribute('gradientTransform', 'rotate(' + (cur.x * 40 - cur.y * 20).toFixed(2) + ' .5 .5)');

      // Title lines leave upward through their masks, one after another
      for (var li = 0; li < heroLines.length; li++) {
        var lk = inOut(clamp((p - li * 0.07) / 0.3, 0, 1));
        heroLines[li].style.translate = '0 ' + (-lk * 108).toFixed(2) + '%';
      }
      // The foot leaves with them: words drop away, the rule retracts
      var fk = inOut(clamp(p / 0.26, 0, 1));
      footPs.forEach(function (fp) { fp.style.opacity = (1 - fk).toFixed(3); fp.style.translate = '0 ' + (fk * 14).toFixed(1) + 'px'; });
      foot.style.setProperty('--hr', (1 - inOut(clamp(p / 0.34, 0, 1))).toFixed(3));

      // The clock winds down: marks go out anticlockwise from twelve
      for (var n = 0; n < 24; n++) {
        var tk = ticks[(24 - n) % 24];
        var tko = 1 - clamp((p - 0.04 - n * 0.011) / 0.06, 0, 1);
        tk.style.strokeOpacity = tko < 1 ? tko.toFixed(3) : '';
      }
      ring.setAttribute('transform', 'rotate(' + (-e * 40).toFixed(2) + ' 777.9 76.5)');

      // The mark travels to the centre, then flattens into a line of light
      var mv = inOut(clamp((p - 0.1) / 0.45, 0, 1));
      var st0 = slitTop();
      var dx = (innerWidth / 2 - lr.x) * mv, dy = (vh * st0 / 100 - 0.5 - lr.y) * mv; // centre of the 1px line
      var sc = lerp(1, 1.4, mv);                                 // grows towards you as it travels
      var fourH = dial.offsetWidth * (152.9 / 320);          // the 4+'s height at rest
      var sy = lerp(sc, 1 / fourH, flat);                       // ...squashed to exactly one pixel
      dial.style.transform = 'translate3d(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px,0) scale(' + sc.toFixed(4) + ',' + sy.toFixed(5) + ')';
      var swap = flat >= 0.999;                                 // flat: the line takes over at the same width
      dial.style.opacity = swap ? '0' : '1';

      // ...and the horizon draws out from it to the width of the site
      var gut2 = leadGut();
      var w0 = (dial.offsetWidth * (145 / 320) * sc) / Math.max(1, innerWidth - gut2 * 2); // the 4+'s width, as a share of the line
      var hzw = lerp(w0, 1, inOut(clamp((p - 0.72) / 0.24, 0, 1)));
      hs.setProperty('--hzx', gut2.toFixed(1) + 'px');
      hs.setProperty('--hzt', st0.toFixed(3) + '%');
      hs.setProperty('--hzw', hzw.toFixed(4));
      hs.setProperty('--hzg', inOut(clamp((p - 0.74) / 0.24, 0, 1)).toFixed(3)); // its glow returns as it draws out
      hs.setProperty('--hzo', swap ? '1' : '0');

      // The announcement waits in its final place, then rises in above the horizon as it draws
      heroP = p;
      if (flead && film && !fstick.classList.contains('live')) {
        var rk = inOut(clamp((p - 0.6) / 0.3, 0, 1));
        flead.style.translate = '0 ' + (-film.getBoundingClientRect().top + (1 - rk) * 48).toFixed(1) + 'px';
        flead.style.opacity = rk.toFixed(3);
      }
    }

    /* Lead words */
    if (words.length) {
      var lp = hero && !hero.classList.contains('handed') ? clamp((heroP - 0.66) / 0.34, 0, 1) : 1; // words light as it arrives
      var n = words.length;
      for (var w = 0; w < n; w++) {
        var k = clamp(lp * (n + 6) - w, 0, 1);
        words[w].style.opacity = (0.16 + k * 0.84).toFixed(3);
      }
    }

    /* Film scene */
    if (film) {
      var fb = film.getBoundingClientRect();
      if (fb.top < vh && fb.bottom > 0) {
        if (filmOn) loopFilm();
        // A held beat first: the announcement sits still over the horizon long enough to be read
        var HOLD = vh * 0.6;
        var sp = clamp((-fb.top - HOLD) / (fb.height - vh - HOLD), 0, 1);
        var live = fb.top <= 0.5;               // the hero has let go: the film's own slit takes over
        fstick.classList.toggle('live', live); hero.classList.toggle('handed', live);
        if (live && flead) { flead.style.opacity = ''; flead.style.translate = ''; }
        var W = innerWidth;
        var lb = Math.max(8, (1 - (W / 2.39) / vh) / 2 * 100);   // cinemascope bars, % of height
        var o1 = inOut(clamp(sp / 0.22, 0, 1));                    // slit → letterbox, easing out of the hold
        var o2 = ease(clamp((sp - 0.3) / 0.2, 0, 1));             // letterbox → full bleed
        var s0 = slitTop();
        var fy = lerp(lerp(s0, lb, o1), 0, o2), fyb = lerp(lerp(100 - s0, lb, o1), 0, o2);
        // The slit starts exactly at the text column's edges, so it marks the site width
        var lw = $('.film-lead'); var gut = lw ? (lw.getBoundingClientRect().left + parseFloat(getComputedStyle(lw).paddingLeft)) : W * 0.1;
        var fx = lerp(lerp(gut, W * 0.025, o1), 0, o2);
        var cam = ease(clamp(sp / 0.62, 0, 1));
        var s = fstick.style;
        s.setProperty('--fy', fy.toFixed(3) + '%'); s.setProperty('--fyb', fyb.toFixed(3) + '%');
        s.setProperty('--fx', fx.toFixed(1) + 'px');
        s.setProperty('--fr', ((1 - o2) * 4).toFixed(2) + 'px');
        s.setProperty('--fs', (lerp(1.55, 1.1, cam) - sp * 0.05).toFixed(4));
        s.setProperty('--fz', lerp(-3.5, 0, cam).toFixed(3) + 'deg');
        s.setProperty('--ftx', lerp(-2.5, 2.5, sp).toFixed(3) + '%');
        s.setProperty('--fty', lerp(1.5, -1.5, sp).toFixed(3) + '%');
        s.setProperty('--fe', (1 - o2).toFixed(3));
        // Final stretch: the services cards rise over the film while it quietly fades away
        // fade with the cards: starts as they rise into view, gone as they reach centre screen
        var cb = cardsEl ? cardsEl.getBoundingClientRect() : null;
        var fk = cb ? clamp((vh - cb.top) / (vh * 0.5 + cb.height * 0.5), 0, 1) : clamp((sp - 0.86) / 0.14, 0, 1);
        s.setProperty('--fo', (1 - inOut(fk)).toFixed(3));
        if (servicesEl) servicesEl.classList.toggle('no-film', fk >= 0.999); // nothing left to see through: drop the blur
        // The line lifts away, then the full logo arrives: keyline 4+, wordmark from blur, then the fill
        var wout = ease(clamp((sp - 0.56) / 0.08, 0, 1));
        s.setProperty('--co', (1 - wout).toFixed(3));
        s.setProperty('--cy', (-wout * 0.07 * vh).toFixed(1) + 'px');
        s.setProperty('--ld', ease(clamp((sp - 0.6) / 0.12, 0, 1)).toFixed(4));
        s.setProperty('--lw', ease(clamp((sp - 0.63) / 0.1, 0, 1)).toFixed(4));
        s.setProperty('--lf', ease(clamp((sp - 0.71) / 0.08, 0, 1)).toFixed(4));
        // ...and is fully gone before the service cards rise over it
        s.setProperty('--lo', (1 - ease(clamp((sp - 0.8) / 0.08, 0, 1))).toFixed(3));
        s.setProperty('--fv', ease(clamp((sp - 0.56) / 0.16, 0, 1)).toFixed(3));
        for (var q = 0; q < fwords.length; q++) {
          var wk = ease(clamp((sp - 0.32 - q * 0.025) / 0.12, 0, 1));
          var st = fwords[q].style;
          st.transform = 'translate3d(0,' + ((1 - wk) * 105).toFixed(2) + '%,0)';
          st.opacity = wk.toFixed(3);
          st.filter = wk < 1 ? 'blur(' + ((1 - wk) * 10).toFixed(2) + 'px)' : 'none';
        }
      }
    }

    /* Sign-off: the render pushes in, the title arrives, then the promise builds line by line */
    if (so) {
      var ob = so.getBoundingClientRect();
      if (ob.top < vh && ob.bottom > 0) {
        var ss = soStick.style;
        var op = clamp(-ob.top / (ob.height - vh), 0, 1);
        var enter = clamp((vh - ob.top) / vh, 0, 1);
        ss.setProperty('--sv', inOut(clamp((op - 0.02) / 0.3, 0, 1)).toFixed(3)); // the render rises out of the navy
        ss.setProperty('--ss', (1.1 - ease(clamp(op / 0.95, 0, 1)) * 0.1 + (1 - enter) * 0.03).toFixed(4));
        ss.setProperty('--sx', (-ease(op) * 1.5).toFixed(3) + '%');
        ss.setProperty('--st', ease(clamp((enter - 0.55) / 0.4 + op * 2, 0, 1)).toFixed(3));
        ss.setProperty('--se', ease(clamp((op - 0.82) / 0.18, 0, 1)).toFixed(3));
        soLines.forEach(function (sp, i) {
          var k = ease(clamp((op - 0.12 - i * 0.16) / 0.16, 0, 1));
          sp.style.transform = 'translate3d(0,' + ((1 - k) * 106).toFixed(2) + '%,0)';
        });
      }
    }

    /* Editorial photographs: scroll parallax, plus a slow buoyant float, as if suspended in
       water; on hover they lean a fraction of a degree towards the cursor */
    eds.forEach(function (el, i) {
      var fig = el.parentNode, py = fig._py || 0, b = fig.getBoundingClientRect();
      if (b.bottom < -300 || b.top > vh + 300) return;
      var c = (b.top - py + b.height / 2 - vh / 2) / vh; // layout position, minus our own offset
      fig._py = -c * parseFloat(el.dataset.speed) * vh * (innerWidth > 900 ? 1 : 0.2);
      fig.style.transform = 'translate3d(0,' + fig._py.toFixed(2) + 'px,0)';
      var sec = t / 1000, ph = i * 2.1, per = [10, 12.5, 11.2][i % 3];
      var fy = Math.sin(sec * 6.283 / per + ph) * 5;
      var fx = Math.sin(sec * 6.283 / (per * 1.6) + ph * 0.7) * 2.5;
      var fr = Math.sin(sec * 6.283 / (per * 1.3) + ph * 1.3) * 0.18;
      var st = el._tilt || (el._tilt = { x: 0, y: 0, tx: 0, ty: 0 });
      st.x += (st.tx - st.x) * 0.05; st.y += (st.ty - st.y) * 0.05;
      el.style.transform = 'perspective(1400px) translate3d(' + fx.toFixed(2) + 'px,' + fy.toFixed(2) + 'px,0) rotateX(' + st.x.toFixed(3) + 'deg) rotateY(' + st.y.toFixed(3) + 'deg) rotate(' + fr.toFixed(3) + 'deg)';
    });

    /* 4+ on each photograph: the diagonal draws, then the plus, then it fills — scrubbed by
       scroll across most of the photo's journey, and damped so it trails the scroll gently */
    marks.forEach(function (m) {
      var b = m.parentNode.getBoundingClientRect();
      var st = m._s || (m._s = { p: 0 });
      var target = clamp((vh - b.bottom) / (vh * 1.15), 0, 1);   // spread across the photo's whole climb
      st.p += (target - st.p) * 0.03;
      if (Math.abs(target - st.p) < 0.0005) st.p = target;
      var p = st.p;
      m.style.setProperty('--d2', inOut(clamp(p / 0.58, 0, 1)).toFixed(4));
      m.style.setProperty('--d1', inOut(clamp((p - 0.16) / 0.58, 0, 1)).toFixed(4));
      m.style.setProperty('--fill', inOut(clamp((p - 0.72) / 0.28, 0, 1)).toFixed(4));
      m.closest('.ed').style.setProperty('--cap', inOut(clamp(p / 0.8, 0, 1)).toFixed(4)); // caption bar fills with the scroll
    });

    /* The signature 4+: one full keyline as it rises into view, a beat, then the solid logo */
    if (endMark) {
      var eb = endMark.getBoundingClientRect();
      var et = clamp((vh * 0.95 - eb.top) / (vh * 0.4), 0, 1);
      if (scrollY >= document.documentElement.scrollHeight - vh - 2) et = 1;   // always complete at the very bottom
      var es = endMark._s || (endMark._s = { p: 0 });
      es.p += (et - es.p) * 0.06; if (Math.abs(et - es.p) < 0.0005) es.p = et;
      var em = endMark.style;
      em.setProperty('--e2', inOut(clamp(es.p / 0.45, 0, 1)).toFixed(4));            // the diagonal
      em.setProperty('--e1', inOut(clamp((es.p - 0.25) / 0.45, 0, 1)).toFixed(4));   // the plus, complete at 0.7
      em.setProperty('--ef', inOut(clamp((es.p - 0.8) / 0.2, 0, 1)).toFixed(4));     // then solid
    }

    /* Debossed 4+: light rakes across it as it passes */
    if (deboss) {
      var cb = contact.getBoundingClientRect();
      if (cb.top < vh && cb.bottom > 0) {
        var cp = clamp((vh - cb.top) / (vh + cb.height), 0, 1);
        var a = (cp * 2 - 1) * 1.6;
        deboss.style.setProperty('--dx', a.toFixed(2) + 'px');
        deboss.style.setProperty('--dy', (-1.2).toFixed(2) + 'px');
        deboss.style.setProperty('--dr', ((cp - 0.5) * -6).toFixed(2) + 'deg');
      }
    }

    raf = requestAnimationFrame(frameLoop);
  }
  var raf = requestAnimationFrame(frameLoop);
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) cancelAnimationFrame(raf); else raf = requestAnimationFrame(frameLoop);
  });
})();
