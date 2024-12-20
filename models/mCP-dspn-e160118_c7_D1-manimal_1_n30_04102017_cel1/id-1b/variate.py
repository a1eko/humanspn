#!/usr/bin/env python3
"""
Provide model variability by combining optimized parameters and
morphological reconstructions.
"""


import argparse
import json
import sys
import os

import json
import efel
import numpy as np
import bluepyopt as bpopt
import bluepyopt.ephys as ephys

import matplotlib.pyplot as plt
plt.rcParams.update({'figure.max_open_warning': 0})

import cell_model
import cell_evaluator


cell_id = '160118_c7_D1'
stim_spec = {
    'nsteps': 55,
    'stimuli': [
        {
            'amp_range': [-0.550, 0.500],
            'delay': 700.0,
            'duration': 2000.0,
            'totduration': 3000.0
         }, {
            'amp_range': [0.103, 0.103],
            'delay': 0.0,
            'duration': 3000.0,
            'totduration': 3000.0
         }
    ]
}


class ListEncoder(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=arguments-differ
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        elif isinstance(obj, set):
            return list(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def save_figs(name, figs):
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(name) as ofile:
        for fig in figs:
            ofile.savefig(fig)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parameters', type=str,
                        help='optimized parameters (json)')
    parser.add_argument('morphology', type=str, nargs='+',
                        help='input morphology file (swc)')
    return parser.parse_args()


def get_distance(morphofile):
    ''' def and init cell and return somatic distance of each section sections '''
    # simulator (neuron)
    #nrn_sim = ephys.simulators.NrnSimulator(cvode_active=False)
    nrn_sim = ephys.simulators.NrnSimulator(cvode_active=False, dt=0.100)
    morphology = ephys.morphologies.NrnFileMorphology(
        morphofile, do_replace_axon=True)
    mechanisms = cell_model.define_mechanisms('mechanisms.json')
    # def cell
    cell = ephys.models.CellModel(name='dspn', 
                                  morph=morphology,
                                  mechs=mechanisms)
    cell.instantiate(sim=nrn_sim)
    h = nrn_sim.neuron.h
    origin = h.distance()
    secId2dist = {}
    for sec in h.allsec():
        #if sec.name().find('dend') >= 0:
        if sec.name().find('dend') >= 0 and sec.name().find('dspn[0]') >= 0:
            secId2dist[ int(sec.name().split('[')[2].split(']')[0]) ] = h.distance(0.5, sec=sec)
    return secId2dist


def bap_ca(id2dist, morphofile, version=0):
    # setup
    parameters = cell_model.define_parameters('parameters.json')
    mechanisms = cell_model.define_mechanisms('mechanisms.json')
    protocol_definitions  = json.load(open('config/protocols.json'))
    
    # simulator (neuron)
    #nrn_sim = ephys.simulators.NrnSimulator(cvode_active=False)
    nrn_sim = ephys.simulators.NrnSimulator(cvode_active=False, dt=0.100)
    
    # def morph
    morphology = ephys.morphologies.NrnFileMorphology(
        morphofile, do_replace_axon=True)
    
    cell = ephys.models.CellModel(
        'dspn', 
        morph=morphology, 
        mechs=mechanisms, 
        params=parameters)
    
    # def soma location   
    somacenter_loc = ephys.locations.NrnSeclistCompLocation(
        name='somacenter',
        seclist_name='somatic',
        sec_index=0,
        comp_x=0.5)
    
    # record (ca conc) in middle of all dendritic sections
    sec_loc = []
    REC     = [ ephys.recordings.CompRecording(
                    name='soma.v',
                    location=somacenter_loc,
                    variable='v') ]
    
    N_sec2loop  = len(id2dist)
    
    for secID in range(N_sec2loop):
        sec_loc.append( ephys.locations.NrnSeclistCompLocation(
            name='secCenter%d'%(secID),
            seclist_name='basal',
            sec_index=secID,
            comp_x=0.5))
        REC.append( ephys.recordings.CompRecording(
            name='sec%d.cai' % (secID),
            location=sec_loc[secID],
            variable='cai')   )
        REC.append( ephys.recordings.CompRecording(
            name='sec%d.cali' % (secID),
            location=sec_loc[secID],
            variable='cali')   )

    # set constant istim
    delay       = 150
    relax_time  = delay - 20
    duration    = 250
    
    #protocol_definition = protocol_definitions.items()[0] # select first prot (same in all)
    protocol_definition = next(iter(protocol_definitions.values()))
    stimuli = [] 
    #stimulus_definition = protocol_definition[1]['stimuli'][1]
    stimulus_definition = protocol_definition['stimuli'][1]
    stimuli.append(ephys.stimuli.NrnSquarePulse(
        step_amplitude=stimulus_definition['amp'],
        step_delay=stimulus_definition['delay'],
        step_duration=stimulus_definition['duration'],
        location=somacenter_loc,
        total_duration=duration))
    
    # spike inducing stimuli
    stimuli.append(ephys.stimuli.NrnSquarePulse(
        step_amplitude=3,  # 2.5,
        step_delay=delay,
        step_duration=2,
        location=somacenter_loc,
        total_duration=duration))

    protocol = ephys.protocols.SweepProtocol(
        'netstim_protocol',
        stimuli,
        REC)
    
    best_models = json.load(open('hall_of_fame.json'))  # best_models.json'))   # 
    #best_models = json.load(open('one_par.json'))  # best_models.json'))   # 
    default_param_values = best_models[version]
    
    # run simulation   
    responses = protocol.run(                                                    
        cell_model=cell,                                                         
        param_values=default_param_values,                                              
        sim=nrn_sim) 
    
    # analyse results
    dist  = [] 
    sumCa = []
    
    for secID in range(N_sec2loop):    
        # get ca conc in two pools (from just before stimuli and onward)
        cali = [ responses['sec%d.cali'%(secID)]['voltage'][index]  for index, tt in enumerate(responses['soma.v']['time']) if tt >= relax_time]
        cai  = [ responses['sec%d.cai'%(secID)][ 'voltage'][index]  for index, tt in enumerate(responses['soma.v']['time']) if tt >= relax_time]
        
        dist.append( id2dist[secID] )
        
        # sum of two pools (used instead of average since relative concentration equal pool size)
        sumCa.append( (max(cai)+max(cali)) - (cai[0]+cali[0]) )
    
    
    # sort, normalize and plot peak values
    index       = np.argsort( dist )                                                # sort index of distances
    norm_ind,D  = next(i for i in enumerate(dist) if i[1] < 40 and i[1] > 30)       # get norm index (first section with somatic distance in range 30-40 um)
    
    print(sumCa[norm_ind])
    print(np.mean([sumCa[i] for i in index if dist[i] > 40 and dist[i] < 50]))
    print(np.mean([sumCa[i] for i in index if dist[i] > 50 and dist[i] < 60]))
    print(np.mean([sumCa[i] for i in index if dist[i] > 60 and dist[i] < 100]))
    
    # sum for z-score (only use values from sections within 60-100 um somatic range)
    CforMean    = [sumCa[i] / sumCa[norm_ind]  for i in index if dist[i] > 60 and dist[i] < 100]
    
    # calc z-score
    mean = np.mean( CforMean )
    print('model V: %d\tmean: %0.3f\tz-score: %0.3f' % (version, mean, (mean-0.11)/0.212) )
    return np.mean(CforMean)


def main(args):
    # define variation protocols
    protocol_definitions = dict()
    feature_definitions = dict()
    n = stim_spec['nsteps']
    x = stim_spec['stimuli'][0]
    stim_amps = np.linspace(x['amp_range'][0], x['amp_range'][1], n)
    x = stim_spec['stimuli'][1]
    hold_amps = np.linspace(x['amp_range'][0], x['amp_range'][1], n)
    for i, stim_amp, hold_amp in zip(range(n), stim_amps, hold_amps):
        pd = dict()
        pd['stimuli'] = list()
        stim = {'amp': stim_amp, 'delay': stim_spec['stimuli'][0]['delay'],
                'duration': stim_spec['stimuli'][0]['duration'],
                'totduration': stim_spec['stimuli'][0]['totduration']}
        pd['stimuli'].append(stim)
        hold = {'amp': hold_amp, 'delay': stim_spec['stimuli'][1]['delay'],
                'duration': stim_spec['stimuli'][1]['duration'],
                'totduration': stim_spec['stimuli'][1]['totduration']}
        pd['stimuli'].append(hold)
        fd = dict()
        fd['soma'] = {'Spikecount': [0.0, 1.0]}
        stim_name = f'STIM_{i}'
        protocol_definitions[stim_name] = pd
        feature_definitions[stim_name] = fd

    # simulate models
    parameters = cell_model.define_parameters('parameters.json')
    mechanisms = cell_model.define_mechanisms('mechanisms.json')
    protocols = cell_evaluator.define_protocols(protocol_definitions=protocol_definitions)
    calculator = cell_evaluator.define_fitness_calculator(protocols, feature_definitions=feature_definitions)
    models = json.load(open(args.parameters))
    stimuli = [(protocol_definitions[p]['stimuli'][0]['amp'] + 
                protocol_definitions[p]['stimuli'][1]['amp'])*1e3
                for p in protocol_definitions]

    figs = list()
    cell_specs = list()
    for morph in args.morphology:
        morphology = ephys.morphologies.NrnFileMorphology(morph, do_replace_axon=True)
        cell = ephys.models.CellModel(
            f'str_dspn_{cell_id}',
            morph=morphology,
            mechs=mechanisms,
            params=parameters)
        opt_params = [p.name for p in cell.params.values() if not p.frozen]
        simulator = ephys.simulators.NrnSimulator()
        evaluator = ephys.evaluators.CellEvaluator(
            cell_model=cell,
            param_names=opt_params,
            fitness_protocols=protocols,
            fitness_calculator=calculator,
            sim=simulator)
        for par, param_values in enumerate(models):
            responses = evaluator.run_protocols(
                protocols=protocols.values(),
                param_values=param_values)
            features_sp = ['Spikecount']
            features_iv = ['steady_state_voltage_stimend', 'decay_time_constant_after_stim']
            features_id = ['inv_first_ISI', 'mean_frequency']
            #features_id = ['inv_first_ISI']
            #features_ap = ['spike_half_width', 'AP_rise_rate', 'AP_fall_rate', 'AHP_depth', 'AHP_depth_abs']
            #features_ap = ['AP_begin_voltage', 'AHP_depth', 'AHP_depth_abs']
            features_ap = ['AP_begin_voltage', 'AHP_depth', 'AHP_depth_abs', 'peak_voltage', 'AP_amplitude']
            traces = []
            for resp in responses:
                trace = {}
                trace['T'] = responses[resp]['time']
                trace['V'] = responses[resp]['voltage']
                trace['stim_start'] = [stim_spec['stimuli'][0]['delay']]
                trace['stim_end'] = [stim_spec['stimuli'][0]['delay'] +
                                     stim_spec['stimuli'][0]['duration']]
                traces.append(trace)
            fig, ax = plt.subplots()
            fig.suptitle(f'{cell_id}, {os.path.basename(morph)}, {par=}', fontsize=8)
            for i, resp in enumerate(list(responses.keys())[::-1]):
                trace = {}
                trace['T'] = responses[resp]['time']
                trace['V'] = responses[resp]['voltage']
                trace['stim_start'] = [stim_spec['stimuli'][0]['delay']]
                trace['stim_end'] = [stim_spec['stimuli'][0]['delay'] +
                                     stim_spec['stimuli'][0]['duration']]
                ax.plot(trace['T'], trace['V'], alpha=min(5.0*i/len(list(responses.keys())), 1.0), lw=1)
            figs.append(fig)
            feature_values = efel.getFeatureValues(traces, features_sp)
            n = len(responses)
            for i, resp in enumerate(responses):
                if feature_values[i]['Spikecount'] == 0:
                    trace = {}
                    trace['T'] = responses[resp]['time']
                    trace['V'] = responses[resp]['voltage']
                    trace['stim_start'] = [stim_spec['stimuli'][0]['delay']]
                    trace['stim_end'] = [stim_spec['stimuli'][0]['delay'] +
                                         stim_spec['stimuli'][0]['duration']]
                    feature_values[i] = efel.getFeatureValues([trace], features_sp + features_iv)[0]
                elif feature_values[i]['Spikecount'] == 1:
                    trace = {}
                    trace['T'] = responses[resp]['time']
                    trace['V'] = responses[resp]['voltage']
                    trace['stim_start'] = [stim_spec['stimuli'][0]['delay']]
                    trace['stim_end'] = [stim_spec['stimuli'][0]['delay'] +
                                         stim_spec['stimuli'][0]['duration']]
                    feature_values[i] = efel.getFeatureValues([trace], features_sp + features_ap)[0]
                else:
                    trace = {}
                    trace['T'] = responses[resp]['time']
                    trace['V'] = responses[resp]['voltage']
                    trace['stim_start'] = [stim_spec['stimuli'][0]['delay']]
                    trace['stim_end'] = [stim_spec['stimuli'][0]['delay'] +
                                         stim_spec['stimuli'][0]['duration']]
                    feature_values[i] = efel.getFeatureValues([trace], features_sp + features_ap + features_id)[0]

            id2dist = get_distance(morph)
            bap_ca_value = bap_ca(id2dist, morph, version=par)
            cs = dict()
            cs['ephys'] = cell_id
            cs['morph'] = os.path.basename(morph)
            cs['par'] = par
            cs['stim'] = stimuli
            cs['feat'] = feature_values
            cs['bap_ca'] = bap_ca_value
            cell_specs.append(cs)
            print(f'{cell_id=}, {morph=}, {par=}', flush=True)

    save_figs('var_models.pdf', figs)
    with open('var_models.json', 'w') as f:
        json.dump(cell_specs, f, cls=ListEncoder, indent=4)


if __name__ == '__main__':
    sys.exit(main(parse_args()))
