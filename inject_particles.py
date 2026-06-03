import os

DIR = r"C:\DOR - Files\Data_Claude Code\SuiteSupports Website"

CANVAS = '<canvas id="particle-canvas" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:2;"></canvas>'

PARTICLE_JS = """
  // BEE PARTICLE SYSTEM
  (function() {
    var canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var W = canvas.width = window.innerWidth;
    var H = canvas.height = window.innerHeight;
    var mouseX = W * 0.5, mouseY = H * 0.5;
    var mouseActive = false, mouseTimer;
    var COLORS = ['212,164,39','236,200,74','74,171,184','45,143,160','248,249,250'];

    function Bee() {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.7;
      this.vy = (Math.random() - 0.5) * 0.7;
      this.size = Math.random() * 1.6 + 0.5;
      this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
      this.baseAlpha = Math.random() * 0.3 + 0.07;
      this.pSpeed = Math.random() * 0.025 + 0.006;
      this.pOff = Math.random() * Math.PI * 2;
      this.wobble = Math.random() * Math.PI * 2;
      this.wobbleV = (Math.random() - 0.5) * 0.05;
    }
    Bee.prototype.update = function() {
      this.wobble += this.wobbleV;
      if (mouseActive) {
        var dx = mouseX - this.x, dy = mouseY - this.y;
        var dist = Math.sqrt(dx*dx + dy*dy) || 1;
        var reach = 300;
        if (dist < reach) {
          var f = ((reach - dist) / reach) * 0.28;
          this.vx += (dx/dist)*f + (dy/dist)*f*0.25;
          this.vy += (dy/dist)*f - (dx/dist)*f*0.25;
        }
      } else {
        this.vx += Math.sin(this.wobble) * 0.025;
        this.vy += Math.cos(this.wobble * 0.7) * 0.025;
      }
      this.vx += (Math.random()-0.5)*0.07;
      this.vy += (Math.random()-0.5)*0.07;
      var spd = Math.sqrt(this.vx*this.vx + this.vy*this.vy);
      var maxSpd = mouseActive ? 4.0 : 1.1;
      if (spd > maxSpd) { this.vx = this.vx/spd*maxSpd; this.vy = this.vy/spd*maxSpd; }
      this.vx *= 0.965; this.vy *= 0.965;
      this.x += this.vx; this.y += this.vy;
      if (this.x < -12) this.x = W+12; if (this.x > W+12) this.x = -12;
      if (this.y < -12) this.y = H+12; if (this.y > H+12) this.y = -12;
    };
    Bee.prototype.draw = function() {
      var pulse = Math.sin(Date.now() * this.pSpeed + this.pOff) * 0.3 + 0.7;
      var a = this.baseAlpha * pulse, s = this.size;
      var glow = ctx.createRadialGradient(this.x,this.y,0,this.x,this.y,s*5);
      glow.addColorStop(0,'rgba('+this.color+','+(a*0.55)+')');
      glow.addColorStop(0.4,'rgba('+this.color+','+(a*0.2)+')');
      glow.addColorStop(1,'rgba('+this.color+',0)');
      ctx.beginPath(); ctx.arc(this.x,this.y,s*5,0,Math.PI*2);
      ctx.fillStyle=glow; ctx.fill();
      ctx.beginPath(); ctx.arc(this.x,this.y,s,0,Math.PI*2);
      ctx.fillStyle='rgba('+this.color+','+Math.min(a*2.2,0.95)+')';
      ctx.fill();
    };
    var bees = [];
    for (var i=0;i<65;i++) bees.push(new Bee());
    window.addEventListener('mousemove',function(e){
      mouseX=e.clientX;mouseY=e.clientY;mouseActive=true;
      clearTimeout(mouseTimer);
      mouseTimer=setTimeout(function(){mouseActive=false;},2200);
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
    },{passive:true});
    function animate(){
      ctx.clearRect(0,0,W,H);
      for(var i=0;i<bees.length;i++){bees[i].update();bees[i].draw();}
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

    if 'particle-canvas' in content:
        print('SKIP (already done): ' + page)
        continue

    # Insert canvas after scroll-progress
    if '<div id="scroll-progress"></div>' in content:
        content = content.replace(
            '<div id="scroll-progress"></div>',
            '<div id="scroll-progress"></div>\n' + CANVAS,
            1
        )
    else:
        content = content.replace('<body>', '<body>\n<div id="scroll-progress"></div>\n' + CANVAS, 1)

    # Insert JS before last </script>
    last_script = content.rfind('</script>')
    if last_script != -1:
        content = content[:last_script] + PARTICLE_JS + '\n</script>' + content[last_script+9:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('DONE: ' + page)

print('All files processed.')
