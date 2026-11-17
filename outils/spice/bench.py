"""SPICE test benches for the ocTavio modules : the whole board (netlist from the .kicad_pcb) + sources on the jacks.
   python3 bench.py VCA            (or AD, ADSR, MIX, NOISETOOLS, SHLAG, RINGMOD, SPRINGREVERB, ATTINV, COMPLEX, all)
Each test prints what it measures next to what the module should do ; results also go to bench-<MODULE>.txt."""
import os, sys, json, subprocess, glob, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(os.path.dirname(H))
sys.path.insert(0, H); import kicad2spice as K
WORK = os.environ.get('BENCH_DIR', '/tmp/bench'); os.makedirs(WORK, exist_ok=True)

def sim(mod, name, cfg, probes):
    pcb = glob.glob(f'{R}/{mod}/*.kicad_pcb')[0]; sch = glob.glob(f'{R}/{mod}/*.kicad_sch')[0]
    base = f'{WORK}/{mod}-{name}'
    cfg = dict(cfg); cfg['extra'] = cfg.get('extra', '') + '\n.control\nset filetype=ascii\nrun\nwrdata %s.txt %s\n.endc' % (base, ' '.join('v(%s)' % p if not p.startswith('i(') else p for p in probes))
    txt = K.netlist(K.load(pcb, sch), cfg)
    if not cfg.get('osc'): txt = txt.replace('PWL(0 0 1m -12)', 'DC -12').replace('PWL(0 0 1m 12)', 'DC 12')
    open(base + '.cir', 'w').write(txt)
    r = subprocess.run(['ngspice', '-b', base + '.cir'], capture_output=True, text=True, timeout=1500)
    if not os.path.exists(base + '.txt'):
        print('   SIMULATION FAILED', name, (r.stdout + r.stderr)[-600:]); return None
    d = np.loadtxt(base + '.txt')
    out = {'t': d[:, 0]}
    for k, p in enumerate(probes): out[p] = d[:, 2 * k + 1]
    return out

def win(d, p, t0, t1=None):
    m = (d['t'] >= t0) & (d['t'] <= (t1 if t1 is not None else d['t'][-1])); return d['t'][m], d[p][m]

def pp(d, p, t0, t1=None):
    t, v = win(d, p, t0, t1); return v.max() - v.min(), v.mean(), v.min(), v.max()

def freq(d, p, t0):
    t, v = win(d, p, t0); v = v - (v.max() + v.min()) / 2
    z = np.where((v[:-1] < 0) & (v[1:] >= 0))[0]
    return (len(z) - 1) / (t[z[-1]] - t[z[0]]) if len(z) > 2 else 0.0

def spectrum(d, p, t0, fs=200000):
    t, v = win(d, p, t0); tu = np.arange(t[0], t[-1], 1 / fs); x = np.interp(tu, t, v); x = x - x.mean()
    S = np.abs(np.fft.rfft(x * np.hanning(len(x)))) * 4 / len(x); f = np.fft.rfftfreq(len(x), 1 / fs)
    return f, S

def at(f, S, f0):
    i = np.argmin(abs(f - f0)); return S[max(0, i - 3):i + 4].max()

LOG = []
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.append(s)

def T(mod, ts, step=None, osc=False, **kw):
    # default : DC supplies and a real operating point (bias capacitors already charged) ;
    # osc=True : supplies ramp from 0 V and the run starts from rest (uic), so oscillators start by themselves
    step = step or ts / 20000
    c = dict(kw); c['osc'] = osc; c['tran'] = '.tran %g %g 0 %g%s' % (step, ts, step, ' uic' if osc else ''); return c

SIN = lambda a, f, off=0: 'SIN(%g %g %g)' % (off, a, f)

# ------------------------------------------------------------------------------------------------ benches
def VCA():
    for cv in (0, 2.5, 5, 10):
        d = sim('VCA', 'cv%g' % cv, T('VCA', 0.012, drive={'J5': SIN(5, 1000), 'J2': 'DC %g' % cv}, pots={'RV5': 0.999, 'RV1': 0.001, 'RV4': 0.001}), ['OUTP', 'OUTN'])
        if d: a, m, lo, hi = pp(d, 'OUTP', 0.006); say(f'  LIN, IN 1 = ±5 V, CV 1 = {cv:>4} V : OUT+ {a / 2:6.2f} V crête, offset {m * 1e3:6.1f} mV')
    d = sim('VCA', 'exp', T('VCA', 0.012, drive={'J5': SIN(5, 1000), 'J2': 'DC 5'}, pots={'RV5': 0.999, 'RV1': 0.001, 'RV4': 0.999}), ['OUTP'])
    if d: say(f'  EXP, CV 1 = 5 V : OUT+ {pp(d, "OUTP", 0.006)[0] / 2:6.2f} V crête')
    d = sim('VCA', 'fix', T('VCA', 0.012, drive={'J5': SIN(5, 1000)}, pots={'RV1': 0.999, 'RV4': 0.001}), ['OUTP'])
    if d: say(f'  FIXED CONTROL VOLTAGE au maximum, sans CV : OUT+ {pp(d, "OUTP", 0.006)[0] / 2:6.2f} V crête')
    d = sim('VCA', 'bleed', T('VCA', 0.012, drive={'J5': 'DC 0', 'J2': 'PULSE(0 10 2m 1u 1u 4m 8m)'}, pots={'RV5': 0.999, 'RV1': 0.001}), ['OUTP'])
    bleed = lambda d: abs(pp(d, 'OUTP', 0.0045, 0.0058)[1] - pp(d, 'OUTP', 0.0075, 0.0098)[1])
    if d: say(f'  fuite de CV (entrée muette, CV 0→10 V) : OUT+ se décale de {bleed(d) * 1e3:6.1f} mV (trimmers au milieu)')
    best = None
    for x in (0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95):
        d = sim('VCA', 'rej%g' % x, T('VCA', 0.012, drive={'J5': 'DC 0', 'J2': 'PULSE(0 10 2m 1u 1u 4m 8m)'}, pots={'RV5': 0.999, 'RV1': 0.001, 'RV2': x}), ['OUTP'])
        if d:
            a = bleed(d)
            say(f'    RV2 {x:.2f} : {a * 1e3:.0f} mV')
            if best is None or a < best[1]: best = (x, a)
    if best: say(f'  réglage CV REJECT (RV2) : meilleure fuite {best[1] * 1e3:.0f} mV avec RV2 à {best[0]:.2f} de sa course')

def AD():
    d = sim('AD', 'one', T('AD', 0.25, drive={'J4': 'PULSE(0 10 5m 1u 1u 1m 1)'}, pots={'RV1': 0.3, 'RV2': 0.5}), ['OUTJ'])
    if d:
        t, v = win(d, 'OUTJ', 0); pk = v.argmax(); tp = t[pk] - 0.005
        after = np.where((t > t[pk]) & (v < 0.1 * v.max()))[0]; td = t[after[0]] - t[pk] if len(after) else float('nan')
        say(f'  ONE : crête {v.max():.2f} V (visé 9,3 V), attaque {tp * 1e3:.1f} ms, decay jusqu à 10 % {td * 1e3:.1f} ms, repos {v[-1]:.3f} V')
    d = sim('AD', 'cycle', T('AD', 0.25, osc=True, spdt={'SW1': '3'}, pots={'RV1': 0.2, 'RV2': 0.2}), ['OUTJ'])
    if d: a, m, lo, hi = pp(d, 'OUTJ', 0.05); say(f'  CYCLE : {freq(d, "OUTJ", 0.05):.1f} Hz, de {lo:.2f} à {hi:.2f} V')

def ADSR():
    d = sim('ADSR', 'gate', T('ADSR', 0.6, drive={'J2': 'PULSE(0 5 10m 1u 1u 300m 1)'}, pots={'RV1': 0.05, 'RV2': 0.2, 'RV3': 0.5, 'RV4': 0.2}), ['OUTJ', 'NOUTJ'])
    if d:
        t, v = win(d, 'OUTJ', 0); pk = v.argmax()
        sus = np.interp(0.29, t, v); rel = np.where((t > 0.31) & (v < 0.1 * sus))[0]
        say(f'  gate 300 ms : crête {v.max():.2f} V à {(t[pk] - 0.01) * 1e3:.1f} ms (visé 10 V), sustain {sus:.2f} V (bouton au milieu → visé 5 V), release à 10 % en {(t[rel[0]] - 0.31) * 1e3 if len(rel) else float("nan"):.0f} ms, fin {v[-1]:.2f} V, −OUT min {d["NOUTJ"].min():.2f} V')
    d = sim('ADSR', 'retrig', T('ADSR', 0.3, drive={'J2': 'PULSE(0 5 10m 1u 1u 20m 60m)'}, pots={'RV1': 0.001, 'RV2': 0.2, 'RV3': 0.3, 'RV4': 0.1}), ['OUTJ'])
    if d:
        t, v = win(d, 'OUTJ', 0); peaks = [win(d, 'OUTJ', a, a + 0.02)[1].max() for a in (0.01, 0.07, 0.13, 0.19)]
        say('  4 gates de 20 ms : crêtes ' + ', '.join('%.2f' % x for x in peaks) + ' V (doivent toutes atteindre ≈ 10 V)')

def MIX():
    d = sim('MIX', 'unity', T('MIX', 0.01, drive={'J2': SIN(2, 1000), 'J3': 'DC 1'}, pots={'RV1': 0.999, 'RV2': 0.999, 'RV3': 0.001, 'RV4': 0.001, 'RV5': 0.001}), ['OUTJ', 'NOUTJ'])
    if d: a, m, lo, hi = pp(d, 'OUTJ', 0.004); say(f'  IN 1 = ±2 V sinus + IN 2 = 1 V, niveaux à fond, MASTER au minimum : OUT ±{a / 2:.2f} V autour de {m:.2f} V, −OUT autour de {pp(d, "NOUTJ", 0.004)[1]:.2f} V')
    d = sim('MIX', 'drive', T('MIX', 0.01, drive={'J2': SIN(5, 1000)}, pots={'RV1': 0.999, 'RV5': 0.999}), ['OUTJ'])
    if d:
        f, S = spectrum(d, 'OUTJ', 0.004); a = pp(d, 'OUTJ', 0.004)
        say(f'  IN 1 = ±5 V, MASTER à fond : OUT de {a[2]:.2f} à {a[3]:.2f} V, 3e harmonique {20 * np.log10(at(f, S, 3000) / at(f, S, 1000)):.0f} dB (saturation douce)')

def NOISETOOLS():
    d = sim('NOISETOOLS', 'clk', T('NOISETOOLS', 0.4, step=20e-6, osc=True, drive={'J5': 'SIN(0 5 3)'}, pots={'RV1': 0.6, 'RV2': 0.3}), ['PULSEJ', 'SHOUTJ', 'SLOUTJ', 'WHITEJ', 'PINKJ'])
    if d:
        say(f'  PULSE : {freq(d, "PULSEJ", 0.05):.1f} Hz, de {d["PULSEJ"].min():.2f} à {d["PULSEJ"].max():.2f} V')
        t, v = win(d, 'SHOUTJ', 0.05); steps = np.sum(np.abs(np.diff(v)) > 0.05)
        say(f'  S&H (entrée = sinus 3 Hz, TRIG = PULSE) : {steps} paliers, de {v.min():.2f} à {v.max():.2f} V ; SLEW de {d["SLOUTJ"].min():.2f} à {d["SLOUTJ"].max():.2f} V')
        say(f'  bruit (SPICE ne fait pas de bruit d avalanche : on vérifie la polarisation) : WHITE moyen {pp(d, "WHITEJ", 0.05)[1]:.2f} V, PINK moyen {pp(d, "PINKJ", 0.05)[1]:.2f} V (doivent être ≈ 0 V)')

def SHLAG():
    d = sim('SHLAG', 'clk', T('SHLAG', 0.4, step=20e-6, osc=True, drive={'J2': 'SIN(0 5 3)'}, pots={'RV1': 0.6, 'RV2': 0.3, 'RV3': 0.3}), ['CLOCKJ', 'SHOUTJ', 'GATEJ', 'LAGOUTJ', 'NOISEJ'])
    if d:
        say(f'  CLOCK : {freq(d, "CLOCKJ", 0.05):.1f} Hz, de {d["CLOCKJ"].min():.2f} à {d["CLOCKJ"].max():.2f} V')
        t, v = win(d, 'SHOUTJ', 0.05)
        say(f'  S&H (entrée = sinus 3 Hz) : {np.sum(np.abs(np.diff(v)) > 0.05)} paliers, de {v.min():.2f} à {v.max():.2f} V ; GATE de {d["GATEJ"].min():.2f} à {d["GATEJ"].max():.2f} V ; LAG de {d["LAGOUTJ"].min():.2f} à {d["LAGOUTJ"].max():.2f} V')
        say(f'  NOISE moyen {pp(d, "NOISEJ", 0.05)[1]:.2f} V (polarisation, doit être ≈ 0 V)')

def RINGMOD():
    d = sim('RINGMOD', 'xy', T('RINGMOD', 0.06, step=2e-6, drive={'J2': SIN(5, 1000), 'J3': SIN(5, 150)}, pots={'RV1': 0.6, 'RV2': 0.6, 'RV3': 0.999}), ['RINGJ', 'OUTJ'])
    if d:
        f, S = spectrum(d, 'RINGJ', 0.02); main = max(at(f, S, 850), at(f, S, 1150))
        say(f'  X = 1 kHz ±5 V, Y = 150 Hz ±5 V : RING ±{pp(d, "RINGJ", 0.02)[0] / 2:.2f} V ; bandes 850 / 1150 Hz {20 * np.log10(at(f, S, 850) + 1e-9):.1f} / {20 * np.log10(at(f, S, 1150) + 1e-9):.1f} dBV ; fuite X (1 kHz) {20 * np.log10(at(f, S, 1000) / main):.0f} dB, fuite Y (150 Hz) {20 * np.log10(at(f, S, 150) / main):.0f} dB (trimmers au milieu)')
    d = sim('RINGMOD', 'vca', T('RINGMOD', 0.02, step=2e-6, drive={'J2': SIN(5, 1000)}, pots={'RV1': 0.6, 'RV2': 0.6, 'RV3': 0.999}), ['RINGJ'])
    if d: say(f'  Y vide (+5 V) : RING ±{pp(d, "RINGJ", 0.01)[0] / 2:.2f} V (le module devient un VCA)')

TANK = {'J10': 'VTK P1 tk 0\nRTK tk P2 1475', 'J11': 'BTK tx P2 V=0.6*i(VTK)\nRTO tx P1 2250'}
def SPRINGREVERB():
    for mix in (0.001, 0.5, 0.999):
        d = sim('SPRINGREVERB', 'mix%g' % mix, T('SPRINGREVERB', 0.012, step=2e-6, conn=TANK, drive={'J2': SIN(2, 1000)}, pots={'RV1': 0.5, 'RV2': 0.5, 'RV3': mix}), ['SENDJ', 'WETJ', 'OUTJ', 'i(VTK)', 'TANKOUT'])
        if d:
            say(f'  IN ±2 V, DRIVE au milieu, MIX {mix:.1f} : courant dans la cuve ±{pp(d, "i(VTK)", 0.004)[0] / 2 * 1e3:.2f} mA, retour cuve ±{pp(d, "TANKOUT", 0.004)[0] / 2 * 1e3:.2f} mV, WET ±{pp(d, "WETJ", 0.004)[0] / 2:.2f} V, OUT ±{pp(d, "OUTJ", 0.004)[0] / 2:.2f} V')

def ATTINV():
    for sw, pos, lab in (('1', 0.999, 'INV, bouton à fond'), ('1', 0.5, 'INV, bouton au milieu'), ('1', 0.001, 'INV, bouton au minimum'), ('3', 0.999, 'ATT, bouton à fond'), ('3', 0.5, 'ATT, bouton au milieu')):
        d = sim('ATTINV', 'g%s%g' % (sw, pos), T('ATTINV', 0.006, drive={'J2': SIN(5, 1000)}, spdt={'SW1': sw, 'SW2': sw}, pots={'RV1': pos, 'RV2': pos}), ['OUTJ1', 'OUTJ2', 'INJ1'])
        if d:
            t, v = win(d, 'OUTJ1', 0.003); _, x = win(d, 'INJ1', 0.003); g = np.polyfit(x, v, 1)[0]
            say(f'  {lab:24s}: gain {g:+.2f} ; canal 2 vide (+5 V) → OUT 2 = {pp(d, "OUTJ2", 0.003)[1]:+.2f} V')

def COMPLEX():
    pcb = glob.glob(f'{R}/COMPLEX/*.kicad_pcb')[0]; sch = glob.glob(f'{R}/COMPLEX/*.kicad_sch')[0]
    P = K.load(pcb, sch); outs = [(r, p['pads']['T'], p['value']) for r, p in sorted(P.items()) if p['lib'] == 'JACK' and 'TN' not in p['pads']]
    d = sim('COMPLEX', 'run', T('COMPLEX', 0.03, step=1e-6, osc=True), [n for _, n, _ in outs])
    if d:
        for r, n, v in outs:
            a = pp(d, n, 0.01); say(f'  {v:10s} : {freq(d, n, 0.01):8.1f} Hz, de {a[2]:6.2f} à {a[3]:6.2f} V')

ALL = ['VCA', 'AD', 'ADSR', 'MIX', 'NOISETOOLS', 'SHLAG', 'RINGMOD', 'SPRINGREVERB', 'ATTINV', 'COMPLEX']
if __name__ == '__main__':
    mods = ALL if sys.argv[1] == 'all' else sys.argv[1:]
    for m in mods:
        LOG.clear(); say('== ' + m); globals()[m]()
        open(os.path.join(H, 'bench-%s.txt' % m), 'w').write('\n'.join(LOG) + '\n')
