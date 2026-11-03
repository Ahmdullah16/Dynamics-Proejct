"""Streamlit Community Cloud entrypoint: app.py."""
from pathlib import Path
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from sdof import System, metrics, sweep, local_sensitivity, response
from plots import sensitivity_plot, response_plot, elasticity_plot

st.set_page_config(page_title='SDOF | Free-vibration sensitivity',page_icon='🏗️',layout='wide')
st.markdown('''<style>
.block-container {padding-top:2.3rem;max-width:1250px}
[data-testid="stMetric"] {background:white;padding:1rem;border:1px solid #dfE7ed;border-radius:12px}
h1,h2,h3 {letter-spacing:-.02em}
</style>''',unsafe_allow_html=True)
st.caption('CIVIL PROJECT  /  STRUCTURAL DYNAMICS LAB')
st.title('How do system properties change vibration?')
st.markdown('Explore mass, stiffness and viscous damping independently. Compare exact free responses, measure sensitivity and export the evidence.')
with st.sidebar:
    st.header('Baseline system')
    m=st.number_input('Mass m (kg)',min_value=100.0,max_value=100000.0,value=1000.0,step=100.0)
    k=st.number_input('Stiffness k (N/m)',min_value=1000.0,max_value=10000000.0,value=100000.0,step=1000.0)
    c=st.number_input('Damping c (N·s/m)',min_value=10.0,max_value=100000.0,value=1000.0,step=100.0)
    v0=st.number_input('Initial velocity (m/s)',min_value=0.001,max_value=1.0,value=0.1,step=0.01,format='%.3f')
    tolerance=st.selectbox('Settling band (% of each peak)',[2,5,1],index=0)/100
    limits=st.slider('Independent parameter factor range',0.1,4.0,(0.25,4.0),0.05)
    count=st.select_slider('Samples per parameter',options=[51,101,151,201],value=151)
    st.info('Only the selected parameter changes. Initial displacement is zero and initial velocity is fixed. Damping ratio is calculated, never held fixed during a mass or stiffness sweep.')

baseline=System(m,k,c,v0)
base=metrics(baseline,tolerance)
regime='Underdamped' if base['damping_ratio']<1 else ('Critically damped' if base['damping_ratio']==1 else 'Overdamped')
st.caption(f'{regime} · linear elastic SDOF · SI units · analytical response and event root finding')
columns=st.columns(4)
for col,(label,key,fmt) in zip(columns,[('Natural frequency','frequency_hz','.3f'),('Damping ratio','damping_ratio','.4f'),('First peak time','first_peak_s','.4f'),('Settling time','settling_s','.3f')]):
    col.metric(label,format(base[key],fmt)+(' Hz' if key=='frequency_hz' else ' s' if key.endswith('_s') else ''))

@st.cache_data(show_spinner=False)
def calculate(system,factors,tol):
    return sweep(system,np.asarray(factors),tol),local_sensitivity(system,tol)

factors=tuple(np.unique(np.r_[np.linspace(*limits,count),1.0]))
data,elastic=calculate(baseline,factors,tolerance)
overview,curves,theory,downloads=st.tabs(['Sensitivity study','Free-response comparison','Method & interpretation','Submission downloads'])

def display_figure(fig,name):
    st.pyplot(fig)
    buffer=BytesIO(); fig.savefig(buffer,format='png',dpi=180,bbox_inches='tight')
    st.download_button('Download this plot',buffer.getvalue(),name+'.png','image/png',key=name)
    plt.close(fig)

with overview:
    st.subheader('One parameter changes. What moves most?')
    normalized=st.toggle('Normalize responses to the baseline',value=True)
    display_figure(sensitivity_plot(data,baseline,tolerance,normalized),'sensitivity')
    st.caption(f'{len(data)} one-at-a-time cases. A factor of 1 is the baseline. The selected factor interval is shared across all three properties.')
    st.subheader('Local sensitivity at the current baseline')
    display_figure(elasticity_plot(elastic),'elasticity')
    st.warning('Settling time is the last threshold crossing. Small parameter changes can switch the last significant oscillation, giving sharp changes. Its local derivative may differ strongly from its broad trend; do not infer a global ranking from this heatmap alone.')
    st.dataframe(elastic.style.format('{:+.4f}'),width='stretch')
    st.subheader('Range-based influence for the selected interval')
    span=data.groupby('parameter')[['omega_n_rad_s','damping_ratio','first_peak_s','settling_s']].agg(lambda x: (x.max()-x.min()))
    for key in span:
        span[key]/=base[key]
    st.dataframe(span.style.format('{:.3f}'),width='stretch')
    st.caption('Dimensionless span = (maximum measure − minimum measure) / baseline measure. Ranking depends on the chosen interval and damping regime.')
with curves:
    parameter=st.selectbox('Property to compare',['mass','stiffness','damping'])
    display_figure(response_plot(baseline,parameter,(limits[0],1,limits[1]),tolerance),'response')
    st.info('The first peak is the first positive displacement maximum after release. The settling band is relative to each individual response peak; initial rest at x=0 does not count as settling.')
    st.subheader('Damping regimes')
    st.markdown('Increase c above the critical value to inspect nonoscillatory responses. Excessive damping can make the slow return to equilibrium longer.')
    st.write(f'Current critical damping: **{2*np.sqrt(m*k):,.2f} N·s/m**')
with theory:
    st.latex(r'm\ddot{x}+c\dot{x}+kx=0,\qquad x(0)=0,\quad\dot{x}(0)=v_0')
    st.latex(r'\omega_n=\sqrt{k/m},\qquad \zeta=\frac{c}{2\sqrt{mk}},\qquad \omega_d=\omega_n\sqrt{1-\zeta^2}')
    st.latex(r'x(t)=\frac{v_0}{\omega_d}e^{-\zeta\omega_n t}\sin(\omega_d t)\quad(0\leq\zeta<1)')
    st.latex(r't_p=\frac{\operatorname{atan2}(\omega_d,\zeta\omega_n)}{\omega_d}')
    st.markdown('**Settling:** the earliest time after which |x(t)| stays below the selected fraction of its global peak for all later time. The program locates the last extremum outside the band and solves its final crossing. Critical and overdamped cases use the monotonic tail after their single peak.')
    st.latex(r't_s\approx\frac{4}{\zeta\omega_n}=\frac{8m}{c}\quad\text{(2\% band, light damping only)}')
    st.markdown('''**Engineering interpretation near the default baseline**
- Natural frequency depends equally strongly on mass and stiffness in relative terms: elasticities −0.5 and +0.5. Viscous damping does not change the undamped natural frequency.
- Damping ratio has elasticity +1 to c and −0.5 to either m or k. Thus c has the strongest relative influence.
- First peak time is governed mainly by mass and stiffness at light damping. Increasing c reduces its time slightly for the chosen initial-velocity release.
- Across the default range, settling is governed primarily by damping and mass. The decay rate is c/(2m); stiffness mostly changes phase and the final band crossing. These conclusions can change in overdamped systems.

**Scope:** illustrative linear SDOF study, no continuing external force, no soil interaction, yielding or multimode response. It is not a calibrated building or an excavation safety assessment.''')
    st.markdown('[Read the full study on GitHub](https://github.com/Ahmdullah16/Dynamics-Proejct/blob/main/reports/engineering_interpretation.md)')
with downloads:
    st.subheader('Export your current study')
    st.download_button('Sensitivity data (CSV)',data.to_csv(index=False),'sensitivity_data.csv','text/csv')
    st.download_button('Local sensitivities (CSV)',elastic.to_csv(),'local_sensitivity.csv','text/csv')
    t=np.linspace(0,base['settling_s']*1.15,5000)
    x,v=response(baseline,t)
    st.download_button('Baseline time history (CSV)',pd.DataFrame({'time_s':t,'displacement_m':x,'velocity_m_s':v}).to_csv(index=False),'baseline_response.csv','text/csv')
    root=Path(__file__).parent
    for filename in ('sdof.py','run_study.py','reports/engineering_interpretation.md','reports/SDOF_Sensitivity_Report.pdf'):
        path=root/filename
        if path.exists():
            st.download_button('Download '+path.name,path.read_bytes(),path.name,key=filename)
    st.caption('The PDF contains the submitted default study. Plots and CSV exports above reflect your current settings.')
st.divider()
st.caption('SDOF Sensitivity Lab · reproducible civil engineering project · developed for Ahmdullah')
