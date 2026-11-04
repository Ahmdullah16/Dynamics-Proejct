"""On-site concepts, derivations, units and numerical worked example."""
import streamlit as st
import numpy as np


def render_theory(system,result,tolerance):
    st.header('Concepts & mathematical formulation')
    st.markdown('A single-degree-of-freedom (SDOF) model describes motion using one coordinate: displacement from static equilibrium. Mass stores kinetic energy, the spring stores elastic energy, and the viscous damper dissipates energy. Change an input in the sidebar to update the numerical example below.')
    st.image('''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="175" viewBox="0 0 800 175"><rect width="800" height="175" fill="#f1f6fa"/><path d="M85 20V150M85 50H125L138 35L157 65L176 35L195 65L214 35L233 65L246 50H310M85 120H170M170 100V140M170 100H230V140H170M200 120H310" fill="none" stroke="#147d92" stroke-width="4"/><rect x="310" y="30" width="130" height="120" rx="8" fill="#dcebf1" stroke="#147d92" stroke-width="3"/><text x="360" y="100" font-size="30">m</text><text x="175" y="25" font-size="22">k</text><text x="180" y="165" font-size="22">c</text><path d="M470 85H650M638 75L650 85L638 95" stroke="#dc6b31" fill="none" stroke-width="4"/><text x="510" y="65" font-size="23">x(t)</text><text x="475" y="140" font-size="18">Free response: external force = 0</text></svg>''',width='stretch')
    with st.expander('1 · Forces, equation of motion and assumptions',expanded=True):
        st.markdown('For positive displacement to the right, the spring force opposes displacement and the damper force opposes velocity. Apply Newton’s second law:')
        st.latex(r'F_k=-kx,\quad F_c=-c\dot{x},\quad m\ddot{x}=F_k+F_c')
        st.latex(r'\boxed{m\ddot{x}+c\dot{x}+kx=0},\qquad x(0)=x_0,\quad\dot{x}(0)=v_0')
        st.markdown('Displacement is measured from static equilibrium, so the constant weight is already balanced. The model assumes a fixed support, constant positive mass and stiffness, linear elasticity, nonnegative viscous damping, and no external excitation after release. Initial conditions set the motion; they are not a continuing force.')
        st.table({'Symbol':['m','k','c','x, x₀','ẋ, v₀','ẍ'],'Meaning':['Mass','Stiffness','Viscous damping coefficient','Displacement / initial displacement','Velocity / initial velocity','Acceleration'],'SI unit':['kg','N/m','N·s/m','m','m/s','m/s²']})
    with st.expander('2 · Natural frequency, damping ratio and characteristic roots',expanded=True):
        st.markdown('Divide the governing equation by mass and compare coefficients with the standard form:')
        st.latex(r'\ddot{x}+2\zeta\omega_n\dot{x}+\omega_n^2x=0')
        st.latex(r'\omega_n=\sqrt{\frac{k}{m}},\quad f_n=\frac{\omega_n}{2\pi},\quad T_n=\frac{2\pi}{\omega_n}')
        st.latex(r'c_{\mathrm{cr}}=2\sqrt{mk},\quad\zeta=\frac{c}{c_{\mathrm{cr}}},\quad\alpha=\zeta\omega_n=\frac{c}{2m}')
        st.markdown('Try an exponential solution x = C exp(rt). Substitution gives a quadratic equation, whose roots determine the damping regime:')
        st.latex(r'mr^2+cr+k=0\quad\Longrightarrow\quad r_{1,2}=-\alpha\pm\sqrt{\alpha^2-\omega_n^2}')
        st.table({'Regime':['Undamped','Underdamped','Critical','Overdamped'],'Condition':['c = 0','0 < ζ < 1','ζ = 1','ζ > 1'],'Behavior':['Persistent oscillation','Oscillation with decaying envelope','Repeated real root; nonoscillatory response','Two real roots; nonoscillatory response']})
    with st.expander('3 · Exact solution for every damping regime',expanded=True):
        st.markdown('**Underdamped and undamped:** let A = x₀ and enforce the initial velocity to determine B:')
        st.latex(r'\omega_d=\omega_n\sqrt{1-\zeta^2},\quad A=x_0,\quad B=\frac{v_0+\alpha x_0}{\omega_d}')
        st.latex(r'\boxed{x(t)=e^{-\alpha t}\left[A\cos(\omega_dt)+B\sin(\omega_dt)\right]}')
        st.latex(r'\dot{x}(t)=e^{-\alpha t}\left[v_0\cos(\omega_dt)-\frac{\alpha v_0+\omega_n^2x_0}{\omega_d}\sin(\omega_dt)\right]')
        st.markdown('Setting c = 0 gives α = 0 and a constant oscillation amplitude. The damped frequency is defined only in the oscillatory regime; the undamped natural frequency remains defined for all positive m and k.')
        st.markdown('**Critical damping:** the roots coincide at −ωₙ. Enforcing both initial conditions gives:')
        st.latex(r'\boxed{x(t)=\left[x_0+(v_0+\omega_nx_0)t\right]e^{-\omega_nt}}')
        st.markdown('**Overdamping:** use the distinct real roots and solve the two initial-condition equations:')
        st.latex(r'r_s=-\omega_n\left(\zeta-\sqrt{\zeta^2-1}\right),\quad r_f=-\omega_n\left(\zeta+\sqrt{\zeta^2-1}\right)')
        st.latex(r'C_s=\frac{v_0-r_fx_0}{r_s-r_f},\quad C_f=\frac{r_sx_0-v_0}{r_s-r_f},\quad \boxed{x(t)=C_se^{r_st}+C_fe^{r_ft}}')
        st.markdown('The implementation evaluates the slow root as −ωₙ/(ζ + √(ζ² − 1)) and uses expm1 for close exponentials to reduce numerical cancellation.')
        st.latex(r'\boxed{\ddot{x}(t)=-\frac{c}{m}\dot{x}(t)-\frac{k}{m}x(t)}')
    with st.expander('4 · Peak time and exact settling time',expanded=True):
        st.markdown('**First future peak:** the first displacement turning point at t > 0, obtained from ẋ(t) = 0. A negative displacement minimum is a peak of absolute displacement. The initial displacement at t = 0 is included in the global amplitude but excluded from the future peak time. A monotonic response has no future peak and is marked N/A.')
        st.latex(r'v_0\cos(\omega_dt)-\frac{\alpha v_0+\omega_n^2x_0}{\omega_d}\sin(\omega_dt)=0')
        st.markdown('For the original initial-velocity release x₀ = 0, v₀ > 0:')
        st.latex(r't_p=\frac{\operatorname{atan2}(\omega_d,\alpha)}{\omega_d}\quad(\zeta<1),\qquad t_p=\frac1{\omega_n}\quad(\zeta=1)')
        st.markdown('**Settling definition:** let P be the largest absolute displacement over t ≥ 0, and ε the selected tolerance. The same fraction is used in every case, but each case has its own band εP:')
        st.latex(r'P=\max_{t\geq0}|x(t)|,\qquad t_s=\inf\{t\geq0:\ |x(\tau)|\leq\varepsilon P\ \text{for every }\tau\geq t\}')
        st.markdown('For an underdamped response, successive absolute extrema are separated by π/ωd and decay geometrically. The solver locates the last extremum outside the band, then solves the subsequent band crossing using Brent’s method. For critical and overdamped motion it solves the final monotonic tail. Metrics therefore do not depend on the displayed time window or plot sample count.')
        st.latex(r'|x(t_p+n\pi/\omega_d)|=|x(t_p)|\exp\left(-\frac{n\pi\alpha}{\omega_d}\right)')
        st.markdown('Nonzero undamped motion never settles. If both initial conditions are zero, the response stays zero: global peak and settling time are zero, while first future peak is undefined. The band is relative to each peak, not a universal displacement safety limit.')
        st.markdown('**Engineering estimate:** for a lightly damped envelope, ln(1/0.02) ≈ 4. This familiar estimate is not the exact final crossing:')
        st.latex(r't_s\approx\frac{4}{\zeta\omega_n}=\frac{8m}{c}\qquad\text{(2\% envelope estimate)}')
    with st.expander('5 · Energy, phase plane and physical checks'):
        st.latex(r'E(t)=\frac12m\dot{x}^2+\frac12kx^2')
        st.latex(r'\frac{dE}{dt}=\dot{x}(m\ddot{x}+kx)=-c\dot{x}^2\leq0')
        st.markdown('Kinetic and spring energies exchange during vibration. Total energy is conserved when c = 0 and cannot increase when c > 0. The phase plane plots velocity against displacement: closed orbits for undamped motion, and paths toward equilibrium for damped motion. Holding x₀ and v₀ fixed does not hold initial energy fixed while m or k varies.')
    with st.expander('6 · Sensitivity definitions and engineering interpretation',expanded=True):
        st.markdown('Each sweep changes one property p by a factor λ while keeping the other properties and both initial conditions fixed. Damping ratio is recomputed; it is not held fixed during mass or stiffness variations.')
        st.latex(r'p=\lambda p_0,\qquad S_p^y=\frac{p}{y}\frac{\partial y}{\partial p}=\frac{\partial\ln y}{\partial\ln p}')
        st.latex(r'S_p^y\approx\frac{\ln y(p(1+h))-\ln y(p(1-h))}{\ln(1+h)-\ln(1-h)},\qquad h=10^{-4}')
        st.latex(r'S_m^{\omega_n}=-\frac12,\quad S_k^{\omega_n}=+\frac12,\quad S_c^{\omega_n}=0')
        st.latex(r'S_m^\zeta=-\frac12,\quad S_k^\zeta=-\frac12,\quad S_c^\zeta=1')
        st.markdown('Thus mass and stiffness have equal relative influence on natural frequency; c has the greatest relative influence on damping ratio. First peak is mainly controlled by √(m/k) near light damping. Broad settling trends follow c/(2m), while strong overdamping introduces a slow time scale near c/k. Exact peak and settling sensitivities depend on initial conditions and damping regime.')
        st.latex(r'I_p^y=\frac{\max_\lambda y-\min_\lambda y}{|y_0|}')
        st.markdown('The range-based influence table uses the chosen factor interval plus the baseline. It is not a universal ranking. Exact settling can jump when its last significant oscillation changes; a local derivative can differ substantially from the broad trend. Zero, infinite, or undefined responses cannot be logarithmically normalized and are marked N/A. Multiplying zero c by a factor keeps it zero; choose a positive c to study damping sensitivity.')
    with st.expander('7 · Current numerical substitution',expanded=True):
        st.latex(rf'\omega_n=\sqrt{{\frac{{{system.stiffness:g}}}{{{system.mass:g}}}}}={result["omega_n_rad_s"]:.6g}\ \mathrm{{rad/s}}')
        st.latex(rf'\zeta=\frac{{{system.damping:g}}}{{2\sqrt{{{system.mass:g}\times{system.stiffness:g}}}}}={result["damping_ratio"]:.6g}')
        st.latex(rf'x(0)={system.x0:g}\ \mathrm{{m}},\quad\dot x(0)={system.v0:g}\ \mathrm{{m/s}},\quad\varepsilon={tolerance:g}')
        st.markdown(f'Current peak magnitude: **{result["peak_displacement_m"]*1000:.6g} mm**. Settling band: **±{result["settling_band_m"]*1000:.6g} mm**. See the Results tab for the computed future peak and settling events.')
    st.caption('References: Chopra, Dynamics of Structures, 5th edition, free vibration of SDOF systems; SciPy official brentq and expm documentation. This ideal linear model does not represent yielding, higher modes, soil interaction or a calibrated structural safety assessment.')
    st.markdown('[SciPy root solver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html) · [Independent matrix-exponential verification](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html)')
