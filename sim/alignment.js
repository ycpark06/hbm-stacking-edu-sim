/* 원본 vision.py:24-26. */
export function subpixelPeak(a,b,c,method='gauss') {
  if(method==='gauss' && Math.min(a,b,c)>0) [a,b,c]=[a,b,c].map(Math.log);
  const d=a-2*b+c;return d===0?0:0.5*(a-c)/d;
}
/* 원본 vision.py:94-96; error_budget.py:18,23. */
export const angleSigmaDeg=(s,L=4000,n=4)=>(n===2?Math.sqrt(2)*Math.sqrt(2):Math.sqrt(2))*s/L*180/Math.PI;
export const sigmaOf=(dist,p)=>dist==='n'?p:p/Math.sqrt(3);
export const rssSigma=terms=>Math.sqrt(terms.reduce((s,[d,p])=>s+sigmaOf(d,p)**2,0));
/* 원본 vision.py:67-73: Householder QR least squares, avoiding normal equations. */
export function affineFit(P,S) {
  if(P.length<3 || P.length!==S.length) throw new RangeError('affine point count');
  const M=P.map(([x,y])=>[x,y,1]),Y=S.map(r=>[...r]);
  for(let k=0;k<3;k++) {
    const norm=Math.hypot(...M.slice(k).map(r=>r[k]));
    if(norm===0) throw new RangeError('rank deficient affine points');
    const v=M.slice(k).map(r=>r[k]);v[0]+=Math.sign(v[0]||1)*norm;
    const vv=v.reduce((s,x)=>s+x*x,0);
    for(const [A,cols] of [[M,3],[Y,2]]) for(let j=(A===M?k:0);j<cols;j++) {
      const f=2*v.reduce((s,x,i)=>s+x*A[i+k][j],0)/vv;
      v.forEach((x,i)=>{A[i+k][j]-=f*x;});
    }
  }
  const coef=Array.from({length:3},()=>[0,0]);
  for(let k=2;k>=0;k--) for(let j=0;j<2;j++) coef[k][j]=(Y[k][j]-coef.slice(k+1).reduce((s,r,i)=>s+M[k][k+1+i]*r[j],0))/M[k][k];
  const A=[[coef[0][0],coef[1][0]],[coef[0][1],coef[1][1]]];
  return {A,b:coef[2],rot_deg:Math.atan2(A[1][0],A[0][0])*180/Math.PI,scale_um_px:Math.hypot(A[0][0],A[1][0])};
}
/* 원본 vision.py:78-86: original MC assumptions, no image processing. */
export function alignOnce(rng,sig_ch_um,{init_um=30,init_deg=0.3,tol_um=0.15,tol_deg=0.002,max_iter=3,map_err=5e-4,stage_sigma_um=0.02,theta_meas_deg=0.0005,theta_cmd_deg=0.0003}={}) {
  let d=[rng.uniform(-init_um,init_um),rng.uniform(-init_um,init_um)],theta=rng.uniform(-init_deg,init_deg)*Math.PI/180;
  for(let it=1;it<=max_iter;it++) {
    const meas=d.map(v=>v+rng.normal(0,Math.sqrt(2)*sig_ch_um)),mt=theta+rng.normal(0,theta_meas_deg*Math.PI/180);
    if(meas.every(v=>Math.abs(v)<=tol_um)&&Math.abs(mt*180/Math.PI)<=tol_deg) return {d_um:d,theta_rad:theta,iters:it-1};
    const map=1+rng.normal(0,map_err);
    d=d.map((v,i)=>v-meas[i]*map+rng.normal(0,stage_sigma_um));
    theta=theta-mt+rng.normal(0,theta_cmd_deg)*Math.PI/180;
  }
  // Original consumes one final two-channel measurement even though it isn't returned.
  d.forEach(()=>rng.normal(0,Math.sqrt(2)*sig_ch_um));
  return {d_um:d,theta_rad:theta,iters:max_iter};
}

/** N placements above a fixed substrate (bottom datum), per Cartesian axis.
 * Previous: e_i=e_(i-1)+epsilon_i; substrate: e_i=epsilon_i.
 * Consequently substrate-referenced adjacent errors have sigma sqrt(2)*sigma
 * and negative neighbour covariance; they are not independent layer increments.
 * TC-NCF has no self-alignment (midterm chapter 4).
 */
export function stackOffsetExpected({N,sigma_layer_um,reference='previous',params}) {
  const sigma=sigma_layer_um??params?.alignment.sigma_layer_um.value;
  if(!Number.isInteger(N)||N<1||!(sigma>=0&&Number.isFinite(sigma))||!['previous','substrate'].includes(reference))
    throw new RangeError('stack offset count/sigma/reference');
  const cumulative_sigma_um=sigma*(reference==='previous'?Math.sqrt(N):1);
  return {N,reference,sigma_layer_um:sigma,mean_um:0,cumulative_sigma_um,cumulative_3sigma_um:3*cumulative_sigma_um,
    adjacent_sigma_um:Array.from({length:N},(_,i)=>sigma*(reference==='substrate'&&i>0?Math.SQRT2:1)),
    top_to_first_die_sigma_um:N===1?0:sigma*Math.sqrt(reference==='previous'?N-1:2),self_alignment:false};
}
export function stackOffset(options) {
  const expected=stackOffsetExpected(options),{N,reference,sigma_layer_um:sigma}=expected,{rng}=options;
  if(!rng?.normal)throw new TypeError('seeded rng.normal required');
  const positions_um=[],layer_errors_um=[];let previous=[0,0];
  for(let i=0;i<N;i++) {
    const noise=[rng.normal(0,sigma),rng.normal(0,sigma)],position=noise.map((v,j)=>v+(reference==='previous'?previous[j]:0));
    positions_um.push(position);layer_errors_um.push(position.map((v,j)=>v-previous[j]));previous=position;
  }
  return {...expected,positions_um,layer_errors_um,cumulative_um:positions_um.at(-1),
    top_to_first_die_um:positions_um.at(-1).map((v,j)=>v-positions_um[0][j])};
}
export function stackOffsetMonteCarlo(options) {
  const samples=options.samples??options.params?.alignment.mc_samples.value;
  if(!Number.isInteger(samples)||samples<2)throw new RangeError('MC sample count');
  const expected=stackOffsetExpected(options),mean=[0,0],M2=[0,0];
  for(let n=1;n<=samples;n++) {
    const x=stackOffset(options).cumulative_um;
    for(let j=0;j<2;j++){const d=x[j]-mean[j];mean[j]+=d/n;M2[j]+=d*(x[j]-mean[j]);}
  }
  return {...expected,samples,mc_mean_um:mean,mc_sigma_um:M2.map(v=>Math.sqrt(v/(samples-1))),
    sigma_relative_standard_error:1/Math.sqrt(2*(samples-1))};
}
