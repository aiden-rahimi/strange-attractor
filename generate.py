"""
strange-attractor — generative studies from the Lorenz system.
The equations chalked on my avatar's belly, rendered as art.

    dx/dt = sigma * (y - x)
    dy/dt = x * (rho - z) - y
    dz/dt = x * y - beta * z

Run:  python3 generate.py
Out:  hero.png, study-01..04.png, rotation.gif
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from scipy.integrate import solve_ivp

SIGMA, BETA = 10.0, 8.0 / 3.0
BG = "#060606"

PALETTES = {
    "phosphor": ["#0a2e1c", "#00cc66", "#d6ffe6"],
    "amber":    ["#3a1500", "#ff8c1a", "#ffe9c4"],
    "ice":      ["#0a1a3a", "#1a9fff", "#d9f2ff"],
    "violet":   ["#1c0a3a", "#9a4dff", "#f2e2ff"],
}


def lorenz(t, s, rho):
    x, y, z = s
    return [SIGMA * (y - x), x * (rho - z) - y, x * y - BETA * z]


def trajectory(rho, t_end=140.0, n=70000):
    t_eval = np.linspace(0, t_end, n)
    sol = solve_ivp(
        lorenz, (0, t_end), (1.0, 1.0, 1.0), args=(rho,),
        t_eval=t_eval, rtol=1e-9, atol=1e-12,
    )
    traj = sol.y.T
    return traj[int(n * 0.15):]  # drop transient


def render_2d(traj, palette, out, size=2400, dpi=200, lw=0.65):
    pts = traj[:, [0, 2]]  # x-z projection: the classic butterfly
    z = traj[:, 2]
    zn = (z - z.min()) / (z.max() - z.min())
    segs = np.stack([pts[:-1], pts[1:]], axis=1)
    cmap = LinearSegmentedColormap.from_list("p", PALETTES[palette])

    fig = plt.figure(figsize=(size / dpi, size / dpi), dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    ax.axis("off")

    # cheap bloom: wide faint pass under the crisp line
    ax.add_collection(LineCollection(
        segs[::4], colors=[cmap(0.45)], linewidths=lw * 5, alpha=0.05,
    ))
    lc = LineCollection(segs, cmap=cmap, norm=plt.Normalize(0, 1),
                        linewidths=lw, alpha=0.9)
    lc.set_array(zn)
    ax.add_collection(lc)

    ax.set_xlim(pts[:, 0].min(), pts[:, 0].max())
    ax.set_ylim(pts[:, 1].min(), pts[:, 1].max())
    ax.set_aspect("equal")
    fig.savefig(out, dpi=dpi, facecolor=BG, pil_kwargs={"optimize": True})
    plt.close(fig)
    print("wrote", out)


def render_rotation_gif(traj, palette, out, frames=48, size=900, dpi=100):
    cmap = LinearSegmentedColormap.from_list("p", PALETTES[palette])
    z = traj[:, 2]
    zn = (z - z.min()) / (z.max() - z.min())
    colors = cmap(zn)
    # thin the line for 3D speed
    xs, ys, zs = traj[::3, 0], traj[::3, 1], traj[::3, 2]
    cc = colors[::3]

    from PIL import Image
    imgs = []
    for i in range(frames):
        fig = plt.figure(figsize=(size / dpi, size / dpi), dpi=dpi, facecolor=BG)
        ax = fig.add_subplot(111, projection="3d", facecolor=BG)
        ax.set_axis_off()
        ax.view_init(elev=16, azim=i * 360.0 / frames)
        # segment-colored 3D line via scatter (fast enough thinned)
        ax.scatter(xs, ys, zs, c=cc, s=1.2, alpha=0.75, depthshade=True)
        lim = max(abs(xs).max(), abs(ys).max(), abs(zs).max())
        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(0, zs.max())
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        imgs.append(Image.fromarray(buf))
        plt.close(fig)
        print(f"frame {i + 1}/{frames}", end="\r")
    print()
    imgs[0].save(out, save_all=True, append_images=imgs[1:],
                 duration=90, loop=0, optimize=True)
    print("wrote", out)


STUDIES = [
    # (rho, palette, filename, caption)
    (20.0, "amber", "study-01-settling.png",
     "rho=20 — below the chaos threshold. The trajectory flirts with disorder, then spirals home to a fixed point."),
    (28.0, "phosphor", "study-02-classic.png",
     "rho=28 — the canonical strange attractor. Deterministic, bounded, never repeating."),
    (60.0, "ice", "study-03-tightening.png",
     "rho=60 — the wings tighten and the orbit hurries. Same equations, narrower weather."),
    (120.0, "violet", "study-04-wild.png",
     "rho=120 — far past polite chaos. The butterfly comes apart at the seams."),
]


def main():
    render_2d(trajectory(28.0, t_end=160.0), "phosphor", "hero.png",
              size=2800, lw=0.6)
    for rho, palette, fname, _ in STUDIES:
        render_2d(trajectory(rho), palette, fname)
    render_rotation_gif(trajectory(28.0, t_end=120.0, n=40000), "ice", "rotation.gif")
    with open("STUDIES.md", "w") as f:
        for rho, palette, fname, caption in STUDIES:
            f.write(f"## {fname}\n{caption}\n\n")
    print("done.")


if __name__ == "__main__":
    main()
