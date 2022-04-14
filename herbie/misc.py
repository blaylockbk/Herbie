## Brian Blaylock
## May 13, 2021

"""
┏━┓ ┏━┓               ┏━┓    ┏━┓
┃ ┃ ┃ ┃ ┏━━━━┓ ┏━┓┏━┓ ┃ ┃    ┏━┓ ┏━━━━┓
┃ ┗━┛ ┃ ┃ ━━ ┃ ┃ ┏━━┛ ┃ ┗━━┓ ┃ ┃ ┃ ━━ ┃
┃ ┏━┓ ┃ ┃ ━━━┓ ┃ ┃    ┃ ━━ ┃ ┃ ┃ ┃ ━━━┓
┗━┛ ┗━┛ ┗━━━━┛ ┗━┛    ┗━━━━┛ ┗━┛ ┗━━━━┛

    🏁 Retrieve NWP Model Data 🏁

██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
"""


def Herbie_ascii(body="tan"):
    """
    Display the Herbie logo in ASCII characters and colors.

    Usage
    -----
    Command Line
    >>> python -c "from herbie.misc import Herbie_ascii; print(Herbie_ascii())"
    """
    red = "\033[38;2;136;33;27m"
    blue = "\033[38;2;12;53;118m"
    body = "\033[38;2;0;0;0m"
    escape = "\033[0m"
    background = "\033[48;2;240;234;210m"
    a = f"""

{background}{' ':45}{escape}
{background}   {red}█ {blue}██  {body}                                    {escape}
{background}   {red}█ {blue}██  {body}┏━┓ ┏━┓            ┏━┓   ┏━┓        {escape}
{background}   {red}█ {blue}██  {body}┃ ┃ ┃ ┃┏━━━━┓┏━┓┏━┓┃ ┃   ┏━┓┏━━━━┓  {escape}
{background}   {red}█ {blue}██  {body}┃ ┗━┛ ┃┃ ━━ ┃┃ ┏━━┛┃ ┗━━┓┃ ┃┃ ━━ ┃  {escape}
{background}   {red}█ {blue}██  {body}┃ ┏━┓ ┃┃ ━━━┓┃ ┃   ┃ ━━ ┃┃ ┃┃ ━━━┓  {escape}
{background}   {red}█ {blue}██  {body}┗━┛ ┗━┛┗━━━━┛┗━┛   ┗━━━━┛┗━┛┗━━━━┛  {escape}
{background}   {red}█ {blue}██  {body}                                    {escape}
{background}{' ':4}{body}       🏁 Retrieve NWP Model Data 🏁     {escape}
{background}{' ':45}{escape}

    """
    return a


def HerbieColors():
    return dict(
        body="#f0ead2",
        red="#88211b",
        blue="#0c3576",
        white="#ffffff",
        black="#000000",
    )


def HerbieLogo(white_line=False):
    """Logo of Herbie The Love Bug"""
    import matplotlib.patheffects as path_effects
    import matplotlib.pyplot as plt

    colors = HerbieColors()

    plt.figure(figsize=[5, 5], facecolor=colors["body"])

    plt.axis([-10, 10, -10, 10])
    if white_line:
        plt.axvline(4, lw=40, color=colors["white"])
    plt.axvline(2.5, lw=20, color=colors["red"])
    plt.axvline(5.5, lw=40, color=colors["blue"])

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

    plt.gca().set_facecolor(colors["body"])
    plt.gca().margins(0)

    plt.gca().get_xaxis().set_visible(False)
    plt.gca().get_yaxis().set_visible(False)

    plt.gca().spines["bottom"].set_visible(False)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["left"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    return plt.gca()


def HerbieLogo2(white_line=False, text_color="body", text_stroke="black"):
    """Logo of Herbie The Love Bug"""
    import matplotlib.patheffects as path_effects
    import matplotlib.pyplot as plt

    colors = HerbieColors()

    plt.figure(figsize=[5, 3], facecolor=colors["body"])

    plt.axis([1.5, 20, -10, 10])

    if white_line:
        plt.axvline(4, lw=40, color=colors["white"])
    plt.axvline(2.5, lw=20, color=colors["red"])
    plt.axvline(5.5, lw=40, color=colors["blue"])

    if text_color in colors:
        text_color = colors[text_color]
    if text_stroke in colors:
        text_stroke = colors[text_stroke]

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

    plt.gca().set_facecolor(colors["body"])
    plt.gca().margins(0)

    plt.gca().get_xaxis().set_visible(False)
    plt.gca().get_yaxis().set_visible(False)

    plt.gca().spines["bottom"].set_visible(False)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["left"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    return plt.gca()
