/* 원본 process_physics.py:50-52,60; education_calc.py:10-12,22. */
export function timoshenkoCurvature(h1,E1,a1,h2,E2,a2,dT) {
  const m=h1/h2,n=E1/E2,h=h1+h2;
  return 6*(a2-a1)*dT*(1+m)**2/(h*(3*(1+m)**2+(1+m*n)*(m*m+1/(m*n))));
}
export const warpSagitta = (k,L) => k*L**2/8;
