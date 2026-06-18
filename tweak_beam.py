with open('about-us.html', 'r', encoding='utf-8') as f:
    c = f.read()

changes = [
    # ── Tail longer + more steps ─────────────────────────────────────────────
    ('var TAIL    = 220;   // px of active bright tail',
     'var TAIL    = 620;   // px of active bright tail'),
    ('var STEPS   = 55;    // subdivisions for tail gradient',
     'var STEPS   = 90;    // subdivisions for tail gradient'),

    # ── Head smaller: aura radius 44 -> 18 ───────────────────────────────────
    ("ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, 44)",
     "ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, 18)"),
    ("ctx.arc(head.x, head.y, 44, 0, Math.PI * 2);",
     "ctx.arc(head.x, head.y, 18, 0, Math.PI * 2);"),

    # ── Aura colours -> white ─────────────────────────────────────────────────
    ("aura.addColorStop(0,    'rgba(255,255,210,0.88)');",
     "aura.addColorStop(0,    'rgba(255,255,255,0.90)');"),
    ("aura.addColorStop(0.18, 'rgba(255,210,60,0.70)');",
     "aura.addColorStop(0.35, 'rgba(220,235,255,0.50)');"),
    ("aura.addColorStop(0.45, 'rgba(212,164,39,0.28)');",
     "aura.addColorStop(0.7,  'rgba(180,210,255,0.15)');"),
    ("aura.addColorStop(1,    'rgba(212,164,39,0)');",
     "aura.addColorStop(1,    'rgba(180,210,255,0)');"),

    # ── Core smaller: radius 13 -> 5 ─────────────────────────────────────────
    ("ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, 13)",
     "ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, 5)"),
    ("ctx.arc(head.x, head.y, 13, 0, Math.PI * 2);",
     "ctx.arc(head.x, head.y, 5, 0, Math.PI * 2);"),

    # ── Core colours -> white ─────────────────────────────────────────────────
    ("core.addColorStop(0,    'rgba(255,255,255,1)');",
     "core.addColorStop(0,    'rgba(255,255,255,1)');"),          # unchanged
    ("core.addColorStop(0.35, 'rgba(255,248,200,0.95)');",
     "core.addColorStop(0.5,  'rgba(230,240,255,0.85)');"),
    ("core.addColorStop(0.75, 'rgba(236,200,74,0.5)');",
     "core.addColorStop(1,    'rgba(200,225,255,0)');"),
    ("core.addColorStop(1,    'rgba(212,164,39,0)');",
     ""),                                                          # removed (now 3 stops)

    # ── Tip dot smaller: 3.5 -> 2 ────────────────────────────────────────────
    ("ctx.arc(head.x, head.y, 3.5, 0, Math.PI * 2);",
     "ctx.arc(head.x, head.y, 2, 0, Math.PI * 2);"),

    # ── Active tail -> white ──────────────────────────────────────────────────
    ("ctx.strokeStyle = 'rgba(236,200,74,' + (tt * 0.95) + ')';",
     "ctx.strokeStyle = 'rgba(255,255,255,' + (tt * 0.92) + ')';"),
    ("ctx.strokeStyle = 'rgba(255,230,130,' + (tt * 0.28) + ')';",
     "ctx.strokeStyle = 'rgba(210,230,255,' + (tt * 0.20) + ')';"),

    # ── Fading trail -> white ─────────────────────────────────────────────────
    ("ctx.strokeStyle = 'rgba(212,164,39,' + (f * 0.55) + ')';",
     "ctx.strokeStyle = 'rgba(255,255,255,' + (f * 0.50) + ')';"),
    ("ctx.strokeStyle = 'rgba(255,200,80,' + (f * 0.15) + ')';",
     "ctx.strokeStyle = 'rgba(210,230,255,' + (f * 0.14) + ')';"),
]

for old, new in changes:
    if not old:
        continue
    if old in c:
        c = c.replace(old, new, 1)
        print('OK:', old[:55])
    else:
        print('MISS:', old[:55])

with open('about-us.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('\nDone.')
