R=$(cd "$(dirname "$0")/../.." && pwd); H=$(dirname "$0")
# runf NAME VOCT TSTOP [SYNC source] : proposed reset fix
#  1. U1D becomes a monostable : + input = RAMP through 10k (CMPP), 330p + 1M from RSTQ to CMPP
#  2. gate driven DC : RSTQ -> diode -> 4k7 (220p across) -> GATE, R15 22k to -12 V keeps the JFET hard off
#  3. JFET drain on HFC (directly across C10) instead of RAMP
#  4. sync diode D3 into CMPP instead of GATE
#  5. sine output amp : R33, R35 470k and R34, R36 560k (10k/12k were loading the 47k collectors)
bash $H/run.sh $1 $2 'RFIX1 RAMP CMPP 10k|RFIX2 RSTQ CMPP 1Meg|CFIX RSTQ CMPP 330p|DFIX RSTQ GX D1N4148|RFIX3 GX GATE 4.7k|CFIX2 GX GATE 220p' $3 >/dev/null 2>&1
sed -i -e 's/^XU1D RAMP REF5 RSTQ/XU1D CMPP REF5 RSTQ/' -e 's/^DD3 SYD GATE D1N4148/DD3 SYD CMPP D1N4148/' -e 's/^CC11 RSTQ GATE 220p/* C11 removed/' -e 's/^JQ2 RAMP GATE INTN/JQ2 HFC GATE INTN/' $1.cir
[ -n "$4" ] && sed -i "s/^RJ3sw .*/VJ3 SYNCJ 0 $4/" $1.cir
sed -i -e "s/^RR33 SC1 SIN_N 10k/RR33 SC1 SIN_N 470k/" -e "s/^RR35 SC2 SIN_P 10k/RR35 SC2 SIN_P 470k/" -e "s/^RR34 SIN_N SINO 12k/RR34 SIN_N SINO 560k/" -e "s/^RR36 SIN_P 0 12k/RR36 SIN_P 0 560k/" $1.cir
timeout 900 ngspice -b $1.cir > $1.log 2>&1; echo "== $1 voct=$2 (fix)"; python3 $H/ana.py $1.txt SAW,TRI,SINE,PULSE,RAMP $1.npy 2>&1 | tail -6
