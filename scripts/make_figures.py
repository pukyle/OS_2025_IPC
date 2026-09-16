"""Regenerate docs/figures/ — run from the repository root.

    python3 scripts/make_figures.py

Schematic figures drawn from the implementation in sender.c / receiver.c.
Each is rendered light and dark so the README can serve the matching asset
with <picture media="(prefers-color-scheme: ...)">.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from theme import MODES, apply, save

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "figures")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, fc, txt="", fg="#ffffff", fs=10, weight="600", r=0.10):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=fc, edgecolor="none"))
    if txt:
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center",
                color=fg, fontsize=fs, weight=weight, linespacing=1.45)


# ------------------------------------------------------------------ figure 1
def fig_datapath(c, mode):
    """Why shared memory wins: count the copies."""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.3))

    for ax, (title, sub, col, stages, ncopy) in zip(axes, [
        ("Message passing", "msgsnd / msgrcv", c["s2"],
         [("sender\nuser buffer", c["panel"]),
          ("kernel\nmessage queue", c["s2"]),
          ("receiver\nuser buffer", c["panel"])], 2),
        ("Shared memory", "shmat, then a plain store", c["s3"],
         [("sender\naddress space", c["panel"]),
          ("one physical page\nmapped into both", c["s3"]),
          ("receiver\naddress space", c["panel"])], 0),
    ]):
        ax.set_xlim(0, 10); ax.set_ylim(-2.4, 7.0); ax.axis("off")
        ax.text(0, 6.35, title, color=c["text"], fontsize=12.5, weight="600")
        ax.text(0, 5.85, sub, color=c["faint"], fontsize=9.6, family="monospace")

        ys = [4.1, 2.25, 0.4]
        for (label, fc), y in zip(stages, ys):
            fg = "#ffffff" if fc is not c["panel"] else c["muted"]
            box(ax, 1.4, y, 7.2, 1.35, fc, label, fg=fg, fs=10.2)

        for i in range(2):
            kind = "copy_to/from_user" if ncopy else "same page, no copy"
            if ncopy:
                ax.add_patch(FancyArrowPatch((5.0, ys[i] - 0.06), (5.0, ys[i + 1] + 1.41),
                                             arrowstyle="-|>", mutation_scale=13,
                                             color=col, lw=1.8))
            else:
                ax.plot([5.0, 5.0], [ys[i] - 0.06, ys[i + 1] + 1.41],
                        color=c["faint"], lw=1.1, ls=":")
            ax.text(5.25, (ys[i] + ys[i + 1] + 1.35) / 2, kind,
                    color=col if ncopy else c["faint"], fontsize=9,
                    va="center", ha="left", family="monospace")

        ax.text(0, -0.75, f"{ncopy} kernel copies per message",
                color=col, fontsize=13, weight="700")
        ax.text(0, -1.5,
                ("Every message crosses the user/kernel\nboundary twice and is "
                 "buffered in kernel memory."
                 if ncopy else
                 "The page is in both address spaces, so\na write by one is already "
                 "visible to the other."),
                color=c["muted"], fontsize=9.5, va="top", linespacing=1.5)

    fig.suptitle("The two mechanisms differ in exactly one thing: how many times "
                 "the payload is copied",
                 x=0.012, ha="left", color=c["text"], fontsize=13, weight="600")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, os.path.join(OUT, "fig1-datapath"), mode)


# ------------------------------------------------------------------ figure 2
def fig_handshake(c, mode):
    """The two-semaphore alternation implemented in sender.c / receiver.c."""
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.set_xlim(-1.9, 13.2); ax.set_ylim(-2.3, 6.4); ax.axis("off")

    lanes = [("sender", 3.0, c["s1"]), ("receiver", 1.2, c["s2"])]
    for name, y, col in lanes:
        ax.plot([0, 12.6], [y + 0.4, y + 0.4], color=c["grid"], lw=1.1, zorder=0)
        ax.text(-1.85, y + 0.4, name, color=col, fontsize=11,
                weight="600", va="center", ha="left")

    # running / blocked segments, (lane_index, x0, x1, running)
    segs = [
        (0, 0.0, 2.6, True), (0, 2.6, 6.2, False), (0, 6.2, 8.8, True),
        (0, 8.8, 12.4, False),
        (1, 0.0, 2.6, False), (1, 2.6, 6.2, True), (1, 6.2, 8.8, False),
        (1, 8.8, 12.4, True),
    ]
    for li, x0, x1, running in segs:
        _, y, col = lanes[li]
        if running:
            box(ax, x0 + 0.06, y, x1 - x0 - 0.12, 0.8, col, "running", fs=9.4)
        else:
            ax.add_patch(Rectangle((x0 + 0.06, y + 0.26), x1 - x0 - 0.12, 0.28,
                                   facecolor=c["panel"], edgecolor="none"))
            ax.text((x0 + x1) / 2, y + 0.4, "blocked", ha="center", va="center",
                    color=c["faint"], fontsize=9.2)

    calls = [
        (2.6, "sem_post(receiver_sem)\nsem_wait(sender_sem)", c["s1"]),
        (6.2, "sem_post(sender_sem)\nsem_wait(receiver_sem)", c["s2"]),
        (8.8, None, c["s1"]),
    ]
    for x, txt, col in calls:
        ax.plot([x, x], [0.95, 4.05], color=col, lw=1.2, ls=":", zorder=0)
        if txt:
            ax.text(x, 4.2, txt, ha="center", va="bottom", color=col,
                    fontsize=8.6, family="monospace", linespacing=1.6)

    ax.annotate("", xy=(6.2, 0.75), xytext=(2.6, 0.75),
                arrowprops=dict(arrowstyle="<->", color=c["faint"], lw=1.2))
    ax.text(4.4, 0.45, "one message", ha="center", color=c["faint"], fontsize=9)

    ax.text(-1.9, -0.75,
            "Initial values: sender_sem = 1, receiver_sem = 0. The asymmetry is what "
            "starts the cycle, and it is\nalso the failure mode the lab warns about — "
            "initialise both to 0 and neither side ever runs.",
            color=c["muted"], fontsize=9.6, va="top", linespacing=1.55)
    ax.text(-1.9, -1.85,
            "Only the shaded band is timed: clock_gettime() brackets the msgsnd/msgrcv "
            "call or the strcpy, never the wait.",
            color=c["faint"], fontsize=9.4, va="top")
    ax.text(-1.9, 6.05, "Strict alternation enforced by two POSIX semaphores",
            color=c["text"], fontsize=12.5, weight="600")
    save(fig, os.path.join(OUT, "fig2-handshake"), mode)


for mode, c in MODES:
    apply(c)
    fig_datapath(c, mode)
    fig_handshake(c, mode)
print("figures written to", OUT)
