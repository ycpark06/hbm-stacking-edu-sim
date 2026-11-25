import numpy as np
exec(open('control_sim.py').read().split('cases={}')[0])
for Ts in (1e-3,10e-3):
    for ap in (0.02,0.2,0.5):
        k=50.0; ke=1/(1/k+1/2000)
        r=force_sim(k,5.0,Ts=Ts,approach=ap,Ki=(2*np.pi*20)*(2*np.pi*2)/ke,t_end=4.0)
        m=(r["t"]>r["t_contact"])&(r["t"]<r["t_contact"]+0.3)
        print(Ts,ap,"peak in first 0.3 s minus setpoint:",round(float((r["F"][m]-r["sp"][m]).max()),3))
