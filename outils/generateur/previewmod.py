import json, sys, math, matplotlib
sys.path.insert(0,'/home/claude/work'); import importlib; MD=sys.argv[1]; sys.path.insert(0,f'/home/claude/work/{MD}')
matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
from kicadgen import FP, pad_abs, fp_bbox
M=importlib.import_module('parts'+MD); P,PANEL_W,PANEL_H=M.P,M.PANEL_W,M.PANEL_H
pj=json.load(open(f'/home/claude/work/{MD}/panel.json')); pl=json.load(open(f'/home/claude/work/{MD}/placement.json'))
OX=OY=100; OUT='/home/claude/work/out/'+M.FOLDER+'/'
SMALL=set()
Wi=2.6; ppm=Wi*72/(PANEL_W+6)
fig=plt.figure(figsize=(Wi,Wi*(PANEL_H+6)/(PANEL_W+6)),dpi=220)
ax=fig.add_axes([0,0,1,1]); ax.set_xlim(-3,PANEL_W+3); ax.set_ylim(PANEL_H+3,-3); ax.set_aspect('auto'); ax.axis('off'); fig.patch.set_facecolor('#d9d6d0')
ax.add_patch(Rectangle((0,0),PANEL_W,PANEL_H,fc='#111111',ec='#555'))
for x0,x1 in ((pj['STRIP'][0]-0.3,pj['STRIP'][1]),(PANEL_W-pj['STRIP'][1],PANEL_W-pj['STRIP'][0]+0.3)):
    ax.imshow(np.linspace(0,1,32).reshape(1,-1),extent=(x0,x1,PANEL_H,0),cmap=LinearSegmentedColormap.from_list('al',['#8d8d8d','#e6e6e6','#9c9c9c']),aspect='auto',zorder=2)
for hx,hy,d,ov in pj['PANEL_HOLES']:
    if ov: ax.add_patch(FancyBboxPatch((hx-ov[0]/2+1.6,hy-1.6),ov[0]-3.2,3.2,boxstyle='round,pad=0,rounding_size=1.6',fc='#d9d6d0',ec='none'))
for p in P:
    if p['side']!='F': continue
    x,y=p['pos']
    if p['kind']=='POT':
        k=0.8
        ax.add_patch(Circle((x,y),5.4*k,fc='#151515',ec='#777',lw=0.6)); ax.add_patch(Circle((x,y),3.4*k,fc='#b9b4a6',ec='#666',lw=0.4))
        ax.plot([x-2.3*k,x-3.8*k],[y+3.2*k,y+4.6*k],color='white',lw=1.0)
    elif p['kind']=='ROT12':
        import math as mm
        ax.add_patch(Circle((x,y),6.3,fc='#0d0d0d',ec='#888',lw=0.7)); ax.add_patch(Circle((x,y),4.2,fc='#b9b4a6',ec='#666',lw=0.4))
        a=mm.radians(15); ax.plot([x+2.0*mm.sin(a),x+6.0*mm.sin(a)],[y-2.0*mm.cos(a),y-6.0*mm.cos(a)],color='white',lw=1.6)
    elif p['kind']=='JACK':
        ax.add_patch(Circle((x,y),3.6,fc='#a8a49a',ec='#666',lw=0.4)); ax.add_patch(Circle((x,y),1.8,fc='#050505'))
    elif p['kind']=='SPDT':
        ax.add_patch(Circle((x,y),3.0,fc='#9a9a9a',ec='#666',lw=0.4)); ax.plot([x,x-3.4] if p['rot']%180 else [x,x],[y,y] if p['rot']%180 else [y,y-3.4],color='#ddd',lw=2.4,solid_capstyle='round')
    elif p['kind']=='TACT':
        ax.add_patch(Circle((x,y),3.3,fc='#1c1c1c',ec='#777',lw=0.5)); ax.add_patch(Circle((x,y),2.6,fc='#2c2c2c',ec='#555',lw=0.3))
    elif p['fp']=='LED_THT:LED_D3.0mm':
        ax.add_patch(Circle((x+1.27,y),1.6,fc='#c0282d' if 'rouge' in p['mpn'] else '#e8961e',ec='#666',lw=0.4))
for t,x,y,s,th in pj['PANEL_TEXT']:
    ax.text(x,y,t,color='white',ha='center',va='center',fontsize=s*ppm*1.45,fontweight='bold',family='DejaVu Sans')
lg=plt.imread('/home/claude/work/logo_white.png'); L=pj['LOGO']; ax.imshow(lg,extent=(L[0],L[0]+L[2],L[1]+L[3],L[1]),zorder=3,interpolation='bilinear')
for x1,y1,x2,y2 in pj['DIV']: ax.plot([x1,x2],[y1,y2],color='#9a9a9a',lw=0.3*ppm*0.6)
for x1,y1,x2,y2,w in pj['TICKS']: ax.plot([x1,x2],[y1,y2],color='white',lw=0.6)
fig.savefig(OUT+'apercu-facade-'+M.SHORT+'.png',facecolor=fig.get_facecolor()); plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(7.2,9.6),dpi=170)
for axx,side in zip(axs,['B','F']):
    axx.set_aspect('equal'); axx.set_xlim(OX-2,OX+PANEL_W+2); axx.set_ylim(OY+PANEL_H+2,OY-2); axx.axis('off')
    axx.add_patch(Rectangle((OX,OY),PANEL_W,PANEL_H,fc='none',ec='#bbb',ls='--',lw=0.6))
    axx.add_patch(Rectangle((OX+1.5,OY+11),PANEL_W-3,106.5,fc='#1d5e3a',ec='k'))
    axx.set_title('Dos (CMS)' if side=='B' else 'Face avant (jacks, pots)',fontsize=9)
    for p in P:
        d=pl[p['ref']]
        if d['side']!=side and FP[d['fp']]['attr']=='smd': continue
        bb=fp_bbox(d['fp'],d['X'],d['Y'],d['rot'],d['side'],0)
        if d['side']==side:
            axx.add_patch(Rectangle((bb[0],bb[1]),bb[2]-bb[0],bb[3]-bb[1],fc='#e8e2c8' if FP[d['fp']]['attr']=='smd' else '#cfcfcf',ec='#333',lw=0.4,alpha=0.9))
            axx.text((bb[0]+bb[2])/2,(bb[1]+bb[3])/2,p['ref'],fontsize=3.6 if FP[d['fp']]['attr']=='smd' else 6,ha='center',va='center')
        for (n,x,y,w,h,kind) in pad_abs(d['fp'],d['X'],d['Y'],d['rot'],d['side']):
            if kind=='smd' and d['side']!=side: continue
            axx.add_patch(Rectangle((x-w/2,y-h/2),w,h,fc='#d4a43a',ec='none'))
fig.tight_layout(); fig.savefig(OUT+'apercu-pcb-'+M.SHORT+'.png'); plt.close(fig)
print('done')
