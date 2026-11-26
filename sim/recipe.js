export {forceLimit} from './ncf.js';
/* 원본 control_sim.py:65: reference profile. */
export const tcncfProfile=t=>t<40?150:t<70?Math.min(300,150+20*(t-40)):300;
