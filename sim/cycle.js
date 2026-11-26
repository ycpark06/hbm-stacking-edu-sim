/* 원본 drive_calc.py:3-25: gravity, steel density/modulus, root diameter and supports. */
export function ballscrew({m,lead,d,L,eta,a,v,mu,Fext=0,vertical=false,Jm=0,Ca=null,support=3.927,eta2=10}) {
  const g=9.81,rho=7850,E=206e3;
  const Jscrew=Math.PI*rho*(L/1000)*(d/1000)**4/32;
  const alpha=2*Math.PI*a/(lead/1000), Ffr=vertical?0:mu*m*g,Fg=vertical?m*g:0;
  const F=m*a+Ffr+Fg+Fext,T_load=F*lead/1000/(2*Math.PI*eta),T_acc=(Jscrew+Jm)*alpha;
  const F_hold=Ffr+Fg+Fext,dr=d*0.83;
  return {F_peak:F,T_peak:T_load+T_acc,T_hold:F_hold*lead/1000/(2*Math.PI*eta),rpm_max:v/lead*60,
    n_crit:support**2*60/(2*Math.PI*(L/1000)**2)*Math.sqrt(E*1e6*Math.PI*(dr/1000)**4/64/(rho*Math.PI*(dr/1000)**2/4)),P_buckle:eta2*dr**4/L**2*1e4};
}
/* 원본 drive_calc.py:45-50. */
export function leafFlexure(k,F,E=200e3,b=20,L=25) {
  const t=(k*L**3/(4*E*b))**(1/3),defl=F/k;return {t,defl,stress:3*E*t*defl/L**2};
}
