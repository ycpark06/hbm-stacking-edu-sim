/* 원본 education_calc.py:25-31: reference underfill assumptions. */
export const washburnFillTime=(mu,L,gap,{gamma=0.03,theta_deg=40}={})=>3*mu*L**2/(gamma*gap*Math.cos(theta_deg*Math.PI/180));
export const washburnFront=(mu,t,gap,{gamma=0.03,theta_deg=40}={})=>Math.sqrt(gamma*gap*Math.cos(theta_deg*Math.PI/180)*t/(3*mu));
