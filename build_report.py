"""Build the concise printable submission after running run_study.py."""
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from sdof import System, metrics

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reports'
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCustom',fontName='Helvetica-Bold',fontSize=23,leading=28,textColor=colors.HexColor('#152c40'),spaceAfter=16))
styles.add(ParagraphStyle(name='SmallCustom',fontSize=9,leading=13,spaceAfter=6))
styles['BodyText'].fontSize=10
styles['BodyText'].leading=14
styles['BodyText'].spaceAfter=8
styles['Heading2'].textColor=colors.HexColor('#147d92')
story=[]

def para(text,style='BodyText'):
    story.append(Paragraph(text,styles[style]))

def heading(text): para(text,'Heading2')

def table(rows,widths):
    body=[[Paragraph(escape(str(x)),styles['SmallCustom']) for x in row] for row in rows]
    t=Table(body,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f1f4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#147d92')),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f8fa')])]))
    story.append(t); story.append(Spacer(1,10))

def fig(name,width,height):
    story.append(Image(str(OUT/name),width=width,height=height))

def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#dce4e9'));canvas.line(42,37,553,37)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526371'))
    canvas.drawString(42,25,'CIVIL PROJECT | Free-vibration sensitivity | SI units')
    canvas.drawRightString(553,25,str(doc.page))

r=metrics(System())
para('STRUCTURAL DYNAMICS / NUMERICAL STUDY','SmallCustom')
para('Sensitivity of free-vibration response to system properties','TitleCustom')
para('A reproducible SDOF study of independent mass, stiffness and viscous damping variations. Prepared for Ahmdullah.','BodyText')
heading('1. Objective and governing model')
para('Quantify changes in natural frequency, damping ratio, first peak time and settling time. Use an ideal linear single-degree-of-freedom system with fixed support and no external force after release.')
para('<b>m x&#8243; + c x&#8242; + k x = 0</b>, with x(0) = 0 and x&#8242;(0) = v<sub>0</sub>. Displacement is measured from static equilibrium. Constant properties, linear elasticity and viscous damping are assumed.')
table([['Input','Baseline','Purpose'],['Mass, m','1000 kg','Illustrative lumped mass'],['Stiffness, k','100000 N/m','Natural angular frequency 10 rad/s'],['Damping, c','1000 N s/m','Light damping, ratio 0.05'],['Initial velocity','0.1 m/s','Fixed for every case'],['Initial displacement','0 m','First positive peak after release']], [140,130,241])
heading('2. Experimental design and response measures')
para('Change one property at a time over factors 0.25 to 4.0 of baseline, with 151 values per property: <b>453 cases</b>. All other inputs remain fixed. The default study stays underdamped; separate checks cover critical and overdamped systems. Fixed velocity means initial kinetic energy changes when mass changes.')
para('<b>Frequency:</b> omega<sub>n</sub> = sqrt(k/m), f<sub>n</sub> = omega<sub>n</sub>/(2 pi). <b>Damping ratio:</b> zeta = c/[2 sqrt(mk)]. <b>First peak:</b> the first positive displacement maximum after release, not the peak of a forced step response.')
para('<b>Settling:</b> final entry into +/-2% of each case\'s own global peak, remaining there forever. This compares fractional decay; it does not impose a single absolute clearance limit. Initial band entry at t = 0 does not count.')
para('Analytical responses locate extrema exactly. The final band crossing is refined by Brent root finding, independent of plot sampling. For undamped motion settling is infinite.','SmallCustom')
story.append(PageBreak())
heading('3. Computed results and engineering interpretation')
para(f'<b>Baseline:</b> f<sub>n</sub> = {r["frequency_hz"]:.5f} Hz; zeta = 0.05; first peak = {r["first_peak_s"]:.6f} s; peak = {1000*r["peak_displacement_m"]:.5f} mm; settling = {r["settling_s"]:.6f} s.')
df=pd.read_csv(OUT/'sensitivity_data.csv')
rows=[['Changed property','Factor','omega_n (rad/s)','zeta','First peak (s)','Settling (s)']]
for p in ('mass','stiffness','damping'):
    for f in (0.25,4):
        row=df[(df.parameter==p)&(df.factor==f)].iloc[0]
        rows.append([p.capitalize(),f,f'{row.omega_n_rad_s:.2f}',f'{row.damping_ratio:.4f}',f'{row.first_peak_s:.5f}',f'{row.settling_s:.5f}'])
table(rows,[105,43,95,60,100,108])
for title,text in [
('Natural frequency: mass and stiffness tie in relative sensitivity.','Exact elasticities are -0.5 for mass, +0.5 for stiffness and zero for damping. Increasing mass slows the vibration; increasing stiffness speeds it up. Undamped and damped natural frequencies are different quantities.'),
('Damping ratio: damping coefficient has the strongest influence.','Its elasticity is +1 to c and -0.5 to either m or k. A 1% increase in c gives a 1% increase in zeta locally.'),
('First peak: mainly mass and stiffness at light damping.','Baseline elasticities are +0.5152 (m), -0.4848 (k) and -0.0304 (c). The dominant time scale is sqrt(m/k). For the specified initial-velocity release, damping brings the first peak slightly earlier.'),
('Settling: damping and mass dominate over the default range.','Their full-range spans are almost equal, about 29.18 s each; stiffness spans only 0.378 s. The light-damping estimate is 4/(zeta omega_n) = 8m/c = 8 s at baseline. Decay rate c/(2m) explains this trend.'),
('The local settling derivative is not a global ranking.','At baseline its elasticities are +0.5432 (m), -0.4568 (k), -0.08645 (c). These belong to one final-crossing branch. As a later lobe falls below the band, settling can drop abruptly. Stiffness-sweep settling is nonmonotonic: 7.7323 to 8.1100 s.'),
('More damping is not always faster.','At strong overdamping the slow root approaches -k/c, so adding damping can lengthen the tail. Rankings depend on the parameter range, initial conditions and settling definition.')]:
    para('<b>'+title+'</b> '+text,'SmallCustom')
para('Local elasticity is S = (p/y)(dy/dp), estimated by centered logarithmic differences with relative step 0.0001. A value of +0.5 means about +0.5% response change for +1% input change.','SmallCustom')
story.append(PageBreak())
heading('4. Sensitivity plots')
fig('sensitivity_absolute.png',511,325)
para('<b>Figure 1.</b> Independent one-at-a-time sweeps. Each horizontal coordinate is the varied property divided by its baseline value; other properties and initial conditions remain fixed. Settling uses the actual final band crossing.','SmallCustom')
fig('local_elasticity.png',511,227)
para('<b>Figure 2.</b> Baseline local dimensionless sensitivity. Interpret the settling column together with the full settling curve above. A normalized four-panel comparison is also included in the supplied plot files.','SmallCustom')
story.append(PageBreak())
heading('5. Response plots, validation and reproducibility')
for parameter in ('mass','stiffness','damping'):
    fig('response_'+parameter+'.png',465,186)
para('<b>Validation:</b> independent state-matrix exponential checks across eight damping ratios (0 to 20), peak velocity, final band crossings and future tail, energy decay, scaling laws and invalid inputs. Streamlit AppTest covers default and overdamped settings and normalization. Root tolerance: 1e-11 s; not a physical accuracy claim.','SmallCustom')
para('<b>Reproduce:</b> pip install -r requirements.txt; python run_study.py; python -m unittest discover -s tests -v. Launch: python -m streamlit run app.py. Full derivations, references, limitations and deployment steps are in the Markdown report and README.','SmallCustom')
para('<b>Limitations:</b> illustrative linear SDOF, deterministic one-at-a-time study. No parameter interactions, continuing excitation, yielding, soil interaction or higher modes. Not a structural safety assessment. Theory: Chopra, Dynamics of Structures, 5th ed. (2017), free-vibration chapter; numerical methods: official SciPy expm and brentq documentation.','SmallCustom')
SimpleDocTemplate(str(OUT/'SDOF_Sensitivity_Report.pdf'),pagesize=(595.28,841.89),rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=47,title='Sensitivity of free-vibration response to system properties',author='Ahmdullah').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT/'SDOF_Sensitivity_Report.pdf')
