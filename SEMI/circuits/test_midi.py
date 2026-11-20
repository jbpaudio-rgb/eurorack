"""SPICE checks of the KEYBOARD · MIDI section and the speaker amplifier.  python3 test_midi.py"""
import os, subprocess, numpy as np, midi
W = os.environ.get('WORK', '/tmp/semi-midi'); os.makedirs(W, exist_ok=True)
OUT = []
def say(s): print(s); OUT.append(s)

def run(name, net, analysis, probes):
    cir = net + analysis + f"\n.control\nset filetype=ascii\nrun\nwrdata {W}/{name}.txt " + ' '.join(probes) + "\n.endc\n.options method=gear reltol=1e-4\n.end\n"
    open(f'{W}/{name}.cir', 'w').write(cir); r = subprocess.run(['ngspice', '-b', f'{W}/{name}.cir'], capture_output=True, text=True)
    d = np.loadtxt(f'{W}/{name}.txt'); return d[:, 0], [d[:, 2 * i + 1] for i in range(len(probes))]

def op(name, net, probes):
    t, v = run(name, net, ".tran 1u 50u", probes); return [x[-1] for x in v]

def bits(byte):          # UART frame : start (0), 8 data bits LSB first, stop (1) ; returns 1 where the line is pulled low
    b = [1] + [0 if (byte >> k) & 1 else 1 for k in range(8)] + [0]
    return b

def main():
    say('== MIDI IN (H11L1, sortie vers le RX du Pico à 3,3 V)')
    frame = bits(0x90) + bits(0x3C) + bits(0x64); T = 32e-6
    pwl = 'PWL(' + ' '.join(f'{k * T + (1e-9 if k else 0):.9g} {b} {(k + 1) * T - 1e-9:.9g} {b}' for k, b in enumerate(frame)) + ')'
    for snd in ('5V', '3V3'):
        t, (rx, il) = run('in' + snd, midi.midi_in(snd, pwl), '.tran 0.2u %g' % (len(frame) * T + 50e-6), ['v(RX)', 'v.xo.vsense#branch'])
        exp = np.repeat(frame, 1)
        # sample RX in the middle of each bit (as the UART does) : low on RX = bit 0
        mids = [(k + 0.5) * T for k in range(len(frame))]; got = [1 if np.interp(m, t, rx) < 1.0 else 0 for m in mids]
        err = sum(int(a != b) for a, b in zip(got, frame))
        # propagation delays : every edge of the line vs the same edge on RX
        line = np.array([np.interp(x, [k * T for k in range(len(frame))], frame) for x in t]) if False else None
        ein = [k * T for k in range(1, len(frame)) if frame[k] != frame[k - 1]]
        cross = np.where(np.diff((rx < 1.65).astype(int)) != 0)[0]; tc = t[cross]
        dl = [tc[np.argmin(abs(tc - e - 1e-6))] - e for e in ein if len(tc)]
        say(f'  émetteur {snd:3s} : courant LED {il.max() * 1e3:.1f} mA, RX de {rx.min():.2f} à {rx.max():.2f} V, {err} bit faux sur {len(frame)}, retard des fronts {min(dl) * 1e6:.1f} à {max(dl) * 1e6:.1f} µs (bit = 32 µs)')
    say('== MIDI OUT (3,3 V, 33 Ω / 10 Ω) vers une entrée MIDI standard (220 Ω + LED d optocoupleur)')
    for vtx, lab in ((0.0, 'bit 0 (TX bas)'), (3.3, 'repos (TX haut)')):
        net = midi.head() + f"VTX TX 0 DC {vtx}\nR4 P33 RING 33\nR5 TX TIP 10\nRR RING RA 220\nDR RA TIP LEDIR\n"
        i = op('out%g' % vtx, net, ['i(VTX)'])[0]
        say(f'  {lab:16s}: {abs(i) * 1e3:.1f} mA dans la LED du récepteur (MIDI demande ≈ 5 mA pour un 0, ≈ 0 au repos)')
    say('== Sorties CV (DAC MCP4822 → TL074)')
    for c in (0, 1475, 2048, 4095):
        cv, = op('cv%d' % c, midi.outputs(code_pitch=c), ['v(CV)']); say(f'  code {c:4d} : CV {cv:+.3f} V')
    a, = op('cva', midi.outputs(code_pitch=1000), ['v(CV)']); b, = op('cvb', midi.outputs(code_pitch=3000), ['v(CV)'])
    say(f'  pente {(b - a) / 2000 * 1e3:.3f} mV par pas → un demi-ton = {83.333 / ((b - a) / 2000 * 1e3):.1f} pas (≈ 3 cents par pas, calibré en 2 points)')
    v0, = op('vel0', midi.outputs(code_vel=0), ['v(VEL)']); v1, = op('vel1', midi.outputs(code_vel=4095), ['v(VEL)'])
    say(f'  VEL / MOD : de {v0:.3f} à {v1:.2f} V')
    g, t_ = op('gt1', midi.outputs(gate=3.3, trig=3.3), ['v(GATE)', 'v(TRIG)']); g0, t0 = op('gt0', midi.outputs(), ['v(GATE)', 'v(TRIG)'])
    say(f'  GATE {g0:.2f} / {g:.2f} V, TRIG {t0:.2f} / {t_:.2f} V')
    say('== Lecture de CV IN / GATE IN (CV → MIDI)')
    for cv in (-12, -10, -3.6, 0, 6.4, 10, 15):
        v, = op('adc%g' % cv, midi.sense(cv=cv), ['v(ADC)']); say(f'  CV {cv:+6.1f} V → ADC {v:.3f} V')
    for gt in (0, 1.0, 1.5, 2.5, 5, 10):
        v, = op('gs%g' % gt, midi.sense(gate=gt), ['v(GP9)']); say(f'  GATE {gt:4.1f} V → GP9 {v:.2f} V ({"gate" if v < 1 else "repos"})')
    say('== Haut-parleur (LM386, 8 Ω)')
    for a, lab in ((2.5, 'OUTPUT ±2,5 V'), (5, 'OUTPUT ±5 V'), (10, 'OUTPUT ±10 V (maximum)')):
        t, (s, ) = run('spk%g' % a, midi.speaker(amp=a), '.tran 2u 20m', ['v(SPK)'])
        m = t > 0.01; p = np.mean(s[m] ** 2) / 8; clip = s[m].max() > 0.95 * (5.0)
        say(f'  {lab:22s}: ±{np.ptp(s[m]) / 2:.2f} V sur le HP, {p * 1e3:.0f} mW{" (écrêté)" if clip else ""}')
    t, (s, ) = run('spkph', midi.speaker(amp=5, phones=True), '.tran 2u 20m', ['v(SPK)'])
    say(f'  casque branché : ±{np.ptp(s[t > 0.01]) / 2 * 1e3:.1f} mV sur le HP (coupé)')
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultats-midi.txt'), 'w').write('\n'.join(OUT) + '\n')

if __name__ == '__main__': main()
