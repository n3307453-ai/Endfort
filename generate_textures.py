#!/usr/bin/env python3
"""Generuje proceduralne tekstury (Saturn, czarna dziura, Droga Mleczna)
i pakuje je do resource packa wbudowanego w moda.

Uzycie:  python3 generate_textures.py
Wymaga:  pip install pillow numpy
"""
import io, json, zipfile, pathlib
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
OUT_ZIP = ROOT / "cosmic_sky_pack.zip"
SS = 2          # supersampling (antyaliasing)
rng = np.random.default_rng(2603)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def grid(n):
    n2 = n * SS
    a = (np.arange(n2) + 0.5) / n2 * 2 - 1
    x, y = np.meshgrid(a, -a)          # y w gore
    return x, y


def down(rgba):
    n = rgba.shape[0] // SS
    # alpha-weighted downsample
    a = rgba[..., 3:4]
    prem = rgba[..., :3] * a
    prem = prem.reshape(n, SS, n, SS, 3).mean((1, 3))
    a = a.reshape(n, SS, n, SS, 1).mean((1, 3))
    rgb = np.where(a > 1e-4, prem / np.maximum(a, 1e-4), 0)
    out = np.concatenate([rgb, a], -1)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")


def over(dst, rgb, a):
    """alpha-over: kladzie (rgb,a) na dst (premultiplied-free)."""
    da = dst[..., 3:4]
    oa = a + da * (1 - a)
    orgb = np.where(oa > 1e-5, (rgb * a + dst[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-5), 0)
    return np.concatenate([orgb, oa], -1)


def rot(x, y, deg):
    t = np.radians(deg)
    return x * np.cos(t) + y * np.sin(t), -x * np.sin(t) + y * np.cos(t)


# ---------------------------------------------------------------- SATURN
def saturn(n=256):
    x, y = grid(n)
    img = np.zeros(x.shape + (4,))
    R = 0.50
    xr, yr = rot(x, y, 22)
    d = np.sqrt(xr ** 2 + (yr / 0.28) ** 2)
    # pierscienie: C, B, przerwa Cassiniego, A, wasky pas F
    prof = (smooth(0.66, 0.70, d) * (1 - smooth(0.99, 1.00, d)))
    band = 0.75 + 0.25 * np.sin(d * 140) * np.sin(d * 37 + 1)
    cassini = 1 - 0.95 * (smooth(0.855, 0.865, d) * (1 - smooth(0.885, 0.895, d)))
    inner_c = 0.45 + 0.55 * smooth(0.70, 0.80, d)
    ring_a = prof * cassini * inner_c * np.clip(band, 0, 1) * 0.95
    ring_rgb = np.stack([0.86 * band, 0.78 * band, 0.62 * band], -1)
    ring_rgb = np.clip(ring_rgb, 0, 1)

    r = np.sqrt(x ** 2 + y ** 2)
    pmask = 1 - smooth(R - 0.012, R + 0.004, r)
    # kula + pasy
    z = np.sqrt(np.clip(1 - (r / R) ** 2, 0, 1))
    lx, ly, lz = -0.55, 0.55, 0.63
    lam = np.clip((x / R) * lx + (y / R) * ly + z * lz, 0, 1)
    lat = y / R
    bands = (0.5 + 0.5 * np.sin(lat * 18 + 0.8 * np.sin(lat * 5))) * 0.55 + \
            (0.5 + 0.5 * np.sin(lat * 41)) * 0.25
    base = np.array([0.93, 0.80, 0.55])
    dark = np.array([0.70, 0.55, 0.34])
    col = dark + (base - dark) * bands[..., None]
    col = col * (0.18 + 0.95 * lam[..., None] ** 0.85)
    # cien pierscieni na planecie (pas wokol rownika)
    shadow = 1 - 0.55 * np.exp(-((yr + 0.10) / 0.07) ** 2) * (yr < 0.02)
    col *= shadow[..., None]
    planet_rgb = np.clip(col, 0, 1)

    # tylna polowa pierscieni (za planeta)
    back = (yr > 0)       # yr>0 = dalsza strona (po obrocie)
    front = ~back
    img = over(img, ring_rgb, (ring_a * back)[..., None])
    img = over(img, planet_rgb, pmask[..., None])
    img = over(img, ring_rgb, (ring_a * front)[..., None])
    # delikatna poswiata
    glow = np.exp(-np.maximum(r - R, 0) / 0.05) * 0.12 * (1 - pmask)
    img = over(img, np.broadcast_to(np.array([1, .9, .6]), img[..., :3].shape), glow[..., None])
    return down(img)


# ------------------------------------------------------------ CZARNA DZIURA
def blackhole(n=256):
    x, y = grid(n)
    img = np.zeros(x.shape + (4,))
    r = np.sqrt(x ** 2 + y ** 2)
    th = np.arctan2(y, x)
    RH = 0.30
    xr, yr = rot(x, y, -14)

    def heat(t):            # t 0 (zewnatrz) -> 1 (wewnatrz)
        t = np.clip(t, 0, 1)[..., None]
        c0 = np.array([0.55, 0.10, 0.02])
        c1 = np.array([1.00, 0.55, 0.12])
        c2 = np.array([1.00, 0.95, 0.80])
        return np.where(t < 0.5, c0 + (c1 - c0) * (t * 2), c1 + (c2 - c1) * ((t - 0.5) * 2))

    # dysk akrecyjny (elipsa)
    d = np.sqrt(xr ** 2 + (yr / 0.20) ** 2)
    disk_prof = smooth(0.36, 0.42, d) * (1 - smooth(0.80, 1.00, d))
    t = np.clip(1 - (d - 0.36) / 0.64, 0, 1)
    doppler = 0.65 + 0.35 * np.clip(-xr / 0.9 + 0.5, 0, 1)
    swirl = 0.85 + 0.15 * np.sin(d * 90 + th * 3)
    disk_rgb = heat(t ** 1.2) * (doppler * swirl)[..., None]
    disk_a = np.clip(disk_prof * (0.35 + 0.65 * t ** 1.4) * doppler * 1.3, 0, 1)

    # tylna polowa dysku "zagieta" nad i pod cieniem (soczewkowanie)
    halo = np.exp(-np.maximum(r - RH, 0) / 0.055) * (0.55 + 0.45 * np.abs(np.sin(th + np.radians(-14))))
    halo *= (1 - smooth(RH - 0.004, RH + 0.004, -r + 2 * RH))   # tylko r>RH
    halo_rgb = heat(0.55 + 0.45 * np.exp(-np.maximum(r - RH, 0) / 0.04))
    lens_a = np.clip(halo * 1.1, 0, 1)

    # pierscien fotonowy
    ring = np.exp(-((r - (RH + 0.012)) / 0.012) ** 2)
    ring_rgb = np.broadcast_to(np.array([1, 0.97, 0.88]), img[..., :3].shape)

    back = (yr > 0)
    front = ~back
    outside = (r > RH)
    img = over(img, disk_rgb, (disk_a * back * outside)[..., None])
    img = over(img, halo_rgb, lens_a[..., None] * 0.9)
    # cien (czarny, nieprzezroczysty)
    shadow = 1 - smooth(RH - 0.006, RH + 0.002, r)
    img = over(img, np.zeros_like(disk_rgb), shadow[..., None])
    img = over(img, ring_rgb, np.clip(ring, 0, 1)[..., None] * 0.95)
    # przednia czesc dysku przechodzi przed cieniem
    img = over(img, disk_rgb, (disk_a * front)[..., None])
    # zewnetrzna poswiata
    g = np.exp(-np.maximum(r - 0.4, 0) / 0.12) * 0.10
    img = over(img, np.broadcast_to(np.array([1, .6, .25]), img[..., :3].shape), g[..., None] * (img[..., 3:4] < 0.01))
    return down(img)


# ------------------------------------------------------------ DROGA MLECZNA
def periodic_noise(n, beta, seed):
    g = np.random.default_rng(seed)
    f = np.fft.fft2(g.standard_normal((n, n)))
    fx = np.fft.fftfreq(n)[:, None]
    fy = np.fft.fftfreq(n)[None, :]
    k = np.sqrt(fx ** 2 + fy ** 2)
    k[0, 0] = 1
    f *= 1 / k ** beta
    f[0, 0] = 0
    out = np.real(np.fft.ifft2(f))
    out = (out - out.min()) / (out.max() - out.min())
    return out


def milky_way(n=512):
    """Teksturka kafelkowana (vanilla powtarza end_sky.png wielokrotnie na scianie)."""
    u = (np.arange(n) / n)[None, :].repeat(n, 0)
    v = (np.arange(n) / n)[:, None].repeat(n, 1)
    # pas galaktyczny: jedno pasmo na kafelek, na skos (okresowe)
    ph = 2 * np.pi * (u + v)
    warp = 0.06 * periodic_noise(n, 1.2, 1)
    dist = np.abs(np.sin(ph / 2 + warp * 6))            # 0 w osi pasa
    band = np.exp(-(dist / 0.30) ** 2)
    core = np.exp(-(dist / 0.10) ** 2)
    clouds = periodic_noise(n, 1.9, 2)
    fine = periodic_noise(n, 1.2, 3)
    dust = periodic_noise(n, 2.2, 4)
    glow = band * (0.35 + 0.9 * clouds) + core * (0.4 + 0.6 * fine)
    lanes = smooth(0.55, 0.75, dust) * band * 0.85      # ciemne pasy pylu
    glow = np.clip(glow * (1 - lanes), 0, 1.4)

    cool = np.array([0.45, 0.55, 1.00])
    warm = np.array([1.00, 0.82, 0.62])
    mix = np.clip(core + 0.3 * clouds, 0, 1)[..., None]
    nebula = (cool * (1 - mix) + warm * mix) * glow[..., None]
    base = np.array([0.03, 0.02, 0.07])
    img = base + nebula * 0.95

    # gwiazdy: gestsze w pasie
    stars = np.zeros((n, n))
    count = int(n * n * 0.010)
    xs = rng.integers(0, n, count); ys = rng.integers(0, n, count)
    prob = 0.25 + 0.75 * band[ys, xs]
    keep = rng.random(count) < prob
    xs, ys = xs[keep], ys[keep]
    mag = rng.random(len(xs)) ** 3
    for dx, dy, w in [(0, 0, 1.0), (1, 0, .35), (-1, 0, .35), (0, 1, .35), (0, -1, .35)]:
        np.add.at(stars, ((ys + dy) % n, (xs + dx) % n), (0.35 + 0.65 * mag) * w)
    tint = np.array([1.0, 0.97, 0.95])
    img = img + np.clip(stars, 0, 1)[..., None] * tint
    img = np.clip(img, 0, 1)
    # vanilla mnozy end_sky przez ~0.16 -> podbijamy kontrast
    img = img ** 0.8
    arr = (img * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


# ----------------------------------------------------------------- PACK
def png(img):
    b = io.BytesIO(); img.save(b, "PNG", optimize=True); return b.getvalue()


def main():
    sat = saturn(256)
    bh = blackhole(256)
    mw = milky_way(512)

    # moon_phases.png = siatka 4x2 (stary format, kafelek 128x128)
    sheet = Image.new("RGBA", (512, 256))
    bh128 = bh.resize((128, 128), Image.LANCZOS)
    for i in range(8):
        sheet.paste(bh128, ((i % 4) * 128, (i // 4) * 128))

    mcmeta = {"pack": {
        "description": "Cosmic Sky: Saturn (dzien), czarna dziura (noc), Droga Mleczna (End)",
        # szeroki zakres formatow, zeby pack byl widoczny w 26.x
        "min_format": 75, "max_format": 999,
        "pack_format": 75,
    }}
    files = {
        "pack.mcmeta": json.dumps(mcmeta, indent=2).encode(),
        "pack.png": png(sat.resize((64, 64), Image.LANCZOS)),
        "assets/minecraft/textures/environment/sun.png": png(sat),
        "assets/minecraft/textures/environment/moon_phases.png": png(sheet),
        "assets/minecraft/textures/environment/end_sky.png": png(mw),
        # nowszy uklad sciezek (1.21.11+ / 26.x) - zapasowo
        "assets/minecraft/textures/environment/celestial/sun.png": png(sat),
    }
    for name in ["full_moon", "waning_gibbous", "third_quarter", "waning_crescent",
                 "new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous"]:
        files[f"assets/minecraft/textures/environment/celestial/moon/{name}.png"] = png(bh128)

    OUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in files.items():
            z.writestr(zipfile.ZipInfo(k, (2026, 1, 1, 0, 0, 0)), v, zipfile.ZIP_DEFLATED)
    # podglad do debugowania
    prev = ROOT
    bg = Image.new("RGBA", (256 * 3, 256), (8, 8, 20, 255))
    for i, im in enumerate([sat, bh, mw.resize((256, 256))]):
        bg.alpha_composite(im, (i * 256, 0))
    bg.save(prev / "preview.png")
    print("OK ->", OUT_ZIP)


if __name__ == "__main__":
    main()
