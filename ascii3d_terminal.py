#!/usr/bin/env python3
"""
3D 아스키 터미널 애니메이션
이미지를 말랑한 입체로 부풀려서, 색 있는 아스키 글자로 터미널 안에서 빙글빙글 돌립니다.

사용법
  python3 ascii3d_terminal.py               # 내장된 토끼
  python3 ascii3d_terminal.py 내사진.png     # 다른 이미지 (투명 배경 PNG가 가장 깔끔)
  python3 ascii3d_terminal.py --once        # 한 프레임만 찍고 끝내기 (복사·붙여넣기용)
  python3 ascii3d_terminal.py --help        # 옵션 전체 보기

필요한 것: Python 3.8+, numpy, pillow   →   pip install numpy pillow

조작 (실행 중)
  ← → ↑ ↓ / WASD  돌리기        + / -   확대·축소
  space            자동 회전 켜기/끄기
  c                색 바꾸기 (원본 컬러 → 흑백 → 매트릭스 → 앰버)
  g                글자셋 바꾸기 (클래식 → 디테일 → 블록 → 점자 → 바이너리)
  v / V            볼륨 줄이기 / 키우기
  e                윤곽선 켜기/끄기
  q                종료
"""
import argparse
import base64
import io
import os
import shutil
import sys
import time

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("numpy와 pillow가 필요해요:  pip install numpy pillow")

RAMPS = {
    "classic": " .:-=+*#%@",
    "detail": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "block": " ░▒▓█",
    "dots": " ⠁⠃⠇⡇⣇⣧⣷⣿",
    "binary": " .10",
}
RAMP_ORDER = ["classic", "detail", "block", "dots", "binary"]
MODES = ["color", "mono", "matrix", "amber"]
MODE_KO = {"color": "원본 컬러", "mono": "흑백", "matrix": "매트릭스", "amber": "앰버"}
RAMP_KO = {"classic": "클래식", "detail": "디테일", "block": "블록", "dots": "점자", "binary": "바이너리"}
LW = np.array([0.299, 0.587, 0.114], np.float32)
PERSP = 4.0
SS = 2

BUNNY_WEBP = """
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
"""


# ----------------------------------------------------------------------------
# image -> mask + texture
# ----------------------------------------------------------------------------
def load_rgba(path=None, max_side=420):
    if path:
        im = Image.open(path)
    else:
        try:
            im = Image.open(io.BytesIO(base64.b64decode("".join(BUNNY_WEBP.split()))))
        except Exception:
            sys.exit("내장 이미지를 열지 못했어요. pillow를 최신으로 올려 주세요:  pip install -U pillow")
    im = im.convert("RGBA")
    s = max_side / max(im.size)
    if s < 1:
        im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    elif max(im.size) < 240:
        s = 240 / max(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return np.asarray(im).copy()


def _shift(a, dy, dx, fill=0):
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    ys, yd = slice(max(dy, 0), h + min(dy, 0)), slice(max(-dy, 0), h + min(-dy, 0))
    xs, xd = slice(max(dx, 0), w + min(dx, 0)), slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def compute_mask(rgba, tol=48):
    alpha = rgba[..., 3]
    if (alpha < 128).mean() > 0.005:
        return alpha >= 128
    rgb = rgba[..., :3].astype(np.int32)
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    ref = np.median(border, axis=0)
    near = ((rgb - ref) ** 2).sum(-1) <= tol * tol
    bg = np.zeros_like(near)
    bg[0], bg[-1], bg[:, 0], bg[:, -1] = near[0], near[-1], near[:, 0], near[:, -1]
    while True:
        grown = bg | (near & (_shift(bg, 1, 0) | _shift(bg, -1, 0) | _shift(bg, 0, 1) | _shift(bg, 0, -1)))
        if (grown == bg).all():
            break
        bg = grown
    mask = ~bg
    if mask.mean() < 0.01 or mask.mean() > 0.985:
        mask[:] = True
    return mask


def _distance_inside(mask):
    """8-neighbour chamfer distance to the outside (pixels)."""
    h, w = mask.shape
    d = np.where(mask, 1e9, 0.0)
    d = np.pad(d, 1)  # image border counts as outside
    r2 = 2 ** 0.5
    for _ in range(2):
        for y in range(1, h + 1):
            row = np.minimum(d[y], d[y - 1] + 1)
            row[1:] = np.minimum(row[1:], d[y - 1, :-1] + r2)
            row[:-1] = np.minimum(row[:-1], d[y - 1, 1:] + r2)
            d[y] = row
        for y in range(h, 0, -1):
            row = np.minimum(d[y], d[y + 1] + 1)
            row[1:] = np.minimum(row[1:], d[y + 1, :-1] + r2)
            row[:-1] = np.minimum(row[:-1], d[y + 1, 1:] + r2)
            d[y] = row
        for x in range(1, w + 1):
            d[:, x] = np.minimum(d[:, x], d[:, x - 1] + 1)
        for x in range(w, 0, -1):
            d[:, x] = np.minimum(d[:, x], d[:, x + 1] + 1)
    return d[1:-1, 1:-1]


def _nearest_fill(valid, values):
    out = values.copy()
    done = valid.copy()
    front = valid.copy()
    while not done.all() and front.any():
        new = np.zeros_like(done)
        newv = np.zeros_like(out)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            src = _shift(front, dy, dx, False)
            sv = _shift(out, dy, dx, 0)
            take = src & ~done & ~new
            newv[take] = sv[take]
            new |= take
        out[new] = newv[new]
        done |= new
        front = new
    return out


def prepare_texture(rgba, mask):
    rgb = rgba[..., :3].astype(np.float32) / 255.0
    ink = mask & ((rgb @ LW) < 0.36)
    D = _distance_inside(mask)
    t_out = 0
    for d in range(1, 30):
        sel = mask & (np.abs(D - d) < 0.5)
        if not sel.any():
            break
        if ink[sel].mean() >= 0.5:
            t_out = d
        else:
            break
    if t_out:
        t_out += 1
    src = mask & ~ink & (D > 1.5)
    if src.sum() < 10:
        src, t_out = mask.copy(), 0
    filled = _nearest_fill(src, rgb)
    tex = rgb.copy()
    band = (ink & (D <= t_out + 0.5)) if t_out else np.zeros_like(mask)
    replace = band | ~mask
    tex[replace] = filled[replace]
    q = np.floor(rgb[src] * 15.99).astype(int)
    keys = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    top = np.bincount(keys).argmax()
    back = rgb[src][keys == top].mean(axis=0)
    return tex, back


# ----------------------------------------------------------------------------
# inflation: Poisson + sqrt, coarse-to-fine red/black SOR
# ----------------------------------------------------------------------------
def _sor(u, m, iters, omega=1.85):
    h, w = u.shape
    up = np.zeros((h + 2, w + 2))
    up[1:-1, 1:-1] = u
    mp = np.zeros((h + 2, w + 2), bool)
    mp[1:-1, 1:-1] = m
    ii, jj = np.indices((h + 2, w + 2))
    sels = [mp & ((ii + jj) % 2 == 0), mp & ((ii + jj) % 2 == 1)]
    gs = np.zeros_like(up)
    for _ in range(iters):
        for sel in sels:
            gs[1:-1, 1:-1] = (up[:-2, 1:-1] + up[2:, 1:-1] + up[1:-1, :-2] + up[1:-1, 2:] + 1.0) * 0.25
            up[sel] += omega * (gs[sel] - up[sel])
    return up[1:-1, 1:-1]


def poisson_inflate(mask):
    levels = [mask]
    while min(levels[-1].shape) > 24:
        m = levels[-1]
        h2, w2 = (m.shape[0] + 1) // 2, (m.shape[1] + 1) // 2
        mp = np.zeros((h2 * 2, w2 * 2), bool)
        mp[: m.shape[0], : m.shape[1]] = m
        levels.append(mp.reshape(h2, 2, w2, 2).sum(axis=(1, 3)) >= 2)
    u = np.zeros(levels[-1].shape)
    for li in range(len(levels) - 1, -1, -1):
        m = levels[li]
        if u.shape != m.shape:
            u = np.kron(u, np.ones((2, 2)))[: m.shape[0], : m.shape[1]] * 4.0
        u = _sor(u * m, m, 160 if li == len(levels) - 1 else 60)
    return np.maximum(u, 0) * mask


def _box_down(a, f):
    h, w = a.shape[:2]
    H, W = -(-h // f) * f, -(-w // f) * f
    a = np.pad(a, [(0, H - h), (0, W - w)] + [(0, 0)] * (a.ndim - 2), mode="edge")
    return a.reshape((H // f, f, W // f, f) + a.shape[2:]).mean(axis=(1, 3))


class Model:
    def __init__(self, rgba, grid=200, tol=48):
        mask = compute_mask(rgba, tol)
        tex, back = prepare_texture(rgba, mask)
        ys, xs = np.nonzero(mask)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        size = max(y1 - y0, x1 - x0)
        f = max(1, int(round(size / grid)))
        mg = 2 * f
        m_full = np.pad(mask[y0:y1, x0:x1], mg)
        t = np.pad(tex[y0:y1, x0:x1], ((mg, mg), (mg, mg), (0, 0)), mode="edge")
        self.m = _box_down(m_full.astype(np.float32), f) >= 0.5
        self.tg = _box_down(t, f)
        self.u = poisson_inflate(self.m)
        self.back = back
        self.f, self.size = f, size
        self.X0, self.Y0 = x0 - mg, y0 - mg
        self.cx, self.cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0

    def points(self, volume):
        m, tg, f = self.m, self.tg, self.f
        gh, gw = m.shape
        scale = 2.0 / self.size
        dx = f * scale
        jj, ii = np.meshgrid(np.arange(gw), np.arange(gh))
        X = (self.X0 + (jj + 0.5) * f - self.cx) * scale
        Y = -(self.Y0 + (ii + 0.5) * f - self.cy) * scale
        Z = 2.0 * np.sqrt(self.u) * dx * volume
        ring = np.zeros_like(m)
        ring[1:] |= m[:-1]
        ring[:-1] |= m[1:]
        ring[:, 1:] |= m[:, :-1]
        ring[:, :-1] |= m[:, 1:]
        region = m | ring
        gy, gx = np.gradient(Z, dx)
        nrm = np.stack([-gx, gy, np.ones_like(Z)], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        Zp = np.pad(Z, 1)
        zmin = np.minimum.reduce([Zp[:-2, 1:-1], Zp[2:, 1:-1], Zp[1:-1, :-2], Zp[1:-1, 2:]])
        ink = (tg @ LW) < 0.33
        P, N, C, K = [], [], [], []

        def add(p, n, c, k):
            for side in (1, -1):
                pp, nn = p.copy(), n.copy()
                pp[:, 2] *= side
                nn[:, 2] *= side
                P.append(pp)
                N.append(nn)
                C.append(c if side == 1 else np.broadcast_to(self.back, c.shape))
                K.append(k if side == 1 else np.zeros_like(k))

        add(np.stack([X[region], Y[region], Z[region]], -1), nrm[region], tg[region], ink[region])
        step = dx * 0.75
        gap = (Z - zmin) * m
        need = gap > step
        if need.any():
            ks = np.ceil(gap[need] / step).astype(int)
            rep = np.repeat(np.arange(need.sum()), ks - 1)
            offs = np.concatenate([np.arange(1, k) / k for k in ks])
            zt, zlo = Z[need][rep], zmin[need][rep]
            zz = zlo + (zt - zlo) * offs
            nn = nrm[need][rep].copy()
            nn[:, 2] *= np.clip(zz / np.maximum(zt, 1e-9), 0, 1)
            nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
            add(np.stack([X[need][rep], Y[need][rep], zz], -1), nn, tg[need][rep], ink[need][rep])
        P = np.concatenate(P).astype(np.float32)
        wz = np.abs(P[:, 2]) + 1e-6
        P[:, 0] -= (P[:, 0] * wz).sum() / wz.sum()
        P[:, 1] -= (P[:, 1].max() + P[:, 1].min()) / 2
        pts = {
            "P": P,
            "N": np.concatenate(N).astype(np.float32),
            "C": np.ascontiguousarray(np.concatenate(C)).astype(np.float32),
            "K": np.concatenate(K).astype(np.float32),
            "dx": dx,
        }
        pts["rmax"] = float(np.linalg.norm(P, axis=1).max())
        pts["fit"] = fit_extent(P)
        return pts


def rot(yaw, pitch):
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return (Rx @ Ry).astype(np.float32)


def fit_extent(P):
    Ps = P[::7]
    xmax = ymin = ymax = 0.0
    for pitch in (0.0, 0.3):
        for i in range(36):
            p = Ps @ rot(2 * np.pi * i / 36, pitch).T
            s = PERSP / (PERSP - p[:, 2])
            xmax = max(xmax, float(np.abs(p[:, 0] * s).max()))
            ymin = min(ymin, float((p[:, 1] * s).min()))
            ymax = max(ymax, float((p[:, 1] * s).max()))
    return xmax, ymin, ymax


# ----------------------------------------------------------------------------
# render -> characters + colours
# ----------------------------------------------------------------------------
def light_dir(az_deg=-35.0, el_deg=35.0):
    a, e = np.radians(az_deg), np.radians(el_deg)
    return np.array([np.cos(e) * np.sin(a), np.sin(e), np.cos(e) * np.cos(a)], np.float32)


def render(pts, yaw, pitch, cols, rows, aspect, zoom, ramp, mode, paper, edges):
    P = pts["P"]
    R = rot(yaw, pitch)
    p = P @ R.T
    s = PERSP / (PERSP - p[:, 2])
    pw, ph = cols, rows / aspect
    xmax, ymin, ymax = pts["fit"]
    yc = (ymin + ymax) / 2
    S = zoom * 0.95 * min(pw / 2 / xmax, ph / (ymax - ymin))
    W, H = cols * SS, rows * SS
    u = (p[:, 0] * s * S + pw / 2) * SS
    v = (-(p[:, 1] * s - yc) * S + ph / 2) * aspect * SS
    sp = pts["dx"] * (PERSP / (PERSP - pts["rmax"])) * S * SS
    kx, ky = max(1, int(np.ceil(sp * 1.05))), max(1, int(np.ceil(sp * aspect * 1.05)))
    iu0 = np.floor(u - (kx - 1) / 2).astype(np.int64)
    iv0 = np.floor(v - (ky - 1) / 2).astype(np.int64)
    keys, zs, ids = [], [], []
    base = np.arange(len(P))
    for oy in range(ky):
        for ox in range(kx):
            iu, iv = iu0 + ox, iv0 + oy
            ok = (iu >= 0) & (iu < W) & (iv >= 0) & (iv < H)
            keys.append(iv[ok] * W + iu[ok])
            zs.append(p[ok, 2])
            ids.append(base[ok])
    key, z, idx = np.concatenate(keys), np.concatenate(zs), np.concatenate(ids)
    order = np.lexsort((-z, key))
    ks = key[order]
    first = np.ones(len(ks), bool)
    first[1:] = ks[1:] != ks[:-1]
    sel = order[first]
    pix, vis, zv = key[sel], idx[sel], z[sel]
    # shade only the visible samples
    n = pts["N"][vis] @ R.T
    L = light_dir()
    Hv = L + np.array([0, 0, 1], np.float32)
    Hv /= np.linalg.norm(Hv)
    ndl = n @ L
    wrap = np.clip((ndl + 0.35) / 1.35, 0, 1)
    spec = np.clip(n @ Hv, 0, 1) ** 48
    rim = (1 - np.clip(n[:, 2], 0, 1)) ** 3
    shade = 0.28 + 0.42 * wrap + 0.38 * np.clip(ndl, 0, 1)
    C = pts["C"][vis]
    col = C * shade[:, None] + 0.16 * spec[:, None] + 0.12 * rim[:, None] * C
    # gather into cells
    cell = (pix // W // SS) * cols + (pix % W) // SS
    nc = cols * rows
    cnt = np.bincount(cell, minlength=nc).astype(np.float32)
    csum = np.stack([np.bincount(cell, col[:, k], nc) for k in range(3)], -1)
    tsum = np.stack([np.bincount(cell, C[:, k], nc) for k in range(3)], -1)
    inkc = np.bincount(cell, pts["K"][vis], nc)
    zimg = np.full(W * H, -9.0, np.float32)
    zimg[pix] = zv
    depth = zimg.reshape(rows, SS, cols, SS).max(axis=(1, 3)).ravel()
    with np.errstate(invalid="ignore", divide="ignore"):
        colm = csum / np.maximum(cnt, 1)[:, None]
        texm = tsum / np.maximum(cnt, 1)[:, None]
    cov = cnt / (SS * SS)
    covered = cnt > 0
    lum = np.clip(colm @ LW, 0, 1)
    ink = covered & (inkc / (SS * SS) >= 0.25) & ((texm @ LW) < 0.55)
    dg = depth.reshape(rows, cols)
    dp = np.pad(dg, 1, constant_values=-9.0)
    nbmax = np.maximum.reduce([dp[:-2, 1:-1], dp[2:, 1:-1], dp[1:-1, :-2], dp[1:-1, 2:]]).ravel()
    occ = covered & (nbmax - depth > 0.12)
    cg = np.pad(covered.reshape(rows, cols), 1)
    sil = covered & ~(cg[:-2, 1:-1] & cg[2:, 1:-1] & cg[1:-1, :-2] & cg[1:-1, 2:]).ravel()
    nr = len(ramp)
    if paper:
        dk = np.clip(1 - lum, 0, 1) ** 1.25 * 0.92 + 0.06
        dk = np.where(ink, np.maximum(dk, 0.92), dk)
        if edges:
            dk = np.where(occ | sil, np.maximum(dk, 0.85), dk)
        b = dk * np.clip(cov * 1.25, 0, 1)
    else:
        b = np.clip(lum / 1.06, 0, 1) ** 1.3 * np.clip(cov * 1.15, 0, 1)
    gi = np.clip((b * (nr - 1) + 0.5).astype(int), 0, nr - 1)
    gi = np.where(covered, np.maximum(gi, 1 if nr > 2 else 0), 0)
    if not paper:
        gi = np.where(ink | (edges & occ), 0, gi)
    # display colours
    if mode == "color":
        if paper:
            l = (texm.max(-1, keepdims=True) + texm.min(-1, keepdims=True)) / 2
            disp = np.clip(l + (texm - l) * 1.35, 0, 1)
            disp = disp * np.where(l > 0.52, 0.52 / np.maximum(l, 1e-6), 1.0)
            dark = ink | (edges & (occ | sil))
            disp[dark] = (0.10, 0.08, 0.12)
        else:
            mx = np.maximum(colm.max(-1, keepdims=True), 1e-6)
            disp = colm / mx * np.clip(mx * 0.55 + 0.45, 0, 1)
            l = (disp.max(-1, keepdims=True) + disp.min(-1, keepdims=True)) / 2
            disp = np.clip(l + (disp - l) * 1.3, 0, 1)
    elif mode == "matrix":
        g = np.clip(0.25 + b * 0.9, 0, 1) if not paper else np.full(nc, 0.42)
        disp = np.stack([g * 0.25, g, g * 0.35], -1) if not paper else np.broadcast_to([0.05, 0.42, 0.18], (nc, 3))
    elif mode == "amber":
        g = np.clip(0.25 + b * 0.9, 0, 1)
        disp = np.stack([g, g * 0.68, g * 0.12], -1) if not paper else np.broadcast_to([0.62, 0.32, 0.02], (nc, 3))
    else:
        g = np.clip(0.35 + b * 0.75, 0, 1)
        disp = np.stack([g, g, g], -1) if not paper else np.broadcast_to([0.12, 0.11, 0.14], (nc, 3))
    rgb = (np.clip(disp, 0, 1) * 255).astype(np.int32).reshape(rows, cols, 3)
    return gi.reshape(rows, cols), rgb


# ----------------------------------------------------------------------------
# terminal output
# ----------------------------------------------------------------------------
def xterm256(rgb):
    q = np.clip(np.round(rgb / 255 * 5), 0, 5).astype(int)
    return 16 + 36 * q[..., 0] + 6 * q[..., 1] + q[..., 2]


def frame_text(gi, rgb, ramp, colour):
    chars = np.array(list(ramp))[gi]
    rows, cols = gi.shape
    out = []
    if colour == "none":
        for r in range(rows):
            out.append("".join(chars[r]).rstrip())
        return out
    q = (rgb >> 2) << 2  # fewer colour switches
    c256 = xterm256(rgb) if colour == "256" else None
    for r in range(rows):
        parts, last = [], None
        row_c = chars[r]
        for c in range(cols):
            ch = row_c[c]
            if ch != " ":
                key = c256[r, c] if c256 is not None else tuple(q[r, c])
                if key != last:
                    parts.append(f"\x1b[38;5;{key}m" if c256 is not None else "\x1b[38;2;%d;%d;%dm" % key)
                    last = key
            parts.append(ch)
        out.append("".join(parts).rstrip() + "\x1b[0m")
    return out


class Keys:
    """Non-blocking key reader (POSIX termios / Windows msvcrt)."""

    def __init__(self):
        self.ok = sys.stdin.isatty()
        self.win = os.name == "nt"
        self.old = None
        if self.ok and not self.win:
            import termios
            import tty

            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)

    def read(self):
        if not self.ok:
            return []
        keys = []
        if self.win:
            import msvcrt

            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    ch = {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT"}.get(msvcrt.getwch(), "")
                keys.append(ch)
            return keys
        import select

        buf = ""
        while select.select([sys.stdin], [], [], 0)[0]:
            data = os.read(self.fd, 64)
            if not data:
                break
            buf += data.decode("utf-8", "ignore")
        i = 0
        while i < len(buf):
            if buf.startswith("\x1b[", i) and i + 2 < len(buf):
                keys.append({"A": "UP", "B": "DOWN", "C": "RIGHT", "D": "LEFT"}.get(buf[i + 2], ""))
                i += 3
            else:
                keys.append(buf[i])
                i += 1
        return keys

    def close(self):
        if self.old is not None:
            import termios

            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)


def detect_colour(args):
    if args.no_color:
        return "none"
    if args.colors256:
        return "256"
    if args.truecolor:
        return "true"
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return "true"
    if os.environ.get("TERM_PROGRAM") == "Apple_Terminal":
        return "256"
    return "true"


def main():
    ap = argparse.ArgumentParser(description="이미지를 3D로 부풀려 터미널에서 돌리는 아스키 애니메이션")
    ap.add_argument("image", nargs="?", help="이미지 경로 (없으면 내장된 토끼)")
    ap.add_argument("--volume", type=float, default=0.75, help="입체감 0.15~1.4 (기본 0.75)")
    ap.add_argument("--speed", type=float, default=0.8, help="자동 회전 속도 rad/s (기본 0.8)")
    ap.add_argument("--ramp", choices=RAMP_ORDER, default="classic", help="글자셋")
    ap.add_argument("--mode", choices=MODES, default="color", help="색 모드")
    ap.add_argument("--light", action="store_true", help="밝은 배경 터미널용 (연필 스케치 스타일)")
    ap.add_argument("--aspect", type=float, default=0.5, help="글자 칸 가로/세로 비율 (기본 0.5)")
    ap.add_argument("--fps", type=float, default=30, help="최대 프레임 (기본 30)")
    ap.add_argument("--tol", type=int, default=48, help="배경 제거 감도 (투명 배경 아닌 이미지용)")
    ap.add_argument("--once", action="store_true", help="한 프레임만 출력하고 종료")
    ap.add_argument("--yaw", type=float, default=-20, help="--once 일 때 회전 각도(도)")
    ap.add_argument("--size", default=None, help="--once 출력 크기, 예: 100x45")
    ap.add_argument("--no-color", action="store_true", help="색 없이 글자만")
    ap.add_argument("--256", dest="colors256", action="store_true", help="256색 모드 강제")
    ap.add_argument("--truecolor", action="store_true", help="트루컬러 강제")
    args = ap.parse_args()

    colour = detect_colour(args)
    t0 = time.time()
    try:
        rgba = load_rgba(args.image)
    except FileNotFoundError:
        sys.exit(f"이미지를 찾지 못했어요: {args.image}")
    except Exception as e:
        sys.exit(f"이미지를 열지 못했어요 ({e}). PNG·JPG·WebP 파일인지 확인해 주세요.")
    model = Model(rgba, grid=200, tol=args.tol)
    volume = float(np.clip(args.volume, 0.15, 1.4))
    pts = model.points(volume)
    build_ms = (time.time() - t0) * 1000

    if args.once:
        if args.size:
            cols, rows = (int(v) for v in args.size.lower().split("x"))
        else:
            ts = shutil.get_terminal_size((100, 45))
            cols, rows = ts.columns, max(10, ts.lines - 2)
        gi, rgb = render(pts, np.radians(args.yaw), 0.12, cols, rows, args.aspect, 1.0,
                         RAMPS[args.ramp], args.mode, args.light, True)
        lines = frame_text(gi, rgb, RAMPS[args.ramp], colour)
        while lines and not lines[-1].replace("\x1b[0m", "").strip():
            lines.pop()
        while lines and not lines[0].replace("\x1b[0m", "").strip():
            lines.pop(0)
        print("\n".join(lines))
        return

    keys = Keys()
    out = sys.stdout
    out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
    if os.name == "nt":
        os.system("")  # enable VT sequences on Windows 10+
    yaw, pitch, zoom = -0.35, 0.12, 1.0
    auto, edges = True, True
    ramp_i, mode_i = RAMP_ORDER.index(args.ramp), MODES.index(args.mode)
    last_size = None
    last_t = time.time()
    fps_t, fps_n, fps = time.time(), 0, 0.0
    try:
        while True:
            now = time.time()
            dt = min(0.1, now - last_t)
            last_t = now
            for k in keys.read():
                if k in ("q", "Q", "\x03"):
                    return
                elif k in ("LEFT", "a", "A"):
                    yaw -= 0.15
                elif k in ("RIGHT", "d", "D"):
                    yaw += 0.15
                elif k in ("UP", "w", "W"):
                    pitch = max(-1.35, pitch - 0.1)
                elif k in ("DOWN", "s", "S"):
                    pitch = min(1.35, pitch + 0.1)
                elif k in ("+", "="):
                    zoom = min(3.0, zoom * 1.1)
                elif k in ("-", "_"):
                    zoom = max(0.35, zoom / 1.1)
                elif k == " ":
                    auto = not auto
                elif k in ("c", "C"):
                    mode_i = (mode_i + 1) % len(MODES)
                elif k in ("g", "G"):
                    ramp_i = (ramp_i + 1) % len(RAMP_ORDER)
                elif k in ("e", "E"):
                    edges = not edges
                elif k in ("v", "V"):
                    volume = float(np.clip(volume + (0.1 if k == "V" else -0.1), 0.15, 1.4))
                    pts = model.points(volume)
            if auto:
                yaw += args.speed * dt
            ts = shutil.get_terminal_size((100, 40))
            cols, rows = max(20, ts.columns), max(8, ts.lines - 1)
            if (cols, rows) != last_size:
                out.write("\x1b[2J")
                last_size = (cols, rows)
            ramp = RAMPS[RAMP_ORDER[ramp_i]]
            gi, rgb = render(pts, yaw, pitch, cols, rows, args.aspect, zoom, ramp,
                             MODES[mode_i], args.light, edges)
            lines = frame_text(gi, rgb, ramp, colour)
            status = (f" {MODE_KO[MODES[mode_i]]} · {RAMP_KO[RAMP_ORDER[ramp_i]]} · 볼륨 {volume:.2f} · {fps:4.1f}fps"
                      f"  |  ←→↑↓ 회전  +/- 확대  space 자동회전  c 색  g 글자  v/V 볼륨  e 윤곽  q 종료")
            out.write("\x1b[H" + "\n".join(l + "\x1b[K" for l in lines) + "\n\x1b[2m" + status[: cols - 1] + "\x1b[0m\x1b[K")
            out.flush()
            fps_n += 1
            if now - fps_t > 0.5:
                fps, fps_n, fps_t = fps_n / (now - fps_t), 0, now
            spare = 1.0 / args.fps - (time.time() - now)
            if spare > 0:
                time.sleep(spare)
    except KeyboardInterrupt:
        pass
    finally:
        keys.close()
        out.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        out.flush()
        print(f"안녕! (모델 준비 {build_ms:.0f}ms)")


if __name__ == "__main__":
    main()
