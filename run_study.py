"""Reproduce submission: python run_study.py --output reports"""
import argparse
import json
from pathlib import Path
import matplotlib.pyplot as plt
from sdof import System, metrics, sweep, local_sensitivity
from plots import sensitivity_plot, response_plot, elasticity_plot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='reports')
    args=parser.parse_args()
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    system=System(); data=sweep(system); elastic=local_sensitivity(system)
    data.to_csv(out/'sensitivity_data.csv',index=False)
    elastic.to_csv(out/'local_sensitivity.csv')
    (out/'baseline.json').write_text(json.dumps(metrics(system),indent=2)+'\n')
    figures={'sensitivity_absolute':sensitivity_plot(data),
             'sensitivity_normalized':sensitivity_plot(data,normalized=True),
             'local_elasticity':elasticity_plot(elastic)}
    for parameter in ('mass','stiffness','damping'):
        figures['response_'+parameter]=response_plot(parameter=parameter)
    for name,fig in figures.items():
        fig.savefig(out/(name+'.png'),dpi=200)
        fig.savefig(out/(name+'.svg'))
        plt.close(fig)
    print(json.dumps(metrics(system),indent=2))
    print(elastic.round(5).to_string())
    print(f'Generated {len(data)} independent cases and {len(figures)} figures in {out}')

if __name__=='__main__':
    main()
