"""Independent re-read of the Gerber / Excellon files -> PNG, to check what the factory will see."""
import re, sys, glob, math
from PIL import Image, ImageDraw, ImageChops

PX = 16  # pixels per mm

def raster(path, W, H):
    img = Image.new("L", (int(W * PX), int(H * PX)), 0)
    dr = ImageDraw.Draw(img)
    s = open(path).read()
    aps = {}
    for n, kind, dims in re.findall(r"%ADD(\d+)([CRO]),([\d.X]+)\*%", s):
        aps[int(n)] = (kind, [float(v) for v in dims.split("X")])
    cur, x, y, pol, region, pts = None, 0, 0, 255, False, []
    def P(xx, yy):
        return (xx * PX, (H - yy) * PX)
    for cmd in re.findall(r"%[^%]*%|[^*%\n]+\*", s):
        cmd = cmd.strip()
        if cmd.startswith("%LP"):
            pol = 255 if cmd[3] == "D" else 0; continue
        if cmd.startswith("%"):
            continue
        m = re.match(r"D(\d+)\*$", cmd)
        if m and int(m.group(1)) >= 10:
            cur = aps[int(m.group(1))]; continue
        if cmd == "G36*":
            region, pts = True, []; continue
        if cmd == "G37*":
            if len(pts) > 2:
                dr.polygon(pts, fill=pol)
            region = False; continue
        m = re.match(r"X(-?\d+)Y(-?\d+)D0([123])\*", cmd)
        if not m:
            continue
        nx, ny, d = int(m.group(1)) / 1e6, int(m.group(2)) / 1e6, m.group(3)
        if region:
            if d == "2":
                pts = [P(nx, ny)]
            else:
                pts.append(P(nx, ny))
        elif d == "3":
            k, dims = cur
            cx, cy = P(nx, ny)
            w = dims[0] * PX / 2; h = (dims[1] if len(dims) > 1 else dims[0]) * PX / 2
            if k == "C":
                dr.ellipse([cx - w, cy - w, cx + w, cy + w], fill=pol)
            elif k == "R":
                dr.rectangle([cx - w, cy - h, cx + w, cy + h], fill=pol)
            else:
                r = min(w, h)
                dr.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=r, fill=pol)
        elif d == "1":
            k, dims = cur
            a, b = P(x, y), P(nx, ny)
            wd = dims[0] * PX
            dr.line([a, b], fill=pol, width=max(1, int(round(wd))))
            for c in (a, b):
                dr.ellipse([c[0] - wd / 2, c[1] - wd / 2, c[0] + wd / 2, c[1] + wd / 2], fill=pol)
        x, y = nx, ny
    return img

def drills(path, W, H):
    img = Image.new("L", (int(W * PX), int(H * PX)), 0)
    dr = ImageDraw.Draw(img)
    tools, cur = {}, None
    for line in open(path):
        line = line.strip()
        m = re.match(r"T(\d+)C([\d.]+)", line)
        if m:
            tools[m.group(1)] = float(m.group(2)); continue
        m = re.match(r"T(\d+)$", line)
        if m:
            cur = tools[m.group(1)]; continue
        m = re.match(r"X(-?[\d.]+)Y(-?[\d.]+)(?:G85X(-?[\d.]+)Y(-?[\d.]+))?", line)
        if m and cur:
            x1, y1 = float(m.group(1)), float(m.group(2))
            x2, y2 = (float(m.group(3)), float(m.group(4))) if m.group(3) else (x1, y1)
            r = cur * PX / 2
            for (a, b) in ((x1, y1), (x2, y2)):
                dr.ellipse([a * PX - r, (H - b) * PX - r, a * PX + r, (H - b) * PX + r], fill=255)
            dr.line([(x1 * PX, (H - y1) * PX), (x2 * PX, (H - y2) * PX)], fill=255, width=int(cur * PX))
    return img

def compose(d, name, W, H, panel=False):
    g = lambda suf: glob.glob(f"{d}/{name}-{suf}")[0]
    edge = raster(g("Edge_Cuts.gm1"), W, H)
    board = Image.new("L", edge.size, 0); ImageDraw.Draw(board).rectangle(edge.getbbox() or (0, 0, 1, 1), fill=255)
    holes = ImageChops.lighter(drills(g("PTH.drl"), W, H), drills(g("NPTH.drl"), W, H))
    out = []
    for side, cu, mk, sk in (("F", "F_Cu.gtl", "F_Mask.gts", "F_SilkS.gto"), ("B", "B_Cu.gbl", "B_Mask.gbs", "B_SilkS.gbo")):
        c, m, s = raster(g(cu), W, H), raster(g(mk), W, H), raster(g(sk), W, H)
        base = (17, 17, 17) if panel else (20, 90, 50)
        im = Image.new("RGB", edge.size, (217, 214, 208))
        im.paste(Image.new("RGB", edge.size, base), mask=board)
        if not panel:
            im.paste(Image.new("RGB", edge.size, (40, 120, 70)), mask=ImageChops.multiply(c, board))
        exposed = ImageChops.multiply(c, m)
        im.paste(Image.new("RGB", edge.size, (205, 205, 210) if panel else (210, 170, 80)), mask=exposed)
        s2 = ImageChops.subtract(s, m)                      # silk is removed over mask openings
        im.paste(Image.new("RGB", edge.size, (245, 245, 245)), mask=s2)
        im.paste(Image.new("RGB", edge.size, (217, 214, 208)), mask=holes)
        im.paste(Image.new("RGB", edge.size, (255, 0, 0)), mask=edge)
        if side == "B":
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(im)
    W2 = out[0].width * 2 + 40
    sheet = Image.new("RGB", (W2, out[0].height), (217, 214, 208))
    sheet.paste(out[0], (0, 0)); sheet.paste(out[1], (out[0].width + 40, 0))
    return sheet

if __name__ == "__main__":
    d, name, W, H, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
    compose(d, name, W, H, panel="panel" in name).save(out)
    print("saved", out)
