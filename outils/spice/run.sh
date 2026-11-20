export VCOJSON=$(dirname "$0")/vco.json; R=$(cd "$(dirname "$0")/../.." && pwd); H=$(dirname "$0")
# run NAME VOCT "EXTRA|LINES" TSTOP_seconds
python3 - "$@" <<'EOF'
import json,sys
n,v,x,ts=sys.argv[1:5]; ts=float(ts)
c=json.load(open(sys.argv[0] and __import__('os').environ.get('VCOJSON','vco.json'))); c['drive']['J2']='DC '+v
c['tran']='.tran %g %g 0 %g uic'%(ts/120000,ts,ts/120000)
c['extra']=(x.replace('|','\n')+'\n' if x else '')+'.control\nset filetype=ascii\nrun\nwrdata %s.txt v(SAWJ) v(TRIJ) v(SINJ) v(PULJ) v(RAMP)\n.endc'%n
json.dump(c,open(n+'.json','w'))
EOF
python3 $H/kicad2spice.py $R/VCO/octavio-vco.kicad_pcb $R/VCO/octavio-vco.kicad_sch $1.cir $1.json >/dev/null && timeout 900 ngspice -b $1.cir > $1.log 2>&1; echo "== $1"; python3 $H/ana.py $1.txt SAW,TRI,SINE,PULSE,RAMP $1.npy 2>&1 | tail -6
