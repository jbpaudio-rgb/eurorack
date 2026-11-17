import json, sys
sys.path.insert(0,'/home/claude/work'); import importlib; MD=sys.argv[1]; sys.path.insert(0,f'/home/claude/work/{MD}')
from kicadgen import FP, fp_bbox
M=importlib.import_module('parts'+MD); P,PANEL_W,PANEL_H=M.P,M.PANEL_W,M.PANEL_H
pl=json.load(open(f'/home/claude/work/{MD}/placement.json')); pj=json.load(open(f'/home/claude/work/{MD}/panel.json'))
OX=OY=100
items=[]
for p in P:
    d=pl[p['ref']]; fp=d['fp']; x=d['X']-OX; y=d['Y']-OY
    k=p['kind']
    if k=='JACK': items.append(dict(t='jack',x=x,y=y))
    elif k=='ROT12': items.append(dict(t='pot',x=x,y=y,s=1.15,a=15))
    elif k=='POT': items.append(dict(t='pot',x=x,y=y,s=0.8,a=-135))
    elif k=='TACT': items.append(dict(t='button',x=x,y=y))
    elif k=='PICO': items.append(dict(t='pico',x=x,y=y,rot=d['rot']))
    elif fp=='LED_THT:LED_D3.0mm': items.append(dict(t='led2',x=x+1.27,y=y,c=0xd0302a if 'rouge' in p['mpn'] else 0xffa020,e=0x8a0e0a if 'rouge' in p['mpn'] else 0x7a4a00))
    elif k=='SPDT': items.append(dict(t='toggle',x=x,y=y,rot=d['rot']))
    else:
        b=fp_bbox(fp,d['X'],d['Y'],d['rot'],'B',0)
        w=b[2]-b[0]; h=b[3]-b[1]; cx=(b[0]+b[2])/2-OX; cy=(b[1]+b[3])/2-OY
        name=fp.split(':')[1]
        if name.startswith(('R_','C_')):
            # body only (no pad overhang)
            L={'R_0805_2012Metric':(2.0,1.25,0.55),'C_0805_2012Metric':(2.0,1.25,0.9),'C_1206_3216Metric':(3.2,1.6,1.1),'R_0603_1608Metric':(1.6,0.8,0.45),'C_0603_1608Metric':(1.6,0.8,0.8)}[name]
            bw,bh=(L[0],L[1]) if d['rot']%180==0 else (L[1],L[0])
            items.append(dict(t='smd',x=x,y=y,w=bw,h=bh,z=L[2],c='#1b1b1b' if name.startswith('R') else '#b89b6a',ends=True,rot=d['rot']))
        elif 'SOIC' in name:
            items.append(dict(t='ic',x=x,y=y,w=7.5 if '24W' in name else 3.9,h=15.4 if '24W' in name else (9.9 if '16' in name else (8.7 if '14' in name else 4.9)),z=1.6,pins=12 if '24W' in name else (8 if '16' in name else (7 if '14' in name else 4))))
        elif 'SOT-223' in name:
            items.append(dict(t='smd',x=x,y=y,w=6.5,h=3.5,z=1.6,c='#222'))
        elif 'SOT' in name:
            items.append(dict(t='smd',x=x,y=y,w=1.6 if d['rot']%180==0 else 2.9,h=2.9 if d['rot']%180==0 else 1.6,z=1.1,c='#222'))
        elif 'SOD' in name or 'SMA' in name:
            L=(2.7,1.6,1.15) if 'SOD' in name else (4.4,2.7,2.2)
            bw,bh=(L[0],L[1]) if d['rot']%180==0 else (L[1],L[0])
            items.append(dict(t='smd',x=x,y=y,w=bw,h=bh,z=L[2],c='#151515',band=True,rot=d['rot']))
        elif 'IDC' in name or 'JST' in name:
            items.append(dict(t='header',x=cx,y=cy,w=w,h=h))
        elif '3362' in name or '3314' in name:
            items.append(dict(t='trim',x=cx,y=cy))
json.dump(dict(W=PANEL_W,H=PANEL_H,items=items,holes=pj['PANEL_HOLES'],text=pj['PANEL_TEXT'],div=pj['DIV'],strip=pj['STRIP'],ticks=pj['TICKS']),open(f'/home/claude/work/{MD}/scene.json','w'))
print(len(items))
