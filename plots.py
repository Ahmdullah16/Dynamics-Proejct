"""Shared figures with finite-window and undefined-result handling."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace
from sdof import System,metrics,response,time_history
COLORS=['#147d92','#dc6b31','#6555ac']
MEASURES={'omega_n_rad_s':'Natural frequency (rad/s)','damping_ratio':'Damping ratio',
          'first_peak_s':'First future peak time (s)','settling_s':'Settling time (s)'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'figure.dpi':110,'axes.grid':True,'grid.alpha':0.2})


def sensitivity_plot(df,baseline=System(),tolerance=0.02,normalized=False):
    fig,axes=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
    base=metrics(baseline,tolerance)
    for ax,(key,label) in zip(axes.flat,MEASURES.items()):
        any_valid=False
        for color,(p,part) in zip(COLORS,df.groupby('parameter',sort=False)):
            y=part[key].to_numpy().copy()
            if normalized:
                y=y/base[key] if np.isfinite(base[key]) and base[key]>0 else np.full_like(y,np.nan)
            y[~np.isfinite(y)]=np.nan
            any_valid |= np.isfinite(y).any()
            ax.plot(part.factor,y,label=p.capitalize(),color=color,lw=1.8)
        if not any_valid: ax.text(.5,.5,'Not defined for these conditions',transform=ax.transAxes,ha='center')
        ax.axvline(1,color='gray',ls=':',lw=1)
        ax.set(xlabel='Property / baseline property',ylabel='Response / baseline response' if normalized else label,title=label)
    axes[0,0].legend(frameon=False)
    return fig


def display_window(systems,requested=None):
    """Bound chart cost while resolving each oscillation by at least 80 samples."""
    if requested is None:
        values=[metrics(s)['settling_s'] for s in systems]
        finite=[v for v in values if np.isfinite(v) and v>0]
        requested=1.15*max(finite) if finite else 6*max(2*np.pi/s.wn for s in systems)
    desired=min(3600.0,max(0.01,float(requested)))
    max_hz=max((s.wn*np.sqrt(1-s.zeta**2)/(2*np.pi) if s.zeta<1 else 0) for s in systems)
    duration=min(desired,20000/(80*max_hz)) if max_hz else desired
    samples=min(20001,max(1200,int(np.ceil(duration*max_hz*80))+1))
    return duration,samples,duration<desired


def response_plot(baseline=System(),parameter='damping',factors=(0.25,1,4),tolerance=0.02,duration=None,quantity='displacement'):
    systems=[replace(baseline,**{parameter:getattr(baseline,parameter)*f}) for f in factors]
    end,n,_=display_window(systems,duration)
    t=np.linspace(0,end,n)
    fig,ax=plt.subplots(figsize=(10,4),constrained_layout=True)
    for s,f,color in zip(systems,factors,COLORS):
        x,v=response(s,t)
        y={'displacement':x*1000,'velocity':v,'acceleration':-(s.damping*v+s.stiffness*x)/s.mass}[quantity]
        ax.plot(t,y,label=f'{parameter} × {f:g}',color=color,lw=1.1)
    ylabel={'displacement':'Displacement (mm)','velocity':'Velocity (m/s)','acceleration':'Acceleration (m/s²)'}[quantity]
    ax.set(xlabel='Time (s)',ylabel=ylabel,title=f'Independent {parameter} comparison')
    ax.legend(frameon=False)
    return fig


def elasticity_plot(table):
    fig,ax=plt.subplots(figsize=(9,4),constrained_layout=True)
    values=np.asarray(table.values,dtype=float)
    cmap=plt.get_cmap('RdBu_r').copy();cmap.set_bad('#e4e8ed')
    vmax=max(1,float(np.nanmax(np.abs(values)))) if np.isfinite(values).any() else 1
    im=ax.imshow(np.ma.masked_invalid(values),cmap=cmap,vmin=-vmax,vmax=vmax,aspect='auto')
    ax.set_yticks(range(3),table.index)
    ax.set_xticks(range(4),['Natural frequency','Damping ratio','First peak','Settling time'])
    for i in range(3):
        for j in range(4):
            v=values[i,j];ax.text(j,i,f'{v:+.3f}' if np.isfinite(v) else 'N/A',ha='center',va='center')
    fig.colorbar(im,ax=ax,label='Local dimensionless elasticity')
    ax.set_title('Approximate % response change per 1% property change')
    return fig


def history_plot(history,system,result):
    fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True,constrained_layout=True)
    for ax,key,label,color in zip(axes,['displacement_m','velocity_m_s','acceleration_m_s2'],
                                 ['Displacement (mm)','Velocity (m/s)','Acceleration (m/s²)'],COLORS):
        ax.plot(history.time_s,history[key]*(1000 if key=='displacement_m' else 1),color=color,lw=1.2)
        ax.set_ylabel(label)
    band=result['settling_band_m']*1000
    axes[0].axhspan(-band,band,color='#147d92',alpha=.12,label='Settling band')
    for key,label in [('first_peak_s','First future peak'),('settling_s','Final settling')]:
        t=result[key]
        if np.isfinite(t) and 0<t<=history.time_s.iloc[-1]:
            axes[0].axvline(t,ls='--',lw=1,label=label)
    axes[0].legend(frameon=False);axes[-1].set_xlabel('Time (s)')
    return fig


def energy_plot(history):
    fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    for col,color in zip(['kinetic_energy_J','strain_energy_J','total_energy_J'],COLORS):
        axes[0].plot(history.time_s,history[col],label=col.replace('_energy_J','').capitalize(),color=color)
    axes[0].set(xlabel='Time (s)',ylabel='Energy (J)',title='Energy exchange and dissipation');axes[0].legend(frameon=False)
    axes[1].plot(history.displacement_m*1000,history.velocity_m_s,color=COLORS[0],lw=1)
    axes[1].scatter([history.displacement_m.iloc[0]*1000],[history.velocity_m_s.iloc[0]],color=COLORS[1],label='Initial state')
    axes[1].set(xlabel='Displacement (mm)',ylabel='Velocity (m/s)',title='Phase plane');axes[1].legend(frameon=False)
    return fig
