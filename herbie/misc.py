## Brian Blaylock
## May 13, 2021

import matplotlib.pyplot as plt

def HerbieLogo():
    """Logo of Herbie The Love Bug"""
    colors = dict(body='#f0ead2', 
                red='#88211b', 
                blue='#0c3576', 
                white='#ffffff', 
                black='#000000')

    plt.figure(figsize=[5,5], facecolor='b')

    plt.axis([-10, 10, -10, 10])
    #plt.axis("equal")

    plt.axvline(2.5, lw=20, color=colors['red'])
    plt.axvline(5.5, lw=40, color=colors['blue'])

    c=plt.Circle((0, 0), radius=6, ec='k', fc='w', zorder=10, linewidth=3)
    plt.gca().add_artist(c)

    plt.text(0,0, '53', fontsize=110, fontweight='bold', va='center_baseline', ha='center', zorder=11)

    #add circle to plot (gca means "get current axis")

    plt.gca().set_facecolor(colors['body'])

    plt.gca().get_xaxis().set_visible(False)
    plt.gca().get_yaxis().set_visible(False)

    plt.gca().spines['bottom'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)