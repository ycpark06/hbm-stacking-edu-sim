// xoshiro128** (Blackman/Vigna), SplitMix32 seed expansion; no numpy stream equivalence.
export function makeRng(seed) {
  let x = seed >>> 0;
  const s = Array.from({length: 4}, () => {
    x = (x + 0x9e3779b9) >>> 0;
    let z = x; z = Math.imul(z ^ z >>> 16, 0x21f0aaad);
    z = Math.imul(z ^ z >>> 15, 0x735a2d97); return (z ^ z >>> 15) >>> 0;
  });
  const rot = (v, k) => (v << k | v >>> (32-k)) >>> 0;
  function next() {
    const r = Math.imul(rot(Math.imul(s[1], 5), 7), 9) >>> 0, t = s[1] << 9;
    s[2] ^= s[0]; s[3] ^= s[1]; s[1] ^= s[2]; s[0] ^= s[3]; s[2] ^= t; s[3] = rot(s[3], 11);
    return r / 2**32;
  }
  let spare;
  return {
    uniform(a=0,b=1) { return a+(b-a)*next(); },
    normal(mu=0,sigma=1) {
      if (spare !== undefined) { const z=spare; spare=undefined; return mu+sigma*z; }
      const r=Math.sqrt(-2*Math.log(1-next())), th=2*Math.PI*next();
      spare=r*Math.sin(th); return mu+sigma*r*Math.cos(th);
    }
  };
}
