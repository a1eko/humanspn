import bluepyopt as bpopt
import bluepyopt.ephys as ephys


morphology = ephys.morphologies.NrnFileMorphology(
    'morphology/AB5_porta76_cel3.swc',
    do_replace_axon=True)

import cell_model
parameters = cell_model.define_parameters('parameters.json')
#for x in parameters: print(x)

mechanisms = cell_model.define_mechanisms('mechanisms.json')

cell = ephys.models.CellModel(
    'dspn', 
    morph=morphology, 
    mechs=mechanisms, 
    params=parameters)

opt_params = [p.name for p in cell.params.values() if not p.frozen]
#for x in opt_params: print(x)

import cell_evaluator
protocols = cell_evaluator.define_protocols('protocols.json')

calculator = cell_evaluator.define_fitness_calculator(
    protocols, 
    'features.json')

#simulator = ephys.simulators.NrnSimulator()
simulator = ephys.simulators.NrnSimulator(cvode_minstep=1e-3)

evaluator = ephys.evaluators.CellEvaluator(
    cell_model=cell,
    param_names=opt_params,
    fitness_protocols=protocols,
    fitness_calculator=calculator,
    sim=simulator)

offspring_size = 570
ngenerations = 200 # 500 # 200 # 50

from ipyparallel import Client
rc = Client()
lview = rc.load_balanced_view()

optimiser = bpopt.optimisations.DEAPOptimisation(
    evaluator=evaluator,
    offspring_size=offspring_size,
    map_function=lview.map_sync,
    seed=1)

print()

pop, hof, log, hist = optimiser.run(max_ngen=ngenerations)
print(log)

import json
best_models = []
for record in hof:
    params = evaluator.param_dict(record)
    best_models.append(params)

with open('best_models.json', 'w') as fp:
    json.dump(best_models, fp, indent=4)

with open('log.json', 'w') as fp:
    json.dump(log, fp, indent=4)
