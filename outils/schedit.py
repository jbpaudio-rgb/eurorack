"""Edits on a label-connected schematic (octavio_mu style : every pin carries a local label, no wires)."""
import re, uuid

def lib_pins(s, lib):
    i = s.find('(symbol "%s"' % lib); d = 0
    for k in range(i, len(s)):
        if s[k] == '(': d += 1
        elif s[k] == ')':
            d -= 1
            if d == 0: b = s[i:k + 1]; break
    return {n: (float(x), float(y)) for x, y, n in re.findall(r'\(pin \w+ \w+ \(at ([\d.-]+) ([\d.-]+) \d+\).*?\(number "([^"]+)"', b, re.S)}

def sym(s, ref):
    m = re.search(r'\(symbol \(lib_id "([^"]+)"\) \(at ([\d.-]+) ([\d.-]+) 0\)[^\n]*\n\s*\(property "Reference" "%s"' % re.escape(ref), s)
    return m.group(1), float(m.group(2)), float(m.group(3))

def relabel(s, ref, pin, new):
    lib, X, Y = sym(s, ref); px, py = lib_pins(s, lib)[pin]
    x, y = X + px, Y - py
    pat = r'\(label "([^"]+)" \(at %s %s (\d+)\)' % (re.escape(('%g' % x)), re.escape(('%g' % y)))
    m = re.search(pat, s)
    if not m: raise KeyError((ref, pin, x, y))
    old = m.group(1)
    return s[:m.start()] + '(label "%s" (at %g %g %s)' % (new, x, y, m.group(2)) + s[m.end():], old

def set_value(s, ref, val):
    i = s.find('(property "Reference" "%s"' % ref)
    j = s.find('(property "Value" "', i)
    k = s.find('"', j + len('(property "Value" "'))
    return s[:j] + '(property "Value" "%s' % val + s[k:]

def add(s, template, ref, val, X, Y, pins, src=None):
    """src : text of another sheet to take the template symbol from (its lib symbol must exist in this sheet)."""
    T = src or s
    i = T.find('(property "Reference" "%s"' % template); j = T.rfind('(symbol (lib_id', 0, i); d = 0
    for k in range(j, len(T)):
        if T[k] == '(': d += 1
        elif T[k] == ')':
            d -= 1
            if d == 0: b = T[j:k + 1]; break
    lib, X0, Y0 = sym(T, template)
    if src:
        proj = re.search(r'\(instances \(project "([^"]+)" \(path "([^"]+)"', s)
        b = re.sub(r'\(instances \(project "[^"]+" \(path "[^"]+"', '(instances (project "%s" (path "%s"' % (proj.group(1), proj.group(2)), b)
    def mv(m):
        return '(at %g %g' % (float(m.group(1)) - X0 + X, float(m.group(2)) - Y0 + Y)
    b = re.sub(r'\(at ([\d.-]+) ([\d.-]+)', mv, b)
    b = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % uuid.uuid4(), b)
    b = b.replace('"Reference" "%s"' % template, '"Reference" "%s"' % ref).replace('(reference "%s")' % template, '(reference "%s")' % ref)
    b = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "%s"' % val, b, count=1)
    labs = []
    for pin, net in pins.items():
        px, py = lib_pins(s, lib)[pin]; x, y = X + px, Y - py
        left = px < 0
        labs.append('  (label "%s" (at %g %g %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'
                    % (net, x, y, 180 if left else 0, 'right' if left else 'left', uuid.uuid4()))
    k = s.rstrip().rfind('(sheet_instances')
    if k < 0: k = s.rstrip().rfind(')')
    return s[:k] + b + '\n' + '\n'.join(labs) + '\n  ' + s[k:]

def note(s, text, X, Y):
    k = s.rstrip().rfind('(sheet_instances')
    if k < 0: k = s.rstrip().rfind(')')
    return s[:k] + '(text "%s" (exclude_from_sim no) (at %g %g 0) (effects (font (size 1.8 1.8)) (justify left bottom)) (uuid "%s"))\n  ' % (text, X, Y, uuid.uuid4()) + s[k:]
