/* 원본 process_physics.py:50-52,60; education_calc.py:10-12,22. */
export function timoshenkoCurvature(h1,E1,a1,h2,E2,a2,dT) {
  const m=h1/h2,n=E1/E2,h=h1+h2;
  return 6*(a2-a1)*dT*(1+m)**2/(h*(3*(1+m)**2+(1+m*n)*(m*m+1/(m*n))));
}
export const warpSagitta = (k,L) => k*L**2/8;

/* Free 1D laminate, bottom→top; eps(z)=eps0+kappa*z with z from midplane.
 * nu is optional: when supplied use equal-biaxial Q=E/(1-nu), otherwise Q=E
 * (strip convention matching original Timoshenko). Thermal strain=alpha*dT.
 * [A B; B D][eps0 kappa]=[NT MT], zero external force and moment. */
export function laminateCurvature(layers) {
  if(!layers?.length) throw new RangeError('nonempty laminate');
  const height=layers.reduce((s,l)=>s+l.t_m,0);
  let z=-height/2,A=0,B=0,D=0,NT=0,MT=0;
  for(const l of layers) {
    const Q=l.E_Pa/(1-(l.nu??0)),t=l.t_m,mid=z+t/2,strain=l.alpha*l.dT_K;
    if(!(t>0)||!(Q>0)||!Number.isFinite(strain)||l.nu>=1) throw new RangeError('laminate properties');
    const a=Q*t,b=a*mid,d=a*(mid*mid+t*t/12);
    A+=a;B+=b;D+=d;NT+=a*strain;MT+=b*strain;z+=t;
  }
  const det=A*D-B*B;
  if(!(det>0)) throw new RangeError('singular laminate');
  return {eps0:(D*NT-B*MT)/det,kappa:(A*MT-B*NT)/det};
}

/* Each step supplies the CURRENT complete mechanical laminate. stress_free_C
 * is fixed at attachment (TC-NCF: per-layer bonding temperature); MR-MUF:
 * Si/bump references reset at reflow, MUF uses molding/cure temperature.
 * No cure kinetics or stress relaxation is asserted by this elastic C1 model. */
export function stackWarpHistory(steps) {
  return steps.map(step=>{
    const layers=step.layers.map(l=>({...l,dT_K:l.dT_K??(l.T_C-l.stress_free_C)}));
    const {eps0,kappa}=laminateCurvature(layers),w_um=warpSagitta(kappa,step.die_size_m)*1e6;
    return {t_s:step.t_s,phase:step.phase,layer_count:step.layer_count??layers.length,eps0,kappa,w_um};
  });
}
export function judgeWarpage(w_um,gap_um,params) {
  if(!Number.isFinite(w_um)||!(gap_um>0)) throw new RangeError('warpage/gap');
  const j=params.judgement,a=Math.abs(w_um);
  return a>j.warpage_fail_um.value?'불량':a>j.warpage_caution_ratio.value*gap_um?'주의':'양호';
}

/* Adapter from C1 thermal volumes to strip layers. One gap UNDER each die,
 * including the lowest die's attachment layer; no elastic substrate is added.
 * The unfilled gap is an effective Cu/SnAg series pillar network. */
export function thermalWarpSteps(thermal,model) {
  const p=model.params,g=p.geometry,m=p.materials,mode=model.layers[0].mode;
  const fraction=Math.PI/4*(g.bump_diameter.value/g.bump_pitch.value)**2;
  const cu=g.cu_pillar_height.value/(g.cu_pillar_height.value+g.solder_cap_height.value);
  const bumpE=fraction/(cu/m.cu_E.value+(1-cu)/m.snag_E.value);
  const bumpAlpha=cu*m.cu_cte.value+(1-cu)*m.snag_cte.value;
  let bonded=0,refs=[],gapRefs=[],molded=false;const steps=[];
  function frame(row,temperatures) {
    if(!bonded) return;
    const layers=[];
    for(let i=0;i<bonded;i++) {
      const fill=mode==='TC-NCF'?p.ncf:molded?p.muf:null;
      layers.push({t_m:g.interlayer_gap.value*1e-6,E_Pa:(fill?(fill.modulus_25C??fill.modulus).value:bumpE)*1e9,
        alpha:(fill?fill.cte1.value:bumpAlpha)*1e-6,T_C:temperatures[i],stress_free_C:gapRefs[i]});
      layers.push({t_m:(model.layers[i].thickness_um??g.die_thickness.value)*1e-6,E_Pa:m.si_E.value*1e9,
        alpha:m.si_cte.value*1e-6,T_C:temperatures[i],stress_free_C:refs[i]});
    }
    steps.push({t_s:row.t_s,phase:row.phase,layer_count:bonded,die_size_m:g.die_size.value/1000,layers});
  }
  for(const row of thermal.history) {
    if(row.event==='bond'||row.event==='tack') {
      bonded=row.T.length;refs[bonded-1]=row.T.at(-1);gapRefs[bonded-1]=row.T.at(-1);
    }
    if(row.event==='reflow') {refs=row.T.slice();gapRefs=row.T.slice();}
    frame(row,row.T);
  }
  if(mode==='MR-MUF') {
    const end=thermal.history.at(-1),Tc=p.muf.cure_temp.value;
    // Equilibrium endpoints after mold cure; no invented cure ramp/time profile.
    frame({...end,phase:'mold-preheat'},Array(bonded).fill(Tc));
    molded=true;gapRefs=Array(bonded).fill(Tc);
    frame({...end,phase:'mold-cure'},Array(bonded).fill(Tc));
    frame({...end,t_s:end.t_s+p.muf.cure_time.value,phase:'mold-cooled'},Array(bonded).fill(p.thermal_stack.ambient_temp.value));
  }
  return steps;
}
