"""Shared figure theme for both repositories.

Palette slots and surfaces are taken from the validated reference palette
(adjacent-pair CVD dE >= 8, normal-vision dE >= 15 in both modes).
Every figure is rendered twice -- light and dark -- so the README can serve
the matching asset with <picture media="(prefers-color-scheme: ...)">.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LIGHT = dict(
    surface="#fcfcfb",
    text="#0b0b0b",
    muted="#52514e",
    faint="#8a8983",
    grid="#e3e2dd",
    panel="#f2f1ed",
    s1="#2a78d6", s2="#eb6834", s3="#1baf7a", s4="#eda100",
    s5="#e87ba4", s6="#008300", s7="#4a3aa7", s8="#e34948",
)

DARK = dict(
    surface="#1a1a19",
    text="#ffffff",
    muted="#c3c2b7",
    faint="#8a8983",
    grid="#333331",
    panel="#242423",
    s1="#3987e5", s2="#d95926", s3="#199e70", s4="#c98500",
    s5="#d55181", s6="#008300", s7="#9085e9", s8="#e66767",
)

MODES = [("light", LIGHT), ("dark", DARK)]


def apply(c):
    plt.rcParams.update({
        "figure.facecolor": c["surface"],
        "axes.facecolor": c["surface"],
        "savefig.facecolor": c["surface"],
        "text.color": c["text"],
        "axes.labelcolor": c["muted"],
        "axes.edgecolor": c["grid"],
        "xtick.color": c["muted"],
        "ytick.color": c["muted"],
        "grid.color": c["grid"],
        "font.family": "DejaVu Sans",
        "font.size": 10.5,
        "axes.titlesize": 13,
        "axes.titleweight": "600",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 200,
    })


def strip(ax, c, x=False, y=True):
    """Recessive grid on one axis only."""
    ax.set_axisbelow(True)
    ax.grid(axis="y" if y else "x", color=c["grid"], lw=0.8)
    if not x:
        ax.tick_params(axis="x", length=0)
    ax.tick_params(axis="y", length=0)


def save(fig, path, mode):
    fig.savefig(f"{path}-{mode}.png", bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
