"""JLCPCB assembly files : CPL (positions) for the SMD parts on the back, and the BOM limited to those parts.
Coordinates match the Gerbers : X = x - 100, Y = 228.5 - y (mm)."""
import sys, json, csv, importlib
sys.path.insert(0, "/home/claude/work")
from kicadgen import FP

def make(mdir, mod, plp, bom_in, out_cpl, out_bom):
    sys.path.insert(0, mdir)
    m = importlib.import_module(mod)
    pl = json.load(open(plp))
    smd = [p for p in m.P if FP[pl[p["ref"]]["fp"]]["attr"] == "smd"]
    with open(out_cpl, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for p in smd:
            d = pl[p["ref"]]
            w.writerow([p["ref"], f"{d['X'] - 100:.3f}mm", f"{228.5 - d['Y']:.3f}mm", "Bottom" if d["side"] == "B" else "Top", int(d["rot"]) % 360])
    refs = {p["ref"] for p in smd}
    rows = list(csv.reader(open(bom_in)))
    with open(out_bom, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(rows[0])
        n = 0
        for r in rows[1:]:
            keep = [x for x in r[1].split(",") if x in refs]
            if keep:
                r[1] = ",".join(keep)
                if r[2].startswith("R_0603"):
                    r[0] = r[0].split(" ")[0] + (" 0.1%" if "0.1%" in r[0] else " 1%") + " 0603"
                w.writerow(r); n += len(keep)
    return len(smd), n

if __name__ == "__main__":
    print(make(*sys.argv[1:7]))
