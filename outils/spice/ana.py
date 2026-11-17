import numpy as np, sys
d=np.loadtxt(sys.argv[1]); t=d[:,0]; names=sys.argv[2].split(',')
cols={n:d[:,2*i+1] for i,n in enumerate(names)}
m=t>t[-1]*0.4; t=t[m]; cols={k:v[m] for k,v in cols.items()}
# uniform resample
sr=192000; tu=np.arange(t[0],t[-1],1/sr); U={k:np.interp(tu,t,v) for k,v in cols.items()}
ref=U[names[0]]-U[names[0]].mean(); z=np.where((ref[:-1]<0)&(ref[1:]>=0))[0]
f=(len(z)-1)/((z[-1]-z[0])/sr) if len(z)>2 else 0
print('freq %.2f Hz'%f)
for k,v in U.items():
    seg=v[z[0]:z[-1]]; n=len(seg); S=np.abs(np.fft.rfft(seg*np.hanning(n))); fr=np.fft.rfftfreq(n,1/sr)
    h=[S[np.argmin(abs(fr-f*q))-2:np.argmin(abs(fr-f*q))+3].max() for q in range(1,13)]
    print('%-6s min %6.2f max %6.2f  harm dB:'%(k,seg.min(),seg.max()),' '.join('%5.1f'%(20*np.log10(x/h[0]+1e-12)) for x in h[1:10]))
np.save(sys.argv[3] if len(sys.argv)>3 else 'last.npy', np.vstack([tu]+[U[k] for k in names]))
