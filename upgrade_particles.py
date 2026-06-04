import os, re

DIR = r"C:\DOR - Files\Data_Claude Code\SuiteSupports Website"

NEW_JS = r"""
  // GALAXY PARTICLE SYSTEM v4 — 3 triangle galaxies
  (function() {
    var canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var W = canvas.width = window.innerWidth;
    var H = canvas.height = window.innerHeight;
    var mouseX = -9999, mouseY = -9999;
    var mouseActive = false, mouseTimer;
    var COLORS = ['212,164,39','236,200,74','74,171,184','45,143,160','248,249,250','143,169,181','180,137,26'];
    var COUNT = 240;
    var G = 3; // number of groups
    var GS = Math.floor(COUNT / G); // particles per group

    // States: 0=DRIFT  1=GATHER  2=SWIRL  3=SPREAD
    var idleState = 0;
    var stateStart = Date.now();
    var STATE_MS = [3200, 5500, 36000, 6500];
    var swirlProgress = 0;

    var galaxyTargets = [];
    var groupCenters = [];

    function computeCenters() {
      var cx = W * 0.5, cy = H * 0.5;
      var r = Math.min(W, H) * 0.26;
      // Equilateral triangle — top, bottom-right, bottom-left
      groupCenters = [
        { x: cx,               y: cy - r },
        { x: cx + r * 0.866,   y: cy + r * 0.5 },
        { x: cx - r * 0.866,   y: cy + r * 0.5 }
      ];
    }

    function computeGalaxy() {
      computeCenters();
      galaxyTargets = [];
      var maxR = Math.min(W, H) * 0.10;
      for (var g = 0; g < G; g++) {
        var gcx = groupCenters[g].x, gcy = groupCenters[g].y;
        var start = g * GS;
        var end = (g === G - 1) ? COUNT : start + GS;
        var size = end - start;
        var coreCount = Math.floor(size * 0.18);
        // Core cluster
        for (var i = 0; i < coreCount; i++) {
          var angle = Math.random() * Math.PI * 2;
          var r = Math.pow(Math.random(), 1.6) * maxR * 0.28;
          galaxyTargets.push({ x: gcx + r * Math.cos(angle), y: gcy + r * Math.sin(angle) * 0.88 });
        }
        // 3-arm spiral around group center
        for (var i = coreCount; i < size; i++) {
          var t = (i - coreCount) / (size - coreCount);
          var arm = i % 3;
          var armAngle = (arm / 3) * Math.PI * 2;
          var r = Math.pow(t, 0.5) * maxR;
          var spiral = armAngle + t * Math.PI * 4.5;
          var jx = (Math.random() - 0.5) * maxR * 0.22;
          var jy = (Math.random() - 0.5) * maxR * 0.14;
          galaxyTargets.push({
            x: gcx + r * Math.cos(spiral) + jx,
            y: gcy + r * Math.sin(spiral) * 0.55 + jy
          });
        }
      }
    }

    function Particle(idx) {
      this.idx = idx;
      this.group = Math.min(Math.floor(idx / GS), G - 1);
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 1.2;
      this.vy = (Math.random() - 0.5) * 1.2;
      this.size = Math.random() * 1.9 + 0.4;
      // Slight color tint per group
      var groupTints = [
        ['212,164,39','236,200,74','248,249,250'],   // group 0 — gold
        ['74,171,184','45,143,160','143,169,181'],   // group 1 — teal
        ['180,137,26','212,164,39','248,249,250']    // group 2 — warm gold
      ];
      var tints = groupTints[this.group];
      this.color = tints[Math.floor(Math.random() * tints.length)];
      this.baseAlpha = Math.random() * 0.38 + 0.07;
      this.pSpeed = Math.random() * 0.022 + 0.005;
      this.pOff = Math.random() * Math.PI * 2;
      this.wobble = Math.random() * Math.PI * 2;
      this.wobbleV = (Math.random() - 0.5) * 0.045;
    }

    Particle.prototype.update = function(state, swP) {
      this.wobble += this.wobbleV;
      var gc = groupCenters[this.group];

      if (mouseActive) {
        // BEE SWARM toward cursor
        var dx = mouseX - this.x, dy = mouseY - this.y;
        var dist = Math.sqrt(dx*dx + dy*dy) || 1;
        if (dist < 400) {
          var f = ((400 - dist) / 400) * 0.32;
          this.vx += (dx/dist)*f + (dy/dist)*f*0.22;
          this.vy += (dy/dist)*f - (dx/dist)*f*0.22;
        }
        this.vx += (Math.random()-0.5)*0.09;
        this.vy += (Math.random()-0.5)*0.09;
        var spd = Math.sqrt(this.vx*this.vx+this.vy*this.vy);
        if (spd > 5.5) { this.vx=this.vx/spd*5.5; this.vy=this.vy/spd*5.5; }
        this.vx *= 0.96; this.vy *= 0.96;

      } else if (state === 1) {
        // GATHER — strong direct pull toward own group galaxy target
        var tx = galaxyTargets[this.idx].x, ty = galaxyTargets[this.idx].y;
        var dx = tx - this.x, dy = ty - this.y;
        var dist = Math.sqrt(dx*dx+dy*dy) || 1;
        var pull = Math.min(dist * 0.07, 1.6);
        this.vx += (dx/dist)*pull;
        this.vy += (dy/dist)*pull;
        this.vx += (Math.random()-0.5)*0.008;
        this.vy += (Math.random()-0.5)*0.008;
        var spd = Math.sqrt(this.vx*this.vx+this.vy*this.vy);
        if (spd > 4.5) { this.vx=this.vx/spd*4.5; this.vy=this.vy/spd*4.5; }
        this.vx *= 0.86; this.vy *= 0.86;

      } else if (state === 2) {
        // SWIRL — orbit around OWN group center
        var tx = galaxyTargets[this.idx].x, ty = galaxyTargets[this.idx].y;
        var dx = tx - this.x, dy = ty - this.y;
        // Tangential vector around group center
        var rx = this.x - gc.x, ry = this.y - gc.y;
        var tang = Math.sqrt(rx*rx+ry*ry) || 1;
        var tangX = -ry/tang, tangY = rx/tang;
        // Dead zone first 2s, then quadratic ramp
        var spinP = Math.max(0, (swP - 0.056)) / 0.944;
        var orbitF = spinP * spinP * 0.17;
        var springF = 0.028 - spinP * 0.022;
        this.vx += dx * springF + tangX * orbitF;
        this.vy += dy * springF + tangY * orbitF;
        var spd = Math.sqrt(this.vx*this.vx+this.vy*this.vy);
        var maxSpd = 0.4 + spinP * spinP * 3.2;
        if (spd > maxSpd) { this.vx=this.vx/spd*maxSpd; this.vy=this.vy/spd*maxSpd; }
        this.vx *= 0.97; this.vy *= 0.97;

      } else if (state === 3) {
        // SPREAD — drift outward from own group center
        var dx = this.x - gc.x, dy = this.y - gc.y;
        var dist = Math.sqrt(dx*dx+dy*dy) || 1;
        this.vx += (dx/dist)*0.04 + (Math.random()-0.5)*0.08;
        this.vy += (dy/dist)*0.04 + (Math.random()-0.5)*0.08;
        var spd = Math.sqrt(this.vx*this.vx+this.vy*this.vy);
        if (spd > 1.6) { this.vx=this.vx/spd*1.6; this.vy=this.vy/spd*1.6; }
        this.vx *= 0.985; this.vy *= 0.985;

      } else {
        // DRIFT — sinusoidal float
        this.vx += Math.sin(this.wobble)*0.03;
        this.vy += Math.cos(this.wobble*0.7)*0.03;
        this.vx += (Math.random()-0.5)*0.07;
        this.vy += (Math.random()-0.5)*0.07;
        var spd = Math.sqrt(this.vx*this.vx+this.vy*this.vy);
        if (spd > 1.4) { this.vx=this.vx/spd*1.4; this.vy=this.vy/spd*1.4; }
        this.vx *= 0.965; this.vy *= 0.965;
      }

      this.x += this.vx; this.y += this.vy;
      if (this.x < -15) this.x = W+15; if (this.x > W+15) this.x = -15;
      if (this.y < -15) this.y = H+15; if (this.y > H+15) this.y = -15;
    };

    Particle.prototype.draw = function() {
      var pulse = Math.sin(Date.now() * this.pSpeed + this.pOff) * 0.32 + 0.68;
      var a = this.baseAlpha * pulse, s = this.size;
      var glow = ctx.createRadialGradient(this.x,this.y,0,this.x,this.y,s*5.5);
      glow.addColorStop(0,'rgba('+this.color+','+(a*0.6)+')');
      glow.addColorStop(0.35,'rgba('+this.color+','+(a*0.22)+')');
      glow.addColorStop(1,'rgba('+this.color+',0)');
      ctx.beginPath(); ctx.arc(this.x,this.y,s*5.5,0,Math.PI*2);
      ctx.fillStyle=glow; ctx.fill();
      ctx.beginPath(); ctx.arc(this.x,this.y,s,0,Math.PI*2);
      ctx.fillStyle='rgba('+this.color+','+Math.min(a*2.4,0.98)+')';
      ctx.fill();
    };

    computeGalaxy();
    var particles = [];
    for (var i=0;i<COUNT;i++) particles.push(new Particle(i));

    function tickState() {
      var now = Date.now();
      var elapsed = now - stateStart;
      if (elapsed > STATE_MS[idleState]) {
        idleState = (idleState + 1) % 4;
        stateStart = now;
        elapsed = 0;
        swirlProgress = 0;
        if (idleState === 3) {
          // Gentle push outward from each group center
          for (var i=0;i<particles.length;i++) {
            var gc = groupCenters[particles[i].group];
            var dx=particles[i].x-gc.x, dy=particles[i].y-gc.y;
            var d=Math.sqrt(dx*dx+dy*dy)||1;
            particles[i].vx += (dx/d)*(0.3+Math.random()*0.4);
            particles[i].vy += (dy/d)*(0.3+Math.random()*0.4);
          }
        }
      }
      if (idleState === 2) {
        swirlProgress = Math.min(elapsed / STATE_MS[2], 1);
      }
      return idleState;
    }

    window.addEventListener('mousemove',function(e){
      mouseX=e.clientX;mouseY=e.clientY;mouseActive=true;
      clearTimeout(mouseTimer);
      mouseTimer=setTimeout(function(){mouseActive=false;},2400);
    },{passive:true});
    window.addEventListener('touchmove',function(e){
      var t=e.touches[0];mouseX=t.clientX;mouseY=t.clientY;mouseActive=true;
      clearTimeout(mouseTimer);
      mouseTimer=setTimeout(function(){mouseActive=false;},1800);
    },{passive:true});
    window.addEventListener('touchstart',function(e){
      var t=e.touches[0];mouseX=t.clientX;mouseY=t.clientY;mouseActive=true;
      clearTimeout(mouseTimer);
      mouseTimer=setTimeout(function(){mouseActive=false;},1800);
    },{passive:true});
    window.addEventListener('resize',function(){
      W=canvas.width=window.innerWidth;
      H=canvas.height=window.innerHeight;
      computeGalaxy();
    },{passive:true});

    function animate() {
      ctx.clearRect(0,0,W,H);
      var state = mouseActive ? -1 : tickState();
      for (var i=0;i<particles.length;i++) {
        particles[i].update(state, swirlProgress);
        particles[i].draw();
      }
      requestAnimationFrame(animate);
    }
    animate();
  })();
"""

pages = [
    'suitesupports-website.html',
    'about-us.html',
    'service-ai-chatbot.html',
    'service-web-design.html',
    'service-revenue-management.html',
    'service-digital-marketing.html'
]

for page in pages:
    path = os.path.join(DIR, page)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_pattern = re.compile(
        r'//\s*GALAXY PARTICLE SYSTEM v\d[^\x00]*?\}\)\(\);',
        re.DOTALL
    )
    if old_pattern.search(content):
        new_content = old_pattern.sub(NEW_JS.strip(), content, count=1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('UPDATED: ' + page)
    else:
        print('NO MATCH: ' + page)

print('Done.')
