"""SPICE checks of the SEMI LFO.  python3 test_lfo.py"""
import os, subprocess, numpy as np, lfo
W = os.environ.get('WORK', '/tmp/semi-lfo'); os.makedirs(W, exist_ok=True)
OUT = []
def say(s): print(s); OUT.append(s)

def run(name, cycles_hint_hz, n_cycles=6, **kw):
    T = n_cycles / cycles_hint_hz; step = T / 40000
    cir = lfo.netlist(analysis=f".tran {step:.4g} {T:.4g} 0 {step:.4g} uic\n.control\nset filetype=ascii\nrun\nwrdata {W}/{name}.txt v(OUT) v(SQ) v(TRIG) v(S) i(VP)\n.endc", **kw)
    cir = cir.replace('VP P12 0 DC 12', 'VP P12 0 PWL(0 0 1m 12)').replace('VM M12 0 DC -12', 'VM M12 0 PWL(0 0 1m -12)')
    open(f'{W}/{name}.cir', 'w').write(cir); subprocess.run(['ngspice', '-b', f'{W}/{name}.cir'], capture_output=True, timeout=1500)
    d = np.loadtxt(f'{W}/{name}.txt'); return d[:, 0], d[:, 1], d[:, 3], d[:, 5], d[:, 7]

def analyse(t, out, sq, trig, s):
    m = t > t[-1] * 0.3; t, out, sq, trig, s = t[m], out[m], sq[m], trig[m], s[m]
    fall = np.where((s[:-1] > 0) & (s[1:] <= 0))[0]      # S falls = start of the rising part
    if len(fall) < 3: return None
    per = np.diff(t[fall]).mean(); f = 1 / per
    a, b = fall[-2], fall[-1]; seg_t, seg = t[a:b], out[a:b]
    rise = (seg_t[np.argmax(seg)] - seg_t[0]) / per        # part of the cycle spent rising
    tr = trig > 5; edges = np.where(np.diff(tr.astype(int)) == 1)[0]; ends = np.where(np.diff(tr.astype(int)) == -1)[0]
    w = (t[ends[ends > edges[0]][0]] - t[edges[0]]) * 1e3 if len(edges) and len(ends[ends > edges[0]]) else np.nan
    return f, rise, out.min(), out.max(), sq.min(), sq.max(), trig.max(), w

def main():
    say('== RATE (WAVE au triangle)')
    fr = {}
    for x, hint in ((0.0, 0.02), (0.25, 0.15), (0.5, 1.0), (0.75, 7), (1.0, 50)):
        r = analyse(*run('r%g' % x, hint, rate=x, wave=0.5))
        if r: fr[x] = r[0]; say(f'  RATE {x:.2f} : {r[0]:8.3f} Hz, OUT de {r[2]:.2f} à {r[3]:.2f} V')
        else: say(f'  RATE {x:.2f} : pas d oscillation mesurée')
    if 0.0 in fr and 1.0 in fr: say(f'  -> {np.log2(fr[1.0] / fr[0.0]):.1f} octaves (visé 0,02 → 50 Hz = 11,3)')
    say('== RATE CV (RATE 0,5)')
    b = analyse(*run('cv0', 1.0, rate=0.5, wave=0.5))
    for v in (-2, 1, 2):
        r = analyse(*run('cv%g' % v, 1.0 * 2 ** v, rate=0.5, wave=0.5, vcv='DC %g' % v))
        if r and b: say(f'  CV {v:+d} V : × {r[0] / b[0]:.3f} (visé × {2 ** v:g}), soit {np.log2(r[0] / b[0]) / v:.3f} oct/V')
    say('== WAVE (RATE 0,5) : la vitesse doit rester la même')
    for wv, lab in ((0.0, 'RAMPE ↑'), (0.25, ''), (0.5, 'TRIANGLE'), (0.75, ''), (1.0, 'RAMPE ↓')):
        r = analyse(*run('w%g' % wv, 1.0, rate=0.5, wave=wv))
        if r: say(f'  WAVE {wv:.2f} {lab:9s}: {r[0]:.3f} Hz, montée = {r[1] * 100:4.1f} % du cycle')
    r = analyse(*run('w5', 1.0, rate=0.5, wave=0.5))
    if r: say(f'== Sorties : SQ de {r[4]:.2f} à {r[5]:.2f} V ; TRIG {r[6]:.2f} V pendant {r[7]:.1f} ms au début de chaque montée')
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultats-lfo.txt'), 'w').write('\n'.join(OUT) + '\n')

if __name__ == '__main__': main()
