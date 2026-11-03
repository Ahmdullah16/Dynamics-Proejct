"""Analytical free response and event-based metrics; SI units throughout.
Initial conditions are x(0)=0, v(0)=v0>0 (fixed initial velocity).
"""
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

    def __post_init__(self):
        if not all(np.isfinite(v) for v in (self.mass, self.stiffness, self.damping, self.v0)):
            raise ValueError('All inputs must be finite.')
        if self.mass <= 0 or self.stiffness <= 0 or self.damping < 0 or self.v0 <= 0:
            raise ValueError('Require mass, stiffness and v0 > 0, damping >= 0.')

    @property
    def wn(self):
        return np.sqrt(self.stiffness / self.mass)

    @property
    def zeta(self):
        return self.damping / (2 * np.sqrt(self.mass * self.stiffness))


def response(system, time):
    """Return displacement and velocity at scalar or array time, all regimes."""
    t = np.asarray(time, dtype=float)
    if np.any(~np.isfinite(t)) or np.any(t < 0):
        raise ValueError('Time must be finite and nonnegative.')
    w, z, v = system.wn, system.zeta, system.v0
    a = z * w
    if z < 1:
        b = w * np.sqrt((1-z)*(1+z))
        e = np.exp(-a*t)
        x = v * e * np.sin(b*t)/b
        vel = v * e * (np.cos(b*t)-a*np.sin(b*t)/b)
    elif z == 1:
        x = v*t*np.exp(-w*t)
        vel = v*(1-w*t)*np.exp(-w*t)
    else:
        q = np.sqrt((z-1)*(z+1))
        slow, fast = -w/(z+q), -w*(z+q)
        # expm1 avoids subtracting nearly equal exponentials near critical damping.
        delta = slow-fast
        es = np.exp(slow*t)
        diff = -np.expm1(-delta*t)
        x = v * es * diff / delta
        vel = v * es * (slow*diff + delta*np.exp(-delta*t)) / delta
    return x, vel


def metrics(system, tolerance=0.02):
    """Exact first positive peak and final band crossing (root tolerance 1e-11 s).

    Band is +/- tolerance * this response's global peak; x(0)=0 is not
    misidentified as settling. With zero damping, settling is infinite.
    """
    if not np.isfinite(tolerance) or not 0 < tolerance < 1:
        raise ValueError('Tolerance must be between zero and one.')
    w, z = system.wn, system.zeta
    if z < 1:
        b = w*np.sqrt((1-z)*(1+z))
        tp = np.arctan2(b, z*w)/b
    elif z == 1:
        tp = 1/w
    else:
        q = np.sqrt((z-1)*(z+1))
        slow, fast = -w/(z+q), -w*(z+q)
        tp = np.log(fast/slow)/(slow-fast)
    peak = float(response(system, tp)[0])
    band = tolerance*peak
    if z == 0:
        ts = np.inf
    elif z < 1:
        # All subsequent absolute extrema decay by exp(-a*pi/b).
        # Locate the last extremum outside the band, then solve until its zero.
        a = z*w
        n = max(0, int(np.ceil(np.log(1/tolerance)*b/(a*np.pi)))-1)
        left = tp+n*np.pi/b
        right = (n+1)*np.pi/b
        ts = brentq(lambda t: abs(float(response(system,t)[0]))-band,
                    left, right, xtol=1e-11)
    else:
        left, right = tp, 2*tp
        while float(response(system,right)[0]) > band:
            right *= 2
        ts = brentq(lambda t: float(response(system,t)[0])-band,
                    left, right, xtol=1e-11)
    return dict(omega_n_rad_s=w, frequency_hz=w/(2*np.pi), damping_ratio=z,
                first_peak_s=tp, peak_displacement_m=peak, settling_s=ts,
                estimate_4_over_zeta_wn_s=8*system.mass/system.damping if z else np.inf)


def sweep(baseline=System(), factors=None, tolerance=0.02):
    """One factor at a time; c varies independently, never holds zeta fixed."""
    if factors is None:
        factors = np.unique(np.r_[np.linspace(0.25,4,151), 1.0])
    rows = []
    for parameter in ('mass','stiffness','damping'):
        for factor in factors:
            s = replace(baseline, **{parameter: getattr(baseline,parameter)*factor})
            rows.append(dict(parameter=parameter, factor=factor, mass_kg=s.mass,
                             stiffness_N_m=s.stiffness, damping_N_s_m=s.damping,
                             **metrics(s,tolerance)))
    return pd.DataFrame(rows)


def local_sensitivity(baseline=System(), tolerance=0.02, step=1e-4):
    """Dimensionless centered logarithmic elasticity (p/y) dy/dp."""
    rows=[]
    for p in ('mass','stiffness','damping'):
        low=metrics(replace(baseline, **{p:getattr(baseline,p)*(1-step)}),tolerance)
        high=metrics(replace(baseline, **{p:getattr(baseline,p)*(1+step)}),tolerance)
        rows.append(dict(parameter=p, **{k:(np.log(high[k])-np.log(low[k])) /
                    (np.log(1+step)-np.log(1-step)) for k in
                    ('omega_n_rad_s','damping_ratio','first_peak_s','settling_s')}))
    return pd.DataFrame(rows).set_index('parameter')
