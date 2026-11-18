"""SPICE checks of the SEMI state-variable filter.  python3 test_svf.py"""
import os, subprocess, numpy as np, svf
W = os.environ.get('WORK', '/tmp/semi-svf'); os.makedirs(W, exist_ok=True)
OUT = []
def say(s): print(s); OUT.append(s)

def ac(name, **kw):
    kw.setdefault('vin', 'DC 0 AC 1')
    cir = svf.netlist(analysis=f".control\nset filetype=ascii\nac dec 50 5 50k\nwrdata {W}/{name}.txt vdb(OUT) vdb(LP) vdb(BP) vdb(HP)\n.endc", **kw)
    open(f'{W}/{name}.cir', 'w').write(cir); subprocess.run(['ngspice', '-b', f'{W}/{name}.cir'], capture_output=True)
    d = np.loadtxt(f'{W}/{name}.txt'); return d[:, 0], d[:, 1], d[:, 3], d[:, 5], d[:, 7]

def tran(name, t, step, probes, **kw):
    cir = svf.netlist(analysis=f".tran {step} {t} 0 {step}\n.control\nset filetype=ascii\nrun\nwrdata {W}/{name}.txt " + ' '.join('v(%s)' % p for p in probes) + "\n.endc", **kw)
    open(f'{W}/{name}.cir', 'w').write(cir); subprocess.run(['ngspice', '-b', f'{W}/{name}.cir'], capture_output=True)
    d = np.loadtxt(f'{W}/{name}.txt'); return d[:, 0], {p: d[:, 2 * i + 1] for i, p in enumerate(probes)}

def fc_lp(f, g):  # -3 dB point of the LP (12 dB : at the corner with Q 0.707 ; here : -3 dB from the passband)
    ref = g[f < f[0] * 2].mean(); i = np.where(g < ref - 3)[0]; return f[i[0]] if len(i) else np.nan

def f_peak(f, g): return f[np.argmax(g)]

def main():
    say('== Plage de FREQUENCY (RESONANCE au minimum, Q = 0,5 ; on lit le centre du passe-bande)')
    cent = {}
    for x in (0.0, 0.25, 0.5, 0.75, 1.0):
        f, o, lp, bp, hp = ac('f%g' % x, freq=x); cent[x] = f_peak(f, bp)
        say(f'  FREQ {x:.2f} : centre {cent[x]:8.1f} Hz')
    say(f'  -> {np.log2(cent[1.0] / cent[0.0]):.1f} octaves sur la course (visé ≈ 10)')
    say('== Pentes et modes (FREQ 0,5)')
    f, o, lp, bp, hp = ac('slopes', freq=0.5, reso=0.5)
    fc = f_peak(f, bp)
    for nm, g in (('LP', lp), ('HP', hp)):
        a, b = (fc * 4, fc * 8) if nm == 'LP' else (fc / 4, fc / 8)
        say(f'  {nm} : pente {np.interp(b, f, g) - np.interp(a, f, g):+.1f} dB par octave loin de la coupure (visé ≈ −12)')
    say(f'  BP : −{np.interp(fc, f, bp) - np.interp(fc / 8, f, bp):.1f} dB à 3 octaves sous le centre, −{np.interp(fc, f, bp) - np.interp(fc * 8, f, bp):.1f} dB à 3 octaves au-dessus (visé ≈ 18)')
    for m, lab in ((0.0, 'MODE en bas (LP)'), (0.5, 'MODE au milieu (NOTCH)'), (1.0, 'MODE en haut (HP)')):
        f, o, *_ = ac('mode%g' % m, freq=0.5, reso=0.3, mode=m)
        say(f'  {lab:24s}: OUT à 30 Hz {np.interp(30, f, o):6.1f} dB, au centre {np.interp(fc, f, o):6.1f} dB, à 10 kHz {np.interp(10000, f, o):6.1f} dB')
    f, o, *_ = ac('bpsw', freq=0.5, reso=0.3, bp=True)
    say(f'  inverseur BP            : OUT à 30 Hz {np.interp(30, f, o):6.1f} dB, au centre {np.interp(fc, f, o):6.1f} dB, à 10 kHz {np.interp(10000, f, o):6.1f} dB')
    say('== RESONANCE (FREQ 0,5)')
    for r in (0.0, 0.5, 0.8, 0.9, 0.95):
        f, o, lp, bp, hp = ac('q%g' % r, freq=0.5, reso=r)
        pk = lp.max() - lp[f < 20].mean()
        say(f'  RESONANCE {r:.2f} : bosse du LP {pk:+5.1f} dB à {f_peak(f, lp):.0f} Hz')
    t, d = tran('osc', 0.4, 4e-6, ['OUT', 'HP', 'BP'], freq=0.5, reso=1.0, vin='PULSE(0 0.2 1m 1u 1u 0.2m 1)')
    m = t > 0.3; z = np.where((d['BP'][m][:-1] < 0) & (d['BP'][m][1:] >= 0))[0]; tt = t[m]
    fo = (len(z) - 1) / (tt[z[-1]] - tt[z[0]]) if len(z) > 2 else 0
    say(f'  RESONANCE à fond, sans entrée : auto-oscillation {fo:.0f} Hz, BP ±{np.ptp(d["BP"][m]) / 2:.2f} V, OUT ±{np.ptp(d["OUT"][m]) / 2:.2f} V')
    say('== Entrées de CV (FREQ 0,3)')
    f, o, lp, bp, hp = ac('cv0', freq=0.3); c0 = f_peak(f, bp)
    f, o, lp, bp, hp = ac('cve', freq=0.3, env_amt=1.0, venv='DC 5'); ce = f_peak(f, bp)
    f, o, lp, bp, hp = ac('cvm', freq=0.3, mod_amt=1.0, vmod='DC 4'); cm = f_peak(f, bp)
    say(f'  ENV à fond, +5 V : {np.log2(ce / c0) / 5:.2f} oct/V (visé 0,8) ; MOD à fond, +4 V : {np.log2(cm / c0) / 4:.2f} oct/V (visé 0,5)')
    say('== Niveau et saturation (sinus 200 Hz : FREQ à fond, puis coupure sur le sinus avec RESONANCE 0,5)')
    for a, fq, rs in ((2, 1.0, 0.0), (5, 1.0, 0.0), (10, 1.0, 0.0), (2, 0.31, 0.5), (5, 0.31, 0.5), (10, 0.31, 0.5)):
        t, d = tran('sat%g_%g' % (a, fq), 0.03, 2e-6, ['OUT'], freq=fq, reso=rs, vin=f'SIN(0 {a} 200)')
        m = t > 0.01; x = d['OUT'][m]; tu = np.linspace(t[m][0], t[m][-1], 2 ** 14); y = np.interp(tu, t[m], x)
        S = np.abs(np.fft.rfft(y * np.hanning(len(y)))); fr = np.fft.rfftfreq(len(y), tu[1] - tu[0])
        h = lambda k: S[np.argmin(abs(fr - 200 * k)) - 2:np.argmin(abs(fr - 200 * k)) + 3].max()
        thd = np.sqrt(sum(h(k) ** 2 for k in range(2, 8))) / h(1) * 100
        say(f'  FREQ {fq:.2f}, entrée ±{a:>2} V : sortie ±{np.ptp(x) / 2:.2f} V, distorsion {thd:.2f} %')
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultats-svf.txt'), 'w').write('\n'.join(OUT) + '\n')

if __name__ == '__main__': main()
