#!/usr/bin/python3
"""
Validate single-cell models against population statistics.
"""


import argparse
import json
import sys
import os

import numpy as np


threshold = 3.5  # 3.0


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models', type=str,
                        help='features of the model variations (json)')
    parser.add_argument('population', type=str,
                        help='features of the cell population (json)')
    parser.add_argument('cell', type=str, nargs='+',
                        help='features of a single cell (json)')
    return parser.parse_args()


def get_features(model):
    ephys, morph, par, stim, feat, bap_ca = model.values()
    spec = {'ephys': ephys, 'morph': morph, 'par': par}
    iv_curve = {'stim': [s for s,f in zip(stim,feat) if f['Spikecount'][0]==0],
                'volt': [f['steady_state_voltage_stimend'][0] for s,f in zip(stim,feat) if f['Spikecount'][0]==0]}
    spec['iv_curve'] = iv_curve
    if [s for s,f in zip(stim,feat) if f['Spikecount'][0]>1]:
        id_curve = {'stim': [s for s,f in zip(stim,feat) if f['Spikecount'][0]>1],
                    'freq': [f['mean_frequency'][0] for s,f in zip(stim,feat) if f['Spikecount'][0]>1]}
                    #'freq': [f['inv_first_ISI'][0] for s,f in zip(stim,feat) if f['Spikecount'][0]>1]}
    else:
        id_curve = None
    spec['id_curve'] = id_curve
    features = dict()
    if [s for s,f in zip(stim,feat) if f['Spikecount'][0]>0]:
        features['fi_rheobase'] = [s for s,f in zip(stim,feat) if f['Spikecount'][0]>0][0]
    else:
        features['fi_rheobase'] = None

    from scipy.optimize import curve_fit

    def fit(x, a, b, c, d):
        return a + b*x + np.exp((x-c)/d)

    def dfit(x, a, b, c, d):
        return b + np.exp((x-c)/d)/d

    popt, _ = curve_fit(fit, iv_curve['stim'], iv_curve['volt'],
                        bounds=([-100,0,-1000,1], [0,0.1,1000,1000]))
    slope = dfit(iv_curve['stim'], *popt)
    features['vm_rest'] = fit(0, *popt)
    #features['ir_fitmin'] = min(slope)*1e3
    features['ir_fitmax'] = max(slope)*1e3
    features['ir_fitrest'] = dfit(0, *popt)*1e3
    #features['ir_fitratio'] = features['ir_fitmax'] / features['ir_fitmin']
    #rest = [f for s, f  in zip(stim, feat) if s >= 0.0][0]
    #features['tau_rest'] = rest['decay_time_constant_after_stim'][0]

    if id_curve:
        p = np.polyfit(id_curve['stim'], id_curve['freq'], 1)
        #features['fi_1st_baserate'] = id_curve['freq'][0]
        #features['fi_1st_fitslope'] = p[0]
        #features['fi_1st_fitbaserate'] = p[1]+p[0]*id_curve['stim'][0]
        features['fi_avg_fitslope'] = p[0]
        features['fi_avg_fitbaserate'] = p[1]+p[0]*id_curve['stim'][0]
        #spike_half_width = []
        #for f in feat:
        #    if f['Spikecount'][0] > 0:
        #        spike_half_width.extend(f['spike_half_width'])
        #features['ap_half_width'] = np.mean(spike_half_width)
        #ap_rise_rate = []
        #for f in feat:
        #    if f['Spikecount'][0] > 0:
        #        ap_rise_rate.extend(f['AP_rise_rate'])
        #features['ap_rise_rate'] = np.mean(ap_rise_rate)
        #ap_fall_rate = []
        #for f in feat:
        #    if f['Spikecount'][0] > 0:
        #        ap_fall_rate.extend(f['AP_fall_rate'])
        #features['ap_fall_rate'] = np.mean(ap_fall_rate)
        ap_avg_thresh = []
        ap_peak = []
        ap_amplitude = []
        for f in feat:
            if f['Spikecount'][0] > 0:
                ap_avg_thresh.extend(f['AP_begin_voltage'])
                ap_peak.extend(f['peak_voltage'])
                if f['AP_amplitude']:
                    ap_amplitude.extend(f['AP_amplitude'])
        features['ap_avg_thresh'] = np.mean(ap_avg_thresh)
        features['ap_peak'] = np.mean(ap_peak)
        features['ap_amplitude'] = np.mean(ap_amplitude)
        ahp_depth = []
        ahp_depth_abs = []
        for f in feat:
            if f['Spikecount'][0] > 0:
                ahp_depth.extend(f['AHP_depth'])
                ahp_depth_abs.extend(f['AHP_depth_abs'])
        #features['ahp_depth'] = np.mean(ahp_depth)
        features['ahp_depth'] = np.mean(ap_avg_thresh) - np.mean(ahp_depth_abs)
        features['ahp_depth_abs'] = np.mean(ahp_depth_abs)
    else:
        #features['fi_1st_baserate'] = None
        features['fi_1st_fitslope'] = None
        features['fi_1st_fitbaserate'] = None
        #features['ap_half_width'] = None
        features['ahp_depth'] = None
        features['ahp_depth_abs'] = None
    #features['bap_ca'] = bap_ca
    spec['features'] = features

    return spec


def model_score(spec, objective):
    score = []
    for f in spec['features']:
        v = spec['features'][f] 
        if v is not None and f in objective:
            z = abs(v - objective[f]['mean']) / objective[f]['std']
        else:
            z = 13.13
        score.append(z)
        if z > threshold:
            print(f"{z=}, {f=}, {v=},\n{spec['ephys']=}, {spec['morph']=}, {spec['par']=}\n")
    return np.max(score)


def main(args):
    var_models = json.load(open(args.models))
    pop_features = json.load(open(args.population))
    pop_specs = dict()
    for f in pop_features:
        fs = dict()
        values = pop_features[f]
        fs['mean'] = np.mean(values)
        fs['std'] = np.std(values)
        fs['min'] = np.min(values)
        fs['max'] = np.max(values)
        pop_specs[f] = fs
    #pop_specs['bap_ca'] = {'mean': 0.11, 'std': 0.212}  # dspn values
    sel_models = list()
    rej_models = list()

    for model in var_models:
        mod_specs = get_features(model)
        score = model_score(mod_specs, pop_specs)
        if score < threshold:
            sel_models.append(mod_specs)
        else:
            rej_models.append(mod_specs)

    with open('val_models.json', 'w') as f:
        json.dump(sel_models, f, indent=4)

    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12,6))
    fig.suptitle(f"Model variability, cell {var_models[0]['ephys']} (n={len(sel_models)})")
    ax1.set_title('Subthreshold response')
    ax1.set_ylabel('Voltage (mV)')
    ax1.set_xlabel('Current (pA)')
    ax2.set_title('Discharge rate')
    ax2.set_ylabel('Frequency (Hz)')
    ax2.set_xlabel('Current (pA)')
    ax2.set_xlim(0, 1000)
    ax2.set_ylim(0, 50)

    for model in rej_models:
        ax1.plot(model['iv_curve']['stim'], model['iv_curve']['volt'], color='grey', alpha=0.25)
        ax2.plot(model['id_curve']['stim'], model['id_curve']['freq'], color='grey', alpha=0.25)

    for model in sel_models:
        ax1.plot(model['iv_curve']['stim'], model['iv_curve']['volt'], color='k')#, lw=0.5)
        ax2.plot(model['id_curve']['stim'], model['id_curve']['freq'], color='k')#, lw=0.5)

    #rin = np.array([x['features']['ir_fitrest'] for x in sel_models])
    #print(f"input resistance: {rin.mean():.2f} +- {rin.std():.2f} [{rin.min():.2f}; {rin.max():.2f}]")

    lw = 3
    al = 1.0
    for cell in args.cell:
        spec = json.load(open(cell))
        x = [s[0]['stimulus_total_amp'] for s in spec['cell_features']['IV']]
        y = [s[1]['steady_state_voltage_stimend'][0] for s in spec['cell_features']['IV']]
        ax1.plot(x, y, '.', x, y, color='r', linewidth=lw, alpha=al)
        x = [s[0]['stimulus_total_amp'] for s in spec['cell_features']['IDthresh']]
        #y = [s[1]['inv_first_ISI'][0] for s in spec['cell_features']['IDthresh']]
        y = [s[1]['mean_frequency'][0] for s in spec['cell_features']['IDthresh']]
        coef = np.polyfit(x, y, 2)
        poly = np.poly1d(coef)
        xx = np.linspace(x[0], x[-1])
        yy = poly(xx)
        ax2.plot(x, y, '.', xx, yy, color='r', linewidth=lw, alpha=al)
        lw = 1
        al = 0.25

    plt.show()
    fig.savefig('val_models.png')


if __name__ == '__main__':
    sys.exit(main(parse_args()))
