# Glow probe: finds the shots where the bloom glow changes nothing, so the final render can skip it there
# (bloom costs ~30 % of every frame on the cloud renderer). Renders 3 tiny frames per shot with and without bloom,
# compares them, and writes ENGINE/src/short/glow.json {"off": [shot ids with no visible glow]}. Then rebuild app.js.
#   python3 glowprobe.py --engine $W/engine
# Run it after the LAST check-stills round, right before the final render (any later change to sets or lights
# means running it again). Picture quality is unchanged: bloom stays on in every shot where it shows.
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument('--engine', required=True); a = ap.parse_args()
E = os.path.abspath(a.engine); H = os.path.dirname(os.path.abspath(__file__)); T = tempfile.mkdtemp(prefix='glow_')
subprocess.run(['npx', 'esbuild', 'src/short/story.ts', '--bundle', '--platform=node', '--format=cjs', '--outfile=' + T + '/story.js', '--log-level=error'], cwd=E, check=True)
shots = json.loads(subprocess.check_output(['node', '-e', f'const s=require("{T}/story.js");console.log(JSON.stringify(s.SHOTS.map(q=>[q.id,q.a,q.b])))']))
per = {i: sorted({a0 + 1, (a0 + b0) // 2, max(a0, b0 - 2)}) for i, a0, b0 in shots}
fr = sorted({f for v in per.values() for f in v})
json.dump({'off': []}, open(E + '/src/short/glow.json', 'w'))     # probe with bloom available everywhere
subprocess.run(['npx', 'esbuild', 'src/standalone.tsx', '--bundle', '--minify', '--format=iife', '--outfile=web/app.js', '--define:process.env.NODE_ENV="production"', '--log-level=error'], cwd=E, check=True)
for name, post in (('on', ''), ('off', '{"bloom":false}')):
    cmd = [sys.executable, H + '/render.py', '--web', E + '/web', '--out', T + '/' + name, '--list', ','.join(map(str, fr)), '--w', '270', '--sm', '1024']
    if post: cmd += ['--post', post]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
def glows(f):
    p, q = (np.asarray(Image.open(f'{T}/{d}/f_{f:05d}.png').convert('RGB'), int) for d in ('on', 'off'))
    return int((np.abs(p - q).max(2) > 8).sum()) > 25          # more than a few pixels brighter = a visible glow
off = [i for i, v in per.items() if not any(glows(f) for f in v)]
json.dump({'off': off}, open(E + '/src/short/glow.json', 'w'))
print('shots', len(per), 'glow needed', len(per) - len(off), 'bloom skipped in', len(off), off)
print('wrote', E + '/src/short/glow.json  -> now rebuild app.js')
