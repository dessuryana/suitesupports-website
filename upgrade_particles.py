import os, re

DIR = r"C:\DOR - Files\Data_Claude Code\SuiteSupports Website"

NEW_JS = r"""
  // GALAXY PARTICLE SYSTEM v3
  (function() {
    var canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var W = canvas.width = window.innerWidth;
    var H = canvas.height = window.innerHeight;
    var mouseX = -9999, mouseY = -9999;
    var mouseActive = false, mouseTimer;
    var COLORS = ['212,164,39','236,200,74','74,171,184','45,143,160','248,249,250','143,169,181','180,137,26'];
    var COUNT = 220;

    // States: 0=DRIFT  1=GATHER  2=SWIRL(orbit galaxy before spreading)  3=SPREAD
    var idleState = 0;
    var stateStart = Date.now();
    //           DRIFT   GATHER  SWIRL   SPREAD
    var STATE_MS = [3200,  4200,   4500,   6500];

    var galaxyTargets = [];

    function computeGalaxy() {
      galaxyTargets = [];
      var cx = W * 0.5, cy = H * 0.5;
      var maxR = Math.min(W, H) * 0.30;
      var numArms = 3;
      var coreCount = Math.floor(COUNT * 0.15);
      for (var i = 0; i < coreCount; i++) {
        var angle = Math.random() * Math.PI * 2;
        var r = Math.pow(Math.random(), 1.5) * maxR * 0.25;
        galaxyTargets.push({ x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) * 0.9 });
      }
      for (var i = coreCount; i < COUNT; i++) {
        var t = (i - coreCount) / (COUNT - coreCount);
        var arm = i % numArms;
        var armAngle = (arm / numArms) * Math.PI * 2;
        var r = Math.pow(t, 0.5) * maxR;
        var spiral = armAngle + t * Math.PI * 4.5;
        var jx = (Math.random() - 0.5) * maxR * 0.18;
        var jy = (Math.random() - 0.5) * maxR * 0.12;
        galaxyTargets.push({
          x: cx + r * Math.cos(spiral) + jx,
          y: cy + r * Math.sin(spiral) * 0.52 + jy
        });
      }
    }

    function Particle(idx) {
      this.idx = idx;
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 1.2;
      this.vy = (Math.random() - 0.5) * 1.2;
      this.size = Math.random() * 1.9 + 0.4;
      this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
      this.baseAlpha = Math.random() * 0.38 + 0.07;
      this.pSpeed = Math.random() * 0.022 + 0.005;
      this.pOff = Math.random() * Math.PI * 2;
      this.wobble = Math.random() * Math.PI * 2;
      this.wobbleV = (Math.random() - 0.5) * 0.045;
    }

    Particle.prototype.update = function(state, swirlProgress) {
      this.wobble += this.wobbleV;

      if (mouseActive) {
        // BEE SWARM
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
        // GATHER — spring toward galaxy targets
        var tx = galaxyTargets[this.idx].x, ty = galaxyTargets[this.idx].y;
        var dx = tx - this.x, dy = ty - this.y;
        var dist = Math.sqrt(dx*dx+dy*dy) || 1;
        var pull = Math.min(dist * 0.045, 1.2);
        this.vx += (dx/dist)*pull;
        this.vy += (dy/dist)*pull;
        this.vx += (Math.random()-0.5)*0.04;
        this.vy += (Math.random()-0.5)*0.04;
        var spd = Math.sqrt(this.vx*this.vx+this.vy*this.vy);
        if (spd > 3.5) { this.vx=this.vx/spd*3.5; this.vy=this.vy/spd*3.5; }
        this.vx *= 0.94; this.vy *= 0.94;

      } else if (state === 2) {
        // SWIRL — orbit + spring: galaxy spins before dispersing
        // Tangential (orbital) force grows over swirlProgress 0→1
        var tx = galaxyTargets[this.idx].x, ty = galaxyTargets[this.idx].y;
        var dx = tx - this.x, dy = ty - this.y;
        var cx = W*0.5, cy = H*0.5;
        var rx = this.x - cx, ry = this.y - cy;
        // Perpendicular to radius = tangential orbit direction
        var tang = Math.sqrt(rx*rx+ry*ry) || 1;
        var tangX = -ry/tang, tangY = rx/tang;
        // Orbit force ramps up as swirl progresses (0→0.14)
        var orbitF = 0.02 + swirlProgress * 0.12;
        // Spring back force weakens as swirl progresses (0.018→0.004)
        var springF = 0.018 - swirlProgress * 0.014;
        this.vx += dx * springF + tangX * orbitF + Math.sin(this.wobble)*0.02;
        this.vy += dy * springF + tangY * orbitF + Math.cos(this.wobble*0.8)*0.02;
        var spd = Math.sqrt(this.vx*this.vx+this.vy*this.vy);
        var maxSpd = 0.8 + swirlProgress * 2.2;
        if (spd > maxSpd) { this.vx=this.vx/spd*maxSpd; this.vy=this.vy/spd*maxSpd; }
        this.vx *= 0.96; this.vy *= 0.96;

      } else if (state === 3) {
        // SPREAD — slow lazy drift outward
        var cx = W*0.5, cy = H*0.5;
        var dx = this.x - cx, dy = this.y - cy;
        var dist = Math.sqrt(dx*dx+dy*dy) || 1;
        // Very gentle outward nudge + small random drift
        this.vx += (dx/dist)*0.04 + (Math.random()-0.5)*0.08;
        this.vy += (dy/dist)*0.04 + (Math.random()-0.5)*0.08;
        var spd = Math.sqrt(this.vx*this.vx+this.vy*this.vy);
        if (spd > 1.6) { this.vx=this.vx/spd*1.6; this.vy=this.vy/spd*1.6; }
        this.vx *= 0.985; this.vy *= 0.985;

      } else {
        // DRIFT — gentle sinusoidal float
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

    var swirlProgress = 0;

    function tickState() {
      var now = Date.now();
      var elapsed = now - stateStart;
      if (elapsed > STATE_MS[idleState]) {
        idleState = (idleState + 1) % 4;
        stateStart = now;
        elapsed = 0;
        swirlProgress = 0;
        // When entering SPREAD: tiny gentle push (NOT explosive)
        if (idleState === 3) {
          var cx=W*0.5, cy=H*0.5;
          for (var i=0;i<particles.length;i++) {
            var dx=particles[i].x-cx, dy=particles[i].y-cy;
            var d=Math.sqrt(dx*dx+dy*dy)||1;
            // Very small initial push — let the force do the work gradually
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
