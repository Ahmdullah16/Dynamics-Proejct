"""Interactive SDOF free-vibration laboratory; deploy via streamlit.py or app.py."""
from pathlib import Path
from io import BytesIO
from dataclasses import replace,asdict
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from sdof import System,metrics,sweep,local_sensitivity,time_history
from plots import (sensitivity_plot,response_plot,elasticity_plot,history_plot,energy_plot,display_window,MEASURES)
from theory_ui import render_theory

st.set_page_config(page_title='SDOF | Interactive Dynamics Lab',page_icon='🏗️',layout='wide')
st.markdown('''<style>.block-container{padding-top:2rem;max-width:1250px}
[data-testid="stMetric"]{padding:.8rem;border:1px solid #cbdde8;border-radius:12px;background:rgba(20,125,146,.06)}
h1,h2,h3{letter-spacing:-.02em}</style>''',unsafe_allow_html=True)

DEFAULTS=dict(mass=1000.,stiffness=100000.,damping=1000.,x0=0.,v0=.1,zeta_input=.05,
              damping_mode='Coefficient c',tolerance_pct=2.,factor_range=(.25,4.),sample_count=151,
              auto_duration=True,duration=10.)

def set_preset(name):
    st.session_state.update(DEFAULTS)
    st.session_state.damping={'Default':1000.,'Undamped':0.,'Critical':20000.,'Overdamped':40000.}[name]

with st.sidebar:
    st.header('System controls')
    st.caption('Change a value and press Enter or leave the field. Results and visible graphs recalculate automatically.')
    st.button('Reset baseline',on_click=set_preset,args=('Default',),width='stretch')
    m=st.number_input('Mass m (kg)',100.,100000.,1000.,100.,key='mass')
    k=st.number_input('Stiffness k (N/m)',1000.,10000000.,100000.,1000.,key='stiffness')
    damping_mode=st.selectbox('Damping input',['Coefficient c','Damping ratio ζ'],key='damping_mode')
    if damping_mode=='Coefficient c':
        c=st.number_input('Damping c (N·s/m)',0.,100000.,1000.,100.,key='damping')
    else:
        z=st.number_input('Damping ratio ζ',0.,3.,.05,.01,format='%.4f',key='zeta_input')
        c=2*z*np.sqrt(m*k)
        st.caption(f'Derived c = {c:,.6g} N·s/m; ζ is used to set this baseline only.')
    x0=st.number_input('Initial displacement x₀ (m)',-.5,.5,0.,.001,format='%.4f',key='x0')
    v0=st.number_input('Initial velocity v₀ (m/s)',-5.,5.,.1,.01,format='%.4f',key='v0')
    tolerance=st.number_input('Settling tolerance (% of peak)',.1,10.,2.,.1,key='tolerance_pct')/100
    st.subheader('Sweep & plotting')
    limits=st.slider('Independent property factor range',.1,4.,(.25,4.),.05,key='factor_range')
    count=st.select_slider('Samples per property',options=[51,101,151,201],value=151,key='sample_count')
    auto=st.toggle('Automatic plot duration',value=True,key='auto_duration')
    requested=st.number_input('Plot duration (s)',.01,3600.,10.,1.,key='duration',disabled=auto)
    with st.expander('Try another damping regime'):
        for preset in ('Undamped','Critical','Overdamped'):
            st.button(preset,on_click=set_preset,args=(preset,),key='preset_'+preset)
        st.caption('Presets reset system properties and initial conditions for a reproducible example.')
    with st.expander('Input limits & meanings'):
        st.markdown('''- m: 100 to 100000 kg; k: 1000 to 10000000 N/m.
- c mode: 0 to 100000 N·s/m; ζ mode: 0 to 3, with c derived from m and k.
- x₀: −0.5 to +0.5 m; v₀: −5 to +5 m/s.
- Settling tolerance: 0.1% to 10% of each response peak.
- Sweep factors: 0.1 to 4; 51 to 201 requested samples. Baseline factor 1 is always included.
- Plot duration: 0.01 to 3600 s. Long plots are shortened if needed to resolve oscillations within 20001 points.

These are educational exploration limits. Linear elastic validity for a real structure requires its own assessment. Frequency, period and damping ratio are calculated quantities; they cannot all vary independently of m, k and c.''')

system=System(m,k,c,v0,x0); result=metrics(system,tolerance)
regime='Undamped' if c==0 else 'Underdamped' if system.zeta<1 else 'Critical' if system.zeta==1 else 'Overdamped'
st.caption('CIVIL PROJECT / STRUCTURAL DYNAMICS LAB · version 2.0')
st.title('Explore free vibration')
st.markdown('Vary mass, stiffness, damping and initial conditions. Follow the motion, compare sensitivity, and learn the mathematics behind every result.')
st.caption(f'{regime} · m = {m:g} kg · k = {k:g} N/m · c = {c:.6g} N·s/m · x₀ = {x0:g} m · v₀ = {v0:g} m/s')

def formatted(value,unit=''):
    if np.isnan(value): return 'N/A'
    if np.isinf(value): return 'Never settles'
    return f'{value:.5g}'+(' '+unit if unit else '')

cols=st.columns(4)
for col,(label,key,unit) in zip(cols,[('Natural frequency','frequency_hz','Hz'),('Damping ratio','damping_ratio',''),('First future peak','first_peak_s','s'),('Settling time','settling_s','s')]):
    col.metric(label,formatted(result[key],unit))
if x0==0 and v0==0: st.info('Both initial conditions are zero: the system stays at rest. Settling time is 0 s, and no future peak exists.')
elif c==0: st.info('Undamped free vibration persists indefinitely. Settling time is infinite; the displayed interval is a finite view of the motion.')
if np.isnan(result['first_peak_s']) and result['peak_displacement_m']>0:
    st.info('This response has no future displacement turning point. The global maximum includes the initial state at t = 0.')

page=st.radio('Explore the lab',['Results','Sensitivity','Compare','Concepts & mathematics','Downloads'],horizontal=True,label_visibility='collapsed',key='page')

@st.cache_data(show_spinner=False,max_entries=24)
def calculate(s,factors,tol): return sweep(s,np.asarray(factors),tol),local_sensitivity(s,tol)

factors=tuple(np.unique(np.r_[np.linspace(*limits,count),1.0]))

@st.cache_data(show_spinner=False,max_entries=24)
def history(s,end,n): return time_history(s,end,n)

end,n,truncated=display_window([system],None if auto else requested)
# Automatic window follows the selected tolerance, rather than a fixed 2%.
if auto and np.isfinite(result['settling_s']) and result['settling_s']>0:
    end,n,truncated=display_window([system],result['settling_s']*1.15)
trajectory=history(system,end,n)


def show(fig,key):
    st.pyplot(fig)
    buffer=BytesIO();fig.savefig(buffer,format='png',dpi=150,bbox_inches='tight')
    st.download_button('Download plot (PNG)',buffer.getvalue(),key+'.png','image/png',key='plot_'+key)
    plt.close(fig)


def window_notice(duration,samples,shortened=False):
    st.caption(f'Chart/export interval: 0 to {duration:.6g} s · {samples} points. Response metrics use the analytical solution for all future time.')
    if shortened: st.info('The requested window was shortened to resolve the fastest oscillation without excessive chart sampling. Metrics are unchanged.')


if page=='Results':
    st.subheader('Displacement, velocity & acceleration')
    window_notice(end,n,truncated)
    if np.isfinite(result['settling_s']) and result['settling_s']>end:
        st.caption('The computed final settling event occurs after this chart window.')
    show(history_plot(trajectory,system,result),'time_history')
    st.subheader('Energy & phase plane')
    show(energy_plot(trajectory),'energy_phase')
    st.subheader('All calculated outputs')
    labels={'omega_n_rad_s':'Natural angular frequency (rad/s)','frequency_hz':'Natural frequency (Hz)',
            'period_s':'Natural period (s)','damping_ratio':'Damping ratio',
            'critical_damping_N_s_m':'Critical damping (N·s/m)','damped_frequency_rad_s':'Damped angular frequency (rad/s)',
            'decay_rate_s_inv':'Decay coefficient α (1/s)','first_peak_s':'First future peak time (s)',
            'peak_displacement_m':'Global peak magnitude (m)','settling_band_m':'Settling half-band (m)',
            'settling_s':'Final settling time (s)','initial_energy_J':'Initial mechanical energy (J)'}
    st.dataframe(pd.DataFrame({'Measure':list(labels.values()),'Current value':[formatted(result[key]) for key in labels]}),hide_index=True,width='stretch')
    st.caption('Peak time excludes t = 0; global peak magnitude includes it. N/A damped frequency means the system is nonoscillatory.')
    st.markdown(f'**Current settling band:** ±{result["settling_band_m"]*1000:.5g} mm, equal to {tolerance*100:g}% of this response’s peak. The same relative definition is applied separately to every sweep case.')

elif page=='Sensitivity':
    data,elastic=calculate(system,factors,tolerance)
    st.subheader('Independent property sensitivity')
    normalized=st.toggle('Normalize responses to the baseline',value=False,key='normalize')
    show(sensitivity_plot(data,system,tolerance,normalized),'sensitivity')
    st.caption(f'{len(data)} cases; baseline factor 1 is always included. Only m, k or c changes in each curve. Initial conditions are fixed.')
    if c==0: st.info('A multiplicative damping sweep keeps c = 0. Set a positive baseline c to inspect damping-coefficient sensitivity.')
    st.subheader('Local dimensionless sensitivity')
    show(elasticity_plot(elastic),'elasticity')
    st.dataframe(elastic.style.format('{:+.4f}',na_rep='N/A'),width='stretch')
    st.caption('N/A means the input is zero or the output is zero, infinite or undefined, so a relative logarithmic derivative is not meaningful.')
    st.warning('Exact settling can jump when the last significant oscillation changes. A local derivative is not a global ranking; inspect the full curves and chosen-range influence below.')
    st.subheader('Which property has the greatest influence in this range?')
    span=pd.DataFrame(index=['mass','stiffness','damping'])
    for key in MEASURES:
        ref=result[key];values=[]
        for p in span.index:
            y=data.loc[data.parameter==p,key].to_numpy()
            valid=np.isfinite(ref) and ref>0 and np.isfinite(y).all()
            values.append((y.max()-y.min())/abs(ref) if valid else np.nan)
        span[key]=values
    st.dataframe(span.style.format('{:.4f}',na_rep='N/A'),width='stretch')
    for key,label in MEASURES.items():
        series=span[key].dropna()
        if series.empty: st.write(f'**{label}:** no finite relative ranking for the selected conditions.')
        elif series.max()<1e-12: st.write(f'**{label}:** unchanged across this sweep.')
        else:
            winners=series.index[np.isclose(series,series.max(),rtol=.01,atol=1e-10)]
            st.write(f'**{label}:** largest chosen-range influence: **{", ".join(winners)}** (within 1% of the largest span).')
    st.caption('Influence = (maximum − minimum)/|baseline|. Undefined cases are retained as N/A instead of being silently omitted from a ranking.')
    st.markdown('**Why:** frequency follows √(k/m); damping ratio follows c/(2√(mk)). At light damping, envelope decay follows c/(2m). For strong overdamping, the slow root approaches −k/c. Peak and exact settling behavior also depends on initial conditions and the last band crossing.')
    with st.expander('All sweep cases'):
        st.dataframe(data,width='stretch')

elif page=='Compare':
    st.subheader('Compare three free responses')
    parameter=st.selectbox('Property to compare',['mass','stiffness','damping'],key='comparison_parameter')
    quantity=st.selectbox('Response quantity',['displacement','velocity','acceleration'],key='comparison_quantity')
    comparison_factors=tuple(dict.fromkeys((limits[0],1.,limits[1])))
    systems=[replace(system,**{parameter:getattr(system,parameter)*f}) for f in comparison_factors]
    cases=[metrics(s,tolerance) for s in systems]
    finite=[r['settling_s'] for r in cases if np.isfinite(r['settling_s']) and r['settling_s']>0]
    desired=(1.15*max(finite) if finite else None) if auto else requested
    comp_end,comp_n,short=display_window(systems,desired)
    show(response_plot(system,parameter,comparison_factors,tolerance,comp_end,quantity),'comparison')
    window_notice(comp_end,comp_n,short)
    st.dataframe(pd.DataFrame([dict(factor=f,**asdict(s),**r) for f,s,r in zip(comparison_factors,systems,cases)]),hide_index=True,width='stretch')
    st.caption('The comparison uses the selected lower factor, baseline 1, and upper factor. All other physical inputs and both initial conditions stay fixed.')

elif page=='Concepts & mathematics':
    render_theory(system,result,tolerance)

else:
    st.subheader('Download the current recalculated study')
    data,elastic=calculate(system,factors,tolerance)
    st.download_button('Full sensitivity data (CSV)',data.to_csv(index=False),'sensitivity_data.csv','text/csv')
    st.download_button('Local sensitivity (CSV)',elastic.to_csv(),'local_sensitivity.csv','text/csv')
    st.download_button('Time history with energy (CSV)',trajectory.to_csv(index=False),'time_history.csv','text/csv')
    payload={'system':asdict(system),'settling_tolerance':tolerance,'factor_range':limits,'samples_per_property':count,
             'plot_duration_s':end,'metrics':{k:(float(v) if np.isfinite(v) else 'infinite' if np.isinf(v) else None) for k,v in result.items()}}
    st.download_button('Inputs and calculated metrics (JSON)',json.dumps(payload,indent=2,allow_nan=False),'current_study.json','application/json')
    lines=['# Current SDOF free-vibration study','',f'Inputs: {asdict(system)}',f'Settling tolerance: {tolerance*100:g}% of each peak.','',pd.DataFrame({'Measure':list(result),'Value':[formatted(v) for v in result.values()]}).to_csv(index=False),'','## Model',r'm x\'\' + c x\' + k x = 0. Analytical solutions; initial conditions fixed during independent sweeps.','',f'Exported chart interval: 0 to {end:g} s; metrics are not truncated to this interval.']
    st.download_button('Current study summary (Markdown)','\n'.join(lines),'current_study.md','text/markdown')
    window_notice(end,n,truncated)
    st.subheader('Reference submission and source')
    root=Path(__file__).parent
    for filename in ('sdof.py','run_study.py','reports/engineering_interpretation.md','reports/SDOF_Sensitivity_Report.pdf'):
        path=root/filename
        if path.exists(): st.download_button('Download '+path.name,path.read_bytes(),path.name,key=filename)
    st.caption('The reference PDF describes the original default study. Current CSV/JSON/Markdown downloads above reflect the controls you have selected.')
st.divider()
st.caption('SDOF Dynamics Lab v2.0 · analytical event metrics · automatic recalculation · developed for Ahmdullah')
