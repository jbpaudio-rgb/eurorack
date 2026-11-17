import sys, importlib, json, glob, math
MD=sys.argv[1]; sys.path.insert(0,'/home/claude/work'); sys.path.insert(0,f'/home/claude/work/{MD}')
M=importlib.import_module('parts'+MD); P=M.P
import re
def parse(s):
    toks=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s)
    st=[[]]
    for t in toks:
        if t=='(':st.append([])
        elif t==')':
            x=st.pop(); st[-1].append(x)
        else: st[-1].append(t)
    assert len(st)==1 and len(st[0])==1
    return st[0][0]
from kicadgen import FP, pad_abs
OUTD='out/'+M.FOLDER
bad=0
for fn in glob.glob(OUTD+'/**/*.kicad_*',recursive=True)+glob.glob(OUTD+'/**/*.kicad_mod',recursive=True):
    if fn.endswith('.kicad_pro'): continue
    try: parse(open(fn).read())
    except Exception as e: print('FAIL',fn,e); bad+=1
print('files ok' if not bad else 'FILES BAD')
from collections import Counter
c=Counter(n for p in P for n in p['pins'].values() if n)
print('single-pin nets:',[n for n,k in c.items() if k<2])
s=parse(open(f'{OUTD}/{M.PROJ}.kicad_sch').read())
libs={}
for it in s:
    if isinstance(it,list) and it[0]=='lib_symbols':
        for sym in it[1:]:
            name=sym[1].strip('"'); pins={}
            for sub in sym:
                if isinstance(sub,list) and sub[0]=='symbol':
                    for pp in sub:
                        if isinstance(pp,list) and pp[0]=='pin':
                            at=[x for x in pp if isinstance(x,list) and x[0]=='at'][0]
                            num=[x for x in pp if isinstance(x,list) and x[0]=='number'][0][1].strip('"')
                            pins[num]=(float(at[1]),float(at[2]))
            libs[name]=pins
labels={}
pinpos={}
boxes=[]
for it in s:
    if not isinstance(it,list): continue
    if it[0]=='label':
        at=[x for x in it if isinstance(x,list) and x[0]=='at'][0]
        k=(round(float(at[1]),3),round(float(at[2]),3)); labels.setdefault(k,set()).add(it[1].strip('"'))
    if it[0]=='symbol':
        lid=[x for x in it if isinstance(x,list) and x[0]=='lib_id'][0][1].strip('"')
        at=[x for x in it if isinstance(x,list) and x[0]=='at'][0]
        ref=[x for x in it if isinstance(x,list) and x[0]=='property' and x[1]=='"Reference"'][0][2].strip('"')
        sx,sy=float(at[1]),float(at[2])
        for num,(px,py) in libs[lid].items():
            pinpos[(ref,num)]=(round(sx+px,3),round(sy-py,3))
bad=[k for k,v in labels.items() if len(v)>1]
print('conflicting label points',bad)
pm={p['ref']:p for p in P}; err=0
for (ref,num),pt in pinpos.items():
    want=pm[ref]['pins'].get(num)
    got=labels.get(pt)
    if want and (not got or want not in got): err+=1; print('mismatch',ref,num,want,got)
# collisions: pins of different parts at same point
from collections import Counter
c=Counter(pinpos.values()); print('shared pin points',[k for k,v in c.items() if v>1]); print('errors',err,'pins',len(pinpos))

pl=json.load(open(f'/home/claude/work/{MD}/placement.json'))
pads=[]
for r,d in pl.items():
    for (n,x,y,w,h,kind) in pad_abs(d['fp'],d['X'],d['Y'],d['rot'],d['side']):
        pads.append((r,n,x,y,w,h,'*' if kind!='smd' else d['side']))
ov=[]
for i in range(len(pads)):
    for j in range(i+1,len(pads)):
        A,B=pads[i],pads[j]
        if A[0]==B[0]: continue
        if A[6]!='*' and B[6]!='*' and A[6]!=B[6]: continue
        dx=abs(A[2]-B[2])-(A[4]+B[4])/2; dy=abs(A[3]-B[3])-(A[5]+B[5])/2
        if max(dx,dy)<0.25: ov.append((A[0],A[1],B[0],B[1],round(max(dx,dy),2)))
print('pad clashes (<0.25 mm):',ov)
