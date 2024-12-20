import numpy as np
import matplotlib.pyplot as plt


def plot_responses0(responses, expdata=None, junction_potential=0, figsize=None):
    fig, axes = plt.subplots(len(responses), figsize=figsize)
    for index, (name, response) in enumerate(sorted(responses.items())):
        if name in expdata:
            data = np.loadtxt(expdata[name])
            time = data[:,0]
            voltage = data[:,1] - junction_potential
            axes[index].plot(time, voltage, color='lightgrey', linewidth=3)
        axes[index].plot(response['time'], response['voltage'])
        axes[index].set_title(name, size='small')
    fig.tight_layout()

def plot_responses(responses, expdata=[], junction_potential=0, figsize=None, fig=None, ax=None):
    if not ax:
        fig, axes = plt.subplots(len(responses), figsize=figsize)
    for index, (name, response) in enumerate(sorted(responses.items())):
        axis = axes[index] if not ax else ax
        if name in expdata:
            data = np.loadtxt(expdata[name])
            time = data[:,0]
            voltage = data[:,1] - junction_potential
            axis.plot(time, voltage, color='lightgrey')
        axis.plot(response['time'], response['voltage'])
        if not ax:
            axis.set_title(name, size='small')
    fig.tight_layout()


def plot_objectives(objectives, threshold=3, figsize=None):
    ytick_pos = [x + 0.5 for x in range(len(objectives))]
    obj_keys = sorted(objectives.keys())[::-1]
    obj_val = [objectives[x] for x in obj_keys]
    mean_score = np.round(np.mean(obj_val), 3)
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(ytick_pos, obj_val, height=0.75)
    ax.axvline(threshold, color = "lightgray", linewidth=3, alpha=0.7)
    ax.set_yticklabels(obj_keys, size='small')
    ax.set_yticks(ytick_pos)
    ax.set_xscale('log')
    ax.set_xlabel("Feature errors (# STD)")
    ax.set_title('Mean score: ' + str(mean_score))
    fig.tight_layout()


def plot_log(log, figsize=None):
    gennrs = np.array([x['gen'] for x in log])
    minfit = np.array([x['min'] for x in log])
    maxfit = np.array([x['max'] for x in log])
    avgfit = np.array([x['avg'] for x in log])
    stdfit = np.array([x['std'] for x in log])
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(gennrs, minfit, linewidth=3)
    ax.plot(gennrs, maxfit, color='lightgrey')
    ax.plot(gennrs, avgfit, color='black')
    ax.fill_between(gennrs, minfit, avgfit+stdfit, color='lightgrey')
    ax.set_ylabel('Error score')
    ax.set_xlabel('Generations')
    ax.loglog()
    fig.tight_layout()


def plot_scores(df, figsize=None, **kwargs):
    fig, ax = plt.subplots(figsize=figsize)
    plt.pcolor(df, cmap='BuPu', **kwargs)
    plt.yticks(np.arange(0.5, len(df.index), 1), df.index, size='small')
    plt.xticks(np.arange(0.5, len(df.columns), 1), df.columns)
    ax.set_xlabel('Individuals')
    ax.set_title('Feature scores')
    fig.tight_layout()
