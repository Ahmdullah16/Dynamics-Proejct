# Sensitivity of free-vibration response to system properties

## Objective and scope
Quantify how independently changing mass m, stiffness k and viscous damping coefficient c changes an ideal linear SDOF free response. Deliverables are a reusable Python solver, reproducible sensitivity plots and this engineering interpretation. This is an illustrative dynamics experiment; the chosen system is not calibrated to a particular structure.

## Model and baseline
Newton's second law gives m x'' = -c x' -k x, hence **m x'' + c x' + k x = 0**. Displacement is measured from static equilibrium, so gravity is already balanced. The model has constant properties, linear elasticity, viscous damping, a fixed support and no force after release.

| Quantity | Baseline | Rationale |
|---|---:|---|
| Mass m | 1000 kg | Transparent illustrative lumped mass |
| Stiffness k | 100000 N/m | Gives omega_n = 10 rad/s |
| Damping coefficient c | 1000 N s/m | Gives light damping, zeta = 0.05 |
| Initial displacement | 0 m | Initial-velocity release |
| Initial velocity | 0.1 m/s | Same value in every case; well-defined first peak |
| Settling band | +/-2% of each case's peak | Relative decay comparison |

Fixed velocity implies different initial kinetic energies when mass changes (E0 = m v0^2/2). This is intentional: the study fixes initial conditions, not initial energy. A fixed applied impulse would be a different experiment.

## Definitions and method
- Undamped natural angular frequency: omega_n = sqrt(k/m), rad/s; frequency f_n = omega_n/(2 pi), Hz.
- Damping ratio: zeta = c/(2 sqrt(mk)); critical damping c_cr = 2 sqrt(mk).
- First peak time: first positive maximum of x(t) after release. With x(0)=0 and positive initial velocity, this is meaningful in underdamped, critical and overdamped regimes. It is not the forced step-response peak time pi/omega_d.
- Settling time: earliest time after which |x(t)| remains at or below 0.02 times that case's global peak for every future time. It is neither the first band entry nor the end of a finite simulation window. Because each case uses its own peak, this compares fractional decay, not clearance against a single absolute displacement limit.

For zeta < 1, alpha = c/(2m), omega_d = sqrt(omega_n^2-alpha^2):

    x(t) = (v0/omega_d) exp(-alpha t) sin(omega_d t)
    v(t) = v0 exp(-alpha t) [cos(omega_d t) - (alpha/omega_d) sin(omega_d t)]
    t_peak = atan2(omega_d, alpha)/omega_d

The absolute extrema occur at t_peak + n pi/omega_d and decay by exp(-alpha pi/omega_d). The solver finds the last extremum strictly outside the band and uses Brent root finding between it and the following zero. Thus it cannot mistake an early zero crossing for settling.

At critical damping x(t)=v0 t exp(-omega_n t) and t_peak=1/omega_n. Above critical damping, with r_s=-omega_n/(zeta+sqrt(zeta^2-1)) and r_f=-omega_n(zeta+sqrt(zeta^2-1)), x(t)=v0[exp(r_s t)-exp(r_f t)]/(r_s-r_f). Its peak occurs at ln(r_f/r_s)/(r_s-r_f). A doubling bracket and root solve locate settling on the subsequent monotonic tail. With c=0, settling time is infinite. The implementation avoids cancellation close to critical damping using expm1.

### Experimental design
Use 151 equally spaced factors from 0.25 to 4.0, including factor 1.0. For each property, change it alone and hold the other two and the initial velocity fixed: **453 cases** in total. Baseline cases are intentionally repeated across the three sweeps. The default sweep remains underdamped (0.0125 <= zeta <= 0.2); separate validation covers critical and overdamped systems. All quantities use SI units.

The range is shared so relative changes can be compared. Compute dimensionless local sensitivity S_p^y = (p/y)(dy/dp) using centered logarithmic differences at relative step 0.0001. Also compare the full-range span (y_max-y_min)/y_baseline; this is a chosen-range measure, not a universal importance ranking.

## Numerical results
Baseline: omega_n=10 rad/s, f_n=1.59155 Hz, zeta=0.05, first peak time=0.152268 s, peak displacement=9.26692 mm, settling time=7.753210 s.

| Property varied | Factor | omega_n (rad/s) | zeta | First peak (s) | Settling (s) |
|---|---:|---:|---:|---:|---:|
| Mass | 0.25 | 20 | 0.1000 | 0.073902 | 1.993066 |
| Mass | 4.00 | 5 | 0.0250 | 0.309255 | 31.176599 |
| Stiffness | 0.25 | 5 | 0.1000 | 0.295608 | 7.972264 |
| Stiffness | 4.00 | 20 | 0.0250 | 0.077314 | 7.794150 |
| Damping | 0.25 | 10 | 0.0125 | 0.155842 | 31.281880 |
| Damping | 4.00 | 10 | 0.2000 | 0.139768 | 2.099958 |

The complete 453-row table is in sensitivity_data.csv. The actual stiffness-sweep settling minimum and maximum are 7.73233 and 8.11003 s; endpoint values alone miss its nonmonotonic behavior.

## Engineering interpretation
1. **Natural frequency: mass and stiffness are equally influential in relative terms.** Their exact elasticities are -0.5 and +0.5; damping has zero influence on omega_n. A 1% mass increase gives about a 0.5% frequency decrease; a 1% stiffness increase gives about a 0.5% increase. Damped frequency is distinct and does depend on c.
2. **Damping ratio: c is most influential.** Its elasticity is +1, compared with -0.5 for either m or k. Doubling c doubles zeta. Increasing mass at fixed c reduces zeta even though it makes the response decay more slowly in time.
3. **First peak: mass and stiffness dominate near this lightly damped baseline.** Local elasticities are +0.5152 for mass, -0.4848 for stiffness and -0.0304 for damping. The main clock is sqrt(m/k). For this initial-velocity release, increasing damping brings the first peak slightly earlier. This result depends on the stated initial conditions.
4. **Settling: mass and damping dominate the default broad sweep, with nearly equal full-range spans.** At light damping the decay rate is alpha=c/(2m). The familiar 2% estimate is t_s approximately 4/(zeta omega_n)=8m/c, or 8 s at baseline. Quadrupling m gives 31.177 s, while quadrupling c reduces settling to 2.100 s. Changing stiffness mostly changes oscillation phase and the last threshold crossing; the total stiffness-sweep span is only 0.378 s. The estimate is not exact because the band uses each response peak and the actual last crossing lies below an exponential envelope.
5. **Local settling derivatives require care.** At baseline the exact elasticities are +0.5432 (m), -0.4568 (k), -0.08645 (c). These describe only the current final-crossing branch. They do not contradict the broad decay trend. As a later lobe drops below tolerance, the final significant lobe changes and settling can drop abruptly. Report both the full curve and local values rather than using the local derivative as a global ranking.
6. **More damping is not universally faster.** In strongly overdamped systems the slow root approaches -k/c, so tail decay becomes slower as c increases. The baseline ranking is conditional on its range and regime.

## Verification and reproducibility
Run `python -m unittest discover -s tests -v`, then `python -m unittest discover -s tests -p app_smoke.py -v`. Tests compare displacement and velocity with an independent state-matrix exponential in undamped, lightly damped, near-critical, critical and overdamped cases; verify zero velocity at the computed peak, the final band crossing and later response; check energy dissipation, scaling laws, invalid inputs and independent sweeps. Streamlit's AppTest verifies the default app, an overdamped selection and the normalization toggle. Figures are generated only for visualization; their sampling does not determine the response metrics. Root tolerance is 1e-11 s, a numerical tolerance rather than a physical accuracy claim.

Reproduce data and figures with `python run_study.py`. Start the dashboard using `python -m streamlit run app.py`. Build the printable report using `pip install -r requirements-report.txt` followed by `python build_report.py`. GitHub Actions repeats the core and app checks.

## Limitations
This is deterministic one-at-a-time sensitivity, not uncertainty propagation or a design optimization. Interactions between parameters, nonlinear stiffness, nonviscous damping, soil-structure interaction, multiple modes and continuing excitation are excluded. The wide default range is exploratory, not a manufacturing tolerance. A fixed absolute displacement limit or different initial conditions could change settling comparisons. No excavation damage or structural safety conclusion is inferred.

## References
- Chopra, A. K., *Dynamics of Structures*, 5th ed., Pearson, 2017, chapter on free vibration of SDOF systems. Standard governing theory; no claimed page-specific quotation.
- SciPy, `scipy.linalg.expm`, official documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html (independent verification method).
- SciPy, `scipy.optimize.brentq`, official documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html (event root solver).
- Streamlit Community Cloud, deployment documentation: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy.
