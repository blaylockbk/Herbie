## Brian Blaylock
## May 6, 2022

"""
██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██

                █ ██
                █ ██ ┏━┓ ┏━┓            ┏━┓   ┏━┓
                █ ██ ┃ ┃ ┃ ┃┏━━━━┓┏━┓┏━┓┃ ┃   ┏━┓┏━━━━┓
                █ ██ ┃ ┗━┛ ┃┃ ━━ ┃┃ ┏━━┛┃ ┗━━┓┃ ┃┃ ━━ ┃
                █ ██ ┃ ┏━┓ ┃┃ ━━━┓┃ ┃   ┃ ━━ ┃┃ ┃┃ ━━━┓
                █ ██ ┗━┛ ┗━┛┗━━━━┛┗━┛   ┗━━━━┛┗━┛┗━━━━┛
                █ ██
                       🏁 Retrieve NWP Model Data 🏁

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


class ANSI:
    """
    Herbie colors as ansi codes

    Notes
    -----
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

    # Text Colors
    red = f"{ESC}[38;2;136;33;27m"
    blue = f"{ESC}[38;2;12;53;118m"
    black = f"{ESC}[38;2;0;0;0m"
    white = f"{ESC}[37m"
    orange = f"{ESC}[38;2;255;153;0m"
    green = f"{ESC}[38;2;41;130;13m"
    bright_green = f"{ESC}[92m"

    # Background color
    _tan = f"{ESC}[48;2;240;234;210m"
    _white = f"{ESC}[48;2;255;255;255m"

    herbie = f"{_white}{red}▌{reset}{blue}{_tan}▌{black}{bold}Herbie{reset}"

    ascii = f"""

{_tan}{' ':44}{reset}
{_tan}   {red}█ {blue}██ {black}                                    {reset}
{_tan}   {red}█ {blue}██ {black}┏━┓ ┏━┓            ┏━┓   ┏━┓        {reset}
{_tan}   {red}█ {blue}██ {black}┃ ┃ ┃ ┃┏━━━━┓┏━┓┏━┓┃ ┃   ┏━┓┏━━━━┓  {reset}
{_tan}   {red}█ {blue}██ {black}┃ ┗━┛ ┃┃ ━━ ┃┃ ┏━━┛┃ ┗━━┓┃ ┃┃ ━━ ┃  {reset}
{_tan}   {red}█ {blue}██ {black}┃ ┏━┓ ┃┃ ━━━┓┃ ┃   ┃ ━━ ┃┃ ┃┃ ━━━┓  {reset}
{_tan}   {red}█ {blue}██ {black}┗━┛ ┗━┛┗━━━━┛┗━┛   ┗━━━━┛┗━┛┗━━━━┛  {reset}
{_tan}   {red}█ {blue}██ {black}                                    {reset}
{_tan}{' ':3}{black}       🏁 Retrieve NWP Model Data 🏁     {reset}
{_tan}{' ':44}{reset}

    """


def rich_herbie():
    """
    Returns "▌▌Herbie" with rich colors (if rich is installed).
    """
    return f"[on {hc.tan}][{hc.red} on {hc.white}]▌[/][{hc.blue}]▌[/][bold {hc.black}]Herbie[/][/]"


def print_rich(H):
    """
    Print "rich" display console
    TODO: How do I get the __repr__ to do this?

    eh, just use my own ANSI class for text coloring.
    """
    try:
        from rich.console import Console

        from herbie.misc import rich_herbie

        console = Console()
        console.print(
            f"{rich_herbie()} "
            f"{H.model.upper()} model "
            f"[italic]{H.product}[/] product "
            f"initialized [green bold]{H.date:%Y-%b-%d %H:%M} UTC[/] "
            f"[rgb(41, 130, 13)]F{H.fxx:02d}[/] "
            f"┊ [#ff9900 italic]source={H.grib_source}[/]"
        )
    except:
        print("rich is not working/installed")


########################################################################


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
