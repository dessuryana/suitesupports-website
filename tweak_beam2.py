with open('about-us.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Remove the outer aura block entirely (from var aura = ... to ctx.fill())
import re
c = re.sub(
    r'\s*// Beam head - large bright missile tip\s*'
    r'var aura = ctx\.createRadialGradient.*?ctx\.fill\(\);\s*',
    '\n      // Beam head - sharp tip only (no aura)\n      ',
    c, count=1, flags=re.DOTALL
)

# 2. Make active tail line much thinner
c = c.replace(
    "ctx.lineWidth   = 1 + tt * 4.5;",
    "ctx.lineWidth   = 0.5 + tt * 1.0;", 1
)
# Remove outer glow halo of the tail (set to 0 width effectively) — just remove the glow pass
c = c.replace(
    "ctx.strokeStyle = 'rgba(210,230,255,' + (tt * 0.20) + \")';\";",
    "ctx.strokeStyle = 'rgba(210,230,255,' + (tt * 0.20) + \")'\;", 1
)
# Simpler — just zero out the halo lineWidth
c = c.replace(
    "ctx.lineWidth   = 5 + tt * 18;",
    "ctx.lineWidth   = 0.8 + tt * 2;", 1
)

# 3. Make fading trail thinner
c = c.replace(
    "ctx.lineWidth   = f * 2 + 0.5;",
    "ctx.lineWidth   = f * 0.8 + 0.3;", 1
)
c = c.replace(
    "ctx.lineWidth   = f * 8;",
    "ctx.lineWidth   = f * 1.5;", 1
)

with open('about-us.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('Aura removed:', 'var aura' not in c)
print('Thin tail:', '0.5 + tt * 1.0' in c)
print('Thin trail:', 'f * 0.8 + 0.3' in c)
