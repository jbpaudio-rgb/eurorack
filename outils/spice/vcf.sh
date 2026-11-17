R=$(cd "$(dirname "$0")/../.." && pwd); H=$(dirname "$0")
# vcf NAME FREQ EMPH MODE
python3 - "$@" <<'EOF'
import json,sys
n,f,e,m=sys.argv[1:5]
c={"pots":{"RV1":float(f),"RV2":float(e),"RV6":float(m),"RV3":0.0,"RV4":0.0,"RV5":0.0},"drive":{"J5":"DC 0 AC 0.1"},
   "tran":".op","extra":".control\nset filetype=ascii\nac dec 40 5 40k\nwrdata %s.txt vdb(OUTJ)\n.endc"%n}
json.dump(c,open(n+'.json','w'))
EOF
python3 $H/kicad2spice.py $R/VCF/octavio-vcf.kicad_pcb $R/VCF/octavio-vcf.kicad_sch $1.cir $1.json >/dev/null
sed -i -e "s/^\.op$//" -e "s/PWL(0 0 1m -12)/DC -12/" -e "s/PWL(0 0 1m 12)/DC 12/" $1.cir
timeout 600 ngspice -b $1.cir > $1.log 2>&1
python3 - $1 <<'EOF'
import numpy as np,sys
d=np.loadtxt(sys.argv[1]+'.txt'); f=d[:,0]; g=d[:,1]+20  # input 0.1 V -> +20 dB = gain
pk=np.argmax(g); ref=np.median(g[(f>f[0])&(f<f[0]*3)])
lp=g.max()-3; idx=np.where(g>=g.max()-3)[0]
fc=f[idx[-1]] if idx[-1]<len(f)-1 else float('nan')
print('%s  gain@low %.1f dB  peak %.1f dB at %.0f Hz  -3dB(upper) %.0f Hz  gain@20k %.1f dB'%(sys.argv[1],ref,g[pk],f[pk],fc,np.interp(20000,f,g)))
EOF
