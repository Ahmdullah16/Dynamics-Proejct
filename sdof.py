"""Linear SDOF free vibration in SI units, with arbitrary initial conditions."""
from dataclasses import dataclass, replace
import numpy as np
import pandas as pd
from scipy.optimize import brentq


@dataclass(frozen=True)
class System:
    mass: float = 1000.0
    stiffness: float = 100000.0
    damping: float = 1000.0
    v0: float = 0.1
    x0: float = 0.0

    def __post_init__(self):
        if not all(np.isfinite(v) for v in (self.mass,self.stiffness,self.damping,self.v0,self.x0)):
            raise ValueError('All inputs must be finite.')
        if self.mass <= 0 or self.stiffness <= 0 or self.damping < 0:
            raise ValueError('Require mass and stiffness > 0; damping >= 0.')

    @property
    def wn(self): return np.sqrt(self.stiffness/self.mass)

    @property
    def zeta(self): return self.damping/(2*np.sqrt(self.mass*self.stiffness))


def response(system, time):
    """Analytical displacement and velocity, stable close to critical damping."""
    t=np.asarray(time,dtype=float)
    if np.any(~np.isfinite(t)) or np.any(t<0):
        raise ValueError('Time must be finite and nonnegative.')
    w,z,x0,v0=system.wn,system.zeta,system.x0,system.v0
    a=system.damping/(2*system.mass)
    if z < 1:
        b=w*np.sqrt((1-z)*(1+z))
        sin_over_b=t*np.sinc(b*t/np.pi)
        e=np.exp(-a*t)
        x=e*(x0*np.cos(b*t)+(v0+a*x0)*sin_over_b)
        v=e*(v0*np.cos(b*t)-(a*v0+w*w*x0)*sin_over_b)
    elif z == 1:
        B=v0+w*x0
        x=(x0+B*t)*np.exp(-w*t)
        v=(v0-w*B*t)*np.exp(-w*t)
    else:
        q=np.sqrt((z-1)*(z+1))
        rs,rf=-w/(z+q),-w*(z+q)
        delta=rs-rf
        B=v0-rs*x0
        x=np.exp(rs*t)*(x0+B*(-np.expm1(-delta*t))/delta)
        v=rs*x+B*np.exp(rf*t)
    return x,v


def first_extremum(system):
    """First displacement turning point strictly after t=0; NaN if monotonic."""
    w,z,x0,v0=system.wn,system.zeta,system.x0,system.v0
    if x0==0 and v0==0: return np.nan
    a=system.damping/(2*system.mass)
    if z < 1:
        b=w*np.sqrt((1-z)*(1+z))
        theta=np.arctan2(-v0,-(a*v0+w*w*x0)/b) % np.pi
        if theta <= 1e-14: theta=np.pi
        return theta/b
    if z == 1:
        B=v0+w*x0
        tp=v0/(w*B) if B else np.nan
    else:
        q=np.sqrt((z-1)*(z+1)); rs,rf=-w/(z+q),-w*(z+q)
        cs=(v0-rf*x0)/(rs-rf); cf=(rs*x0-v0)/(rs-rf)
        ratio=-rf*cf/(rs*cs) if cs else -1
        tp=np.log(ratio)/(rs-rf) if ratio>0 else np.nan
    return tp if np.isfinite(tp) and tp>1e-12/w else np.nan


def metrics(system,tolerance=0.02):
    """Global absolute peak includes t=0; settling is the final band crossing.

    first_peak_s means the first future absolute-displacement local maximum
    (a displacement turning point), excluding t=0. Monotonic cases return NaN.
    """
    if not np.isfinite(tolerance) or not 0<tolerance<1:
        raise ValueError('Tolerance must be between zero and one.')
    w,z=system.wn,system.zeta; a=system.damping/(2*system.mass)
    tp=first_extremum(system)
    xp=abs(float(response(system,tp)[0])) if np.isfinite(tp) else 0.0
    peak=max(abs(system.x0),xp)
    band=tolerance*peak
    if peak==0:
        ts=0.0
    elif system.damping==0:
        ts=np.inf
    elif z<1:
        b=w*np.sqrt((1-z)*(1+z))
        if xp>band:
            n=max(0,int(np.ceil(np.log(xp/band)*b/(a*np.pi)))-1)
            left=tp+n*np.pi/b
            # First zero after the last significant extremum.
            phi=np.arctan2((system.v0+a*system.x0)/b,system.x0)
            index=np.floor((b*left-phi-np.pi/2)/np.pi)+1
            right=(phi+np.pi/2+index*np.pi)/b
        elif abs(system.x0)>band:
            left,right=0.0,tp
        else:
            left=right=0.0
        ts=brentq(lambda t: abs(float(response(system,t)[0]))-band,
                  left,right,xtol=1e-11) if right>left else 0.0
    else:
        if np.isfinite(tp) and xp>band:
            left=tp
        elif abs(system.x0)>band:
            left=0.0
        else:
            left=None
        if left is None:
            ts=0.0
        else:
            right=max(left+1/w,2*left)
            for _ in range(200):
                if abs(float(response(system,right)[0]))<=band: break
                right*=2
            else: raise ArithmeticError('Could not bracket settling time.')
            ts=brentq(lambda t: abs(float(response(system,t)[0]))-band,
                      left,right,xtol=1e-11)
    wd=w*np.sqrt((1-z)*(1+z)) if z<1 else np.nan
    return dict(omega_n_rad_s=w,frequency_hz=w/(2*np.pi),period_s=2*np.pi/w,
                damping_ratio=z,critical_damping_N_s_m=2*np.sqrt(system.mass*system.stiffness),
                damped_frequency_rad_s=wd,decay_rate_s_inv=a,first_peak_s=tp,
                peak_displacement_m=peak,settling_band_m=band,settling_s=ts,
                initial_energy_J=0.5*system.mass*system.v0**2+0.5*system.stiffness*system.x0**2,
                estimate_4_over_zeta_wn_s=8*system.mass/system.damping if z else np.inf)


def sweep(baseline=System(),factors=None,tolerance=0.02):
    """Vary m, k or c alone; initial displacement and velocity remain fixed."""
    factors=np.unique(np.r_[np.linspace(0.25,4,151),1.0]) if factors is None else np.asarray(factors)
    if factors.ndim!=1 or len(factors)==0 or np.any(~np.isfinite(factors)) or np.any(factors<=0):
        raise ValueError('Sweep factors must be a nonempty positive finite vector.')
    rows=[]
    for p in ('mass','stiffness','damping'):
        for f in factors:
            s=replace(baseline,**{p:getattr(baseline,p)*f})
            rows.append(dict(parameter=p,factor=f,mass_kg=s.mass,stiffness_N_m=s.stiffness,
                             damping_N_s_m=s.damping,x0_m=s.x0,v0_m_s=s.v0,**metrics(s,tolerance)))
    return pd.DataFrame(rows)


def local_sensitivity(baseline=System(),tolerance=0.02,step=1e-4):
    """Logarithmic elasticity; NaN for zero inputs or undefined/nonpositive outputs."""
    if not 0<step<1: raise ValueError('Sensitivity step must be between zero and one.')
    rows=[]
    for p in ('mass','stiffness','damping'):
        lo=metrics(replace(baseline,**{p:getattr(baseline,p)*(1-step)}),tolerance)
        hi=metrics(replace(baseline,**{p:getattr(baseline,p)*(1+step)}),tolerance)
        row={'parameter':p}
        for key in ('omega_n_rad_s','damping_ratio','first_peak_s','settling_s'):
            valid=getattr(baseline,p)>0 and np.isfinite(lo[key]) and np.isfinite(hi[key]) and min(lo[key],hi[key])>0
            row[key]=(np.log(hi[key])-np.log(lo[key]))/np.log((1+step)/(1-step)) if valid else np.nan
        rows.append(row)
    return pd.DataFrame(rows).set_index('parameter')


def time_history(system,duration=10.0,samples=3000):
    if not np.isfinite(duration) or duration<=0 or not 2<=samples<=50000:
        raise ValueError('Require positive duration and 2 to 50000 samples.')
    t=np.linspace(0,duration,int(samples)); x,v=response(system,t)
    acceleration=-(system.damping*v+system.stiffness*x)/system.mass
    kinetic=0.5*system.mass*v*v; strain=0.5*system.stiffness*x*x
    return pd.DataFrame(dict(time_s=t,displacement_m=x,velocity_m_s=v,acceleration_m_s2=acceleration,
                             kinetic_energy_J=kinetic,strain_energy_J=strain,total_energy_J=kinetic+strain))
