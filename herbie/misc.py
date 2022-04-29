## Brian Blaylock
## May 13, 2021

"""
██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██

                █ ██
                █ ██ ┏━┓ ┏━┓            ┏━┓   ┏━┓
                █ ██ ┃ ┃ ┃ ┃┏━━━━┓┏━┓┏━┓┃ ┃   ┏━┓┏━━━━┓
                █ ██ ┃ ┗━┛ ┃┃ ━━ ┃┃ ┏━━┛┃ ┗━━┓┃ ┃┃ ━━ ┃
                █ ██ ┃ ┏━┓ ┃┃ ━━━┓┃ ┃   ┃ ━━ ┃┃ ┃┃ ━━━┓
                █ ██ ┗━┛ ┗━┛┗━━━━┛┗━┛   ┗━━━━┛┗━┛┗━━━━┛
                █ ██
                        Retrieve NWP Model Data 🏎🏁

██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
"""


class hc:
    """Herbie Color Pallette"""

    tan = "#f0ead2"
    red = "#88211b"
    blue = "#0c3576"
    white = "#ffffff"
    black = "#000000"


class ansi:
    """
    Herbie colors as ansi codes

    Reference
    ---------
    https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
    """

    # Octal: \033
    # Unicode: \u001b
    # Hexadecimal: \x1B
    ESC = "\x1B"
    # Style
    bold = f"{ESC}[1m"
    italic = f"{ESC}[3m"
    underline = f"{ESC}[4m"
    strikethrough = f"{ESC}[9m"
    reset = f"{ESC}[0m"
    # Colors
    red = f"{ESC}[38;2;136;33;27m"
    blue = f"{ESC}[38;2;12;53;118m"
    black = f"{ESC}[38;2;0;0;0m"
    white = f"{ESC}[37m"
    # Background color
    _tan = f"{ESC}[48;2;240;234;210m"
    _white = f"{ESC}[47m"


def rich_herbie():
    """
    Returns "▌▌Herbie" with rich colors
    """
    return f"[on {hc.tan}][{hc.red} on {hc.white}]▌[/][{hc.blue}]▌[/][bold {hc.black}]Herbie[/]"


def Herbie_ascii(body="tan"):
    """
    Display the Herbie logo in ASCII characters and colors.

    Usage
    -----
    Command Line
    >>> python -c "from herbie.misc import Herbie_ascii; print(Herbie_ascii())"
    """
    a = f"""

{ansi._tan}{' ':44}{ansi.reset}
{ansi._tan}   {ansi.red}█ {ansi.blue}██ {ansi.black}                                    {ansi.reset}
{ansi._tan}   {ansi.red}█ {ansi.blue}██ {ansi.black}┏━┓ ┏━┓            ┏━┓   ┏━┓        {ansi.reset}
{ansi._tan}   {ansi.red}█ {ansi.blue}██ {ansi.black}┃ ┃ ┃ ┃┏━━━━┓┏━┓┏━┓┃ ┃   ┏━┓┏━━━━┓  {ansi.reset}
{ansi._tan}   {ansi.red}█ {ansi.blue}██ {ansi.black}┃ ┗━┛ ┃┃ ━━ ┃┃ ┏━━┛┃ ┗━━┓┃ ┃┃ ━━ ┃  {ansi.reset}
{ansi._tan}   {ansi.red}█ {ansi.blue}██ {ansi.black}┃ ┏━┓ ┃┃ ━━━┓┃ ┃   ┃ ━━ ┃┃ ┃┃ ━━━┓  {ansi.reset}
{ansi._tan}   {ansi.red}█ {ansi.blue}██ {ansi.black}┗━┛ ┗━┛┗━━━━┛┗━┛   ┗━━━━┛┗━┛┗━━━━┛  {ansi.reset}
{ansi._tan}   {ansi.red}█ {ansi.blue}██ {ansi.black}                                    {ansi.reset}
{ansi._tan}{' ':3}{ansi.black}       🏁 Retrieve NWP Model Data 🏁     {ansi.reset}
{ansi._tan}{' ':44}{ansi.reset}

    """
    return a


def HerbieLogo(white_line=False):
    """Logo of Herbie The Love Bug"""
    import matplotlib.patheffects as path_effects
    import matplotlib.pyplot as plt

    plt.figure(figsize=[5, 5], facecolor=hc.tan)

    plt.axis([-10, 10, -10, 10])
    if white_line:
        plt.axvline(4, lw=40, color=hc.white)
    plt.axvline(2.5, lw=20, color=hc.red)
    plt.axvline(5.5, lw=40, color=hc.blue)

    c = plt.Circle((0, 0), radius=6, ec="k", fc="w", zorder=10, linewidth=3)
    plt.gca().add_artist(c)

    plt.text(
        0,
        0,
        "53",
        fontsize=110,
        fontweight="bold",
        va="center_baseline",
        ha="center",
        zorder=11,
    )

    plt.gca().set_facecolor(hc.tan)
    plt.gca().margins(0)

    plt.gca().get_xaxis().set_visible(False)
    plt.gca().get_yaxis().set_visible(False)

    plt.gca().spines["bottom"].set_visible(False)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["left"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    return plt.gca()


def HerbieLogo2(white_line=False, text_color="tan", text_stroke="black"):
    """
    Herbie logo (main)

    >>> ax = HerbieLogo2()
    >>> plt.savefig('Herbie.svg', bbox_inches="tight")

    >>> ax = HerbieLogo2()
    >>> plt.savefig('Herbie_transparent.svg', bbox_inches="tight", transparent=True)

    >>> ax = HerbieLogo2(text_color='tan')
    >>> plt.savefig('Herbie_transparent_tan.svg', bbox_inches="tight", transparent=True)
    """
    import matplotlib.patheffects as path_effects
    import matplotlib.pyplot as plt

    plt.figure(figsize=[5, 3], facecolor=hc.tan)

    plt.axis([1.5, 20, -10, 10])

    if white_line:
        plt.axvline(4, lw=40, color=hc.white)
    plt.axvline(2.5, lw=20, color=hc.red)
    plt.axvline(5.5, lw=40, color=hc.blue)

    if hasattr(hc, text_color):
        text_color = getattr(hc, text_color)
    if hasattr(hc, text_stroke):
        text_stroke = getattr(hc, text_stroke)

    text = plt.text(
        8,
        0,
        "Herbie",
        fontsize=110,
        fontweight="bold",
        color=text_color,
        va="center_baseline",
        ha="left",
        zorder=11,
    )

    if text_stroke is not None:
        text.set_path_effects(
            [
                path_effects.Stroke(linewidth=3, foreground=text_stroke),
                path_effects.Normal(),
            ]
        )

    plt.gca().set_facecolor(hc.tan)
    plt.gca().margins(0)

    plt.gca().get_xaxis().set_visible(False)
    plt.gca().get_yaxis().set_visible(False)

    plt.gca().spines["bottom"].set_visible(False)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["left"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    return plt.gca()
