#!/usr/bin/env python3
"""Draw a hand-drawn sequence diagram group. Usage: sequence.py spec.json > group.svg
spec: {"x":612,"y":198,"w":604,"lifelines":["Customer","Server"],"sections":[{"name":"Order","messages":[[0,1,"POST /orders"],[1,0,"302 /receipt"]]}]}
Message = [from index, to index, label]. Right arrows are amber, left arrows are the secondary green."""
import json, sys
AMBER, GREEN, RULE, TEXT, MONO = '#FFBF00', '#88C996', '#185E2B', '#B8FFCC', 'font-family="Share Tech Mono, ui-monospace, monospace"'
s = json.load(sys.stdin); x0, y0, w = s['x'], s['y'], s['w']
n = len(s['lifelines']); xs = [round(x0 + 68 + i * (w - 136) / (n - 1)) for i in range(n)]
rows = sum(len(sec['messages']) for sec in s['sections']); h = 24 * len(s['sections']) + 26 * rows + 20
out = [f'  <g id="sequence" data-pptx-bounds="{x0} {y0} {w} {h + 60}">']
for i, (name, x) in enumerate(zip(s['lifelines'], xs)):
    out.append(f'    <text x="{x}" y="{y0 + 24}" font-size="20" fill="{TEXT}" text-anchor="middle">{name}</text>')
    out.append(f'    <path d="M {x} {y0 + 36} Q {x + (0.7, -0.6)[i % 2]} {y0 + 36 + h / 2:g} {x} {y0 + 36 + h}" fill="none" stroke-linecap="round" stroke="{RULE}" stroke-width="1.5" />')
top = y0 + 42
out.append(f'    <path d="M {x0 + 0.6} {top} L {x0 + w - 0.8} {top + 0.7} L {x0 + w - 1.5} {top + h - 4} L {x0 - 0.1} {top + h - 5} Z" stroke-linejoin="round" fill="none" stroke="{RULE}" stroke-width="1.5" />')
y, k = top, 0
for si, sec in enumerate(s['sections']):
    if si:
        out.append(f'    <path d="M {x0} {y} Q {x0 + w / 2:g} {y + 0.8} {x0 + w} {y}" fill="none" stroke-linecap="round" stroke="{RULE}" stroke-width="1.5" stroke-dasharray="6 6" />')
    out.append(f'    <text x="{x0 + w - 8}" y="{y + 18}" font-size="14" fill="{GREEN}" text-anchor="end">{sec["name"]}</text>')
    y += 24
    for a, b, label in sec['messages']:
        d = 1 if b > a else -1; col = AMBER if d > 0 else GREEN
        p, q = xs[a] + 5 * d, xs[b] - 5 * d
        out.append(f'    <path d="M {p} {y} Q {(p + q) / 2:g} {y + (0.6, -0.8, 1.0, -0.5)[k % 4]} {q} {y}" fill="none" stroke-linecap="round" stroke="{col}" stroke-width="1.5" />')
        out.append(f'    <path d="M {q - 9 * d} {y - 5} L {q} {y} L {q - 9 * d} {y + 5}" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke="{col}" stroke-width="1.5" />')
        out.append(f'    <text x="{(xs[a] + xs[b]) / 2:g}" y="{y - 6}" {MONO} font-size="13" fill="{col}" text-anchor="middle">{label}</text>')
        y += 26; k += 1
    y -= 8
out.append('  </g>')
print('\n'.join(out))
