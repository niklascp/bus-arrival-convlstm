import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from cycler import cycler

colors = {
    'Bl':(0,0,0),
    'Or':(.9,.6,0),
    'SB':(.35,.7,.9),
    'bG':(0,.6,.5),
    'Ye':(.95,.9,.25),
    'Bu':(0,.45,.7),
    'Ve':(.8,.4,0),
    'rP':(.8,.6,.7),
}

def set_plot_style():
    plt.style.use('ggplot')
    plt.rcParams['font.size'] = 14
    plt.rcParams['figure.figsize'] = (16, 10)

    plt.rcParams['axes.facecolor'] = 'w'
    plt.rcParams['axes.labelcolor'] = 'k'
    plt.rcParams['axes.edgecolor'] = 'k'
    plt.rcParams['axes.prop_cycle'] = cycler('color',  [colors[k] for k in ['Bl', 'Or', 'SB', 'bG', 'Ye', 'Bu', 'Ve', 'rP']])

    plt.rcParams['grid.color'] = (.7, .7, .7, 0)

    plt.rcParams['xtick.color'] = 'k'
    plt.rcParams['xtick.labelsize'] = 16
    plt.rcParams['ytick.color'] = 'k'
    plt.rcParams['ytick.labelsize'] = 16

    plt.rcParams['legend.fontsize'] = 16
    plt.rcParams['legend.frameon'] = True
    plt.rcParams['legend.framealpha'] = 1
    plt.rcParams['legend.facecolor'] = 'w'
    plt.rcParams['legend.edgecolor'] = (.7, .7, .7, 0)