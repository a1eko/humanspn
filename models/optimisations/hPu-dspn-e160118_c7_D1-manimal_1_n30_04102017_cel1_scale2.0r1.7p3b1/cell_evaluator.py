# Original file l5pc_evaluator.py by Werner Van Geit at EPFL/Blue Brain Project
# Modified by Alexander Kozlov <akozlov@kth.se>

import os
import json

import cell_model

import bluepyopt.ephys as ephys

script_dir = os.path.dirname(__file__)
config_dir = os.path.join(script_dir, 'config')


def define_protocols(filename=None, protocol_definitions=None):
    if not protocol_definitions:
        protocol_definitions = json.load(open(os.path.join(config_dir, filename)))
    protocols = {}
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name='soma',
        seclist_name='somatic',
        sec_index=0,
        comp_x=0.5)
    for protocol_name, protocol_definition in protocol_definitions.items():
        # By default include somatic recording, could be any
        somav_recording = ephys.recordings.CompRecording(
            name='%s.soma.v' %
            protocol_name,
            location=soma_loc,
            variable='v')
        recordings = [somav_recording]
        if 'extra_recordings' in protocol_definition:
            for recording_definition in protocol_definition['extra_recordings']:
                if recording_definition['type'] == 'somadistance':
                    location = ephys.locations.NrnSomaDistanceCompLocation(
                        name=recording_definition['name'],
                        soma_distance=recording_definition['somadistance'],
                        seclist_name=recording_definition['seclist_name'])
                    var = recording_definition['var']
                    recording = ephys.recordings.CompRecording(
                        name='%s.%s.%s' % (protocol_name, location.name, var),
                        location=location,
                        variable=recording_definition['var'])
                    recordings.append(recording)
                else:
                    raise Exception(
                        'Recording type %s not supported' %
                        recording_definition['type'])
        stimuli = []
        for stimulus_definition in protocol_definition['stimuli']:
            stimuli.append(ephys.stimuli.NrnSquarePulse(
                step_amplitude=stimulus_definition['amp'],
                step_delay=stimulus_definition['delay'],
                step_duration=stimulus_definition['duration'],
                location=soma_loc,
                total_duration=stimulus_definition['totduration']))
        protocols[protocol_name] = ephys.protocols.SweepProtocol(
            protocol_name,
            stimuli,
            recordings)
    return protocols


def define_fitness_calculator(protocols, filename=None, feature_definitions=None):
    if not feature_definitions:
        feature_definitions = json.load(open(os.path.join(config_dir, filename)))
    objectives = []
    for protocol_name, locations in feature_definitions.items():
        for location, features in locations.items():
            for efel_feature_name, meanstd in features.items():
                feature_name = '%s.%s.%s' % (
                    protocol_name, location, efel_feature_name)
                recording_names = {'': '%s.%s.v' % (protocol_name, location)}
                stimulus = protocols[protocol_name].stimuli[0]
                stim_start = stimulus.step_delay
                if location == 'soma':
                    threshold = -20
                elif 'dend' in location:
                    threshold = -55
                stim_end = stimulus.step_delay + stimulus.step_duration
                feature = ephys.efeatures.eFELFeature(
                    feature_name,
                    efel_feature_name=efel_feature_name,
                    recording_names=recording_names,
                    stim_start=stim_start,
                    stim_end=stim_end,
                    exp_mean=meanstd[0],
                    exp_std=meanstd[1],
                    threshold=threshold)
                objective = ephys.objectives.SingletonObjective(
                    feature_name,
                    feature)
                objectives.append(objective)
    fitcalc = ephys.objectivescalculators.ObjectivesCalculator(objectives)
    return fitcalc
