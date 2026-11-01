# -*- coding: utf-8 -*-
r"""데스 크림존 오프닝(P00OPEN1, FILM 1.08 cinepak 320×200 띠 2, 프레임 1,146) 한글화(2026-11-01)
  ① 화면 박힌 글(흰 명조) — 구간마다 기준 프레임 T 에서 글자 지우고 한글 그린 K 를 만들고, 구간 안 프레임마다
     · 거의 같음(steady) → K · 밝기 페이드 → f + α(K − T) · 디졸브(점무늬) → 화소별: T 와 같으면 K, 아니면 그대로
       (양쪽 다 검정이라 애매한 화소는 근처 원래 글자 화소의 «T 일치 비율»로 섞음)
  ② 이름 소개표(타자기, 프레임 128~140): 원래 값 글자 잉크 폭 비율만큼 한글을 드러냄
  ③ 음성 대사 자막(아래, 나눔고딕 Bold + 검정 테두리)
  → work/movie/kr/f####.png(바뀐 프레임만) → tools/movenc.reencode(바뀐 키 구간만 다시 굽기, 원래 크기 이하) → work/build/files/P00OPEN1
  python tools/opsub_dc.py [--noenc]    미리보기 work/movie/prev_*.png
"""
import os, sys, json, glob, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
MV = os.path.join(ROOT, 'work', 'movie'); FR = os.path.join(MV, 'fr'); KR = os.path.join(MV, 'kr')
FD = r'C:\claude\utils\font'
NMB = FD + r'\nanum-myeongjo\NanumMyeongjoBold.ttf'; NM = FD + r'\nanum-myeongjo\NanumMyeongjo.ttf'
NG = FD + r'\nanum-gothic\NanumGothic.ttf'; NGB = FD + r'\nanum-gothic\NanumGothicBold.ttf'

# 화면 글 구간: (프레임 a, b(포함), 기준 T, 한국어 줄[원래 줄 순서])
EVENTS = [
    (60, 127, 91, ['「크림존」을 되찾아라…']),          # 범위는 넉넉히 — 글자가 실제로 있는지는 compose 가 일치 비율로 판정
    (60, 127, 113, ['「크림존」은 놈이 가지고 있다']),
    (100, 127, 127, ['그놈의 이름은…']),
    (1080, 1141, 1108, ['이렇게 에치젠은', '「크림존」을 손에 넣었다']),
    (1080, 1141, 1120, ['그러나 지금,', '데스비스노스가 풀어놓은', '몬스터가']),
    (1080, 1141, 1131, ['에치젠을 덮쳐 온다…']),
]
# 소개표: 값 줄(y 범위, 원래 값 x 시작, 한국어)
PROFILE = (128, 140, [((31, 47), '에치젠 코스케'), ((71, 87), '컴뱃 에치젠')])
# 음성 자막(초) — 위스퍼 초벌 + 하스피 확인 대기
VOICE = [
    (12.0, 15.6, '그것은 10년 전의 일이었다'),
    (48.4, 50.6, '뭐야?그렉,살아 있나?'),
    (50.7, 52.0, '그래,어떻게든.'),
    (52.1, 55.0, '위에서 온다,조심해!'),
    (59.8, 61.8, '이쪽이다,에치젠.'),
    (63.5, 65.6, '뭐지,이 계단은?'),
    (66.8, 68.8, '일단 들어가 보자고.'),
    (82.9, 86.6, '모처럼이니 나는 이 빨간 문을 고르겠어.'),
]
TIMES = json.load(open(os.path.join(MV, 'times.json')))


def fr(i): return np.asarray(Image.open(os.path.join(FR, 'f%04d.png' % i)).convert('RGB')).astype(float)
def lum(a): return a.mean(2)


def dil(m, n=1):
    for _ in range(n):
        p = np.pad(m, 1); r = p.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): r |= np.roll(np.roll(p, dy, 0), dx, 1)
        m = r[1:-1, 1:-1]
    return m


def inpaint(a, m):
    a = a.copy(); m = m.copy()
    while m.any():
        k = ~m; s = np.zeros_like(a); c = np.zeros(m.shape)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            ks = np.roll(np.roll(k, dy, 0), dx, 1); s += np.roll(np.roll(a, dy, 0), dx, 1) * ks[..., None]; c += ks
        f = m & (c > 0)
        if not f.any(): break
        a[f] = s[f] / c[f][:, None]; m &= ~f
    return a


def render(text, font, size, ss=4):
    f = ImageFont.truetype(font, size * ss); W = int(f.getlength(text)) + 8 * ss; H = size * ss * 2
    im = Image.new('L', (W, H)); ImageDraw.Draw(im).text((2 * ss, size * ss // 2), text, font=f, fill=255)
    a = np.asarray(im).astype(float) / 255; ys, xs = np.nonzero(a > 0.02); a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h2, w2 = -(-a.shape[0] // ss) * ss, -(-a.shape[1] // ss) * ss
    return np.pad(a, ((0, h2 - a.shape[0]), (0, w2 - a.shape[1]))).reshape(h2 // ss, ss, w2 // ss, ss).mean((1, 3))


def fit(text, font, h, w):
    for s in range(h * 2, 6, -1):
        a = render(text, font, s)
        if a.shape[0] <= h and a.shape[1] <= w: return a
    raise AssertionError(('넘침', text))


def ink_of(T):
    L = lum(T); return (L > 70) & (np.abs(T[..., 0] - T[..., 2]) < 50)


def lines_of(ink, region=None):
    """잉크 행을 줄로 묶음 → [(y0, y1, x0, x1)]"""
    rows = np.nonzero(ink.sum(1) > 0)[0]; out = []; s = rows[0]; p = rows[0]
    for r in list(rows[1:]) + [10 ** 6]:
        if r - p > 3:
            xs = np.nonzero(ink[s:p + 1].any(0))[0]; out.append((s, p, xs.min(), xs.max())); s = r
        p = r
    return out


def make_K(T, texts, font=NMB):
    ink = ink_of(T); ln = lines_of(ink)
    assert len(ln) == len(texts), ('줄 수 다름', len(ln), texts)
    era = dil(ink, 2); K = inpaint(T, era)
    col = np.percentile(T[ink], 95, axis=0)
    glyph = np.zeros(ink.shape)
    for (y0, y1, x0, x1), t in zip(ln, texts):
        h = y1 - y0 + 1; a = fit(t, font, max(11, h - 3), 300)
        cx = (x0 + x1 + 1) / 2; x = int(round(cx - a.shape[1] / 2)); y = int(round((y0 + y1 + 1) / 2 - a.shape[0] / 2))
        x = max(2, min(318 - a.shape[1], x))
        g = glyph[y:y + a.shape[0], x:x + a.shape[1]]; np.maximum(g, a, out=g)
    BG = K.copy()
    K = K * (1 - glyph[..., None]) + col * glyph[..., None]
    region = dil(era | (glyph > 0.03), 2)
    return K, ink, region, BG


def compose(f, T, K, ink, region, uniq=None):
    """원래 프레임 f 에서 T → K 로 바꿈(steady / fade / dissolve 자동)"""
    d = np.abs(f - T).max(2); tol = 30
    if ink.sum() == 0: return f
    Lf_, Lt_ = lum(f), lum(T)
    # 압축 잡음: 원래 글자 화소에서 f 도 밝고 무채색이면 같은 글자로 봄
    match = (d < tol) | (ink & (Lf_ >= 0.6 * Lt_) & (np.abs(f[..., 0] - f[..., 2]) < 50))
    u = uniq if uniq is not None and uniq.sum() > 20 else ink                # 판정은 이 구간에만 있는 글자 화소로(「クリムゾン」 같은 공통 부분 제외)
    m = match[u].mean()
    out = f.copy()
    if m < 0.15: return f                                                  # 이 구간 글자가 (거의) 없음 — 다른 구간 한글이 비치지 않게
    if m > 0.9 and (np.abs(Lf_ - Lt_)[ink] < 40).mean() > 0.85:
        out[region] = K[region]; return out
    Lt = lum(T)[ink]; Lf = lum(f)[ink]; al = float((Lf * Lt).sum() / (Lt * Lt).sum())
    if 0.03 < al < 0.98 and (np.abs(Lf - al * Lt) < 25).mean() > 0.8:
        out[region] = (f + al * (K - T))[region]; return np.clip(out, 0, 255)
    # 애매(양쪽 검정) 화소: 근처 원래 글자 화소의 일치 비율
    im_ = (match & ink).astype(float); ic = ink.astype(float)
    k = np.ones(9) / 9
    def blur(x):
        x = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, x); return np.apply_along_axis(lambda c: np.convolve(c, k, 'same'), 0, x)
    loc = np.where(blur(ic) > 0.01, blur(im_) / np.maximum(blur(ic), 1e-6), m)
    dark = (lum(T) < 30) & (lum(f) < 30)
    a = np.where(dark, loc, match.astype(float))
    out[region] = (f * (1 - a[..., None]) + K * a[..., None])[region]
    return out


def profile(i, f):
    """소개표 프레임 i: 값 칸 원래 글자 지우고, 원래 폭 비율만큼 한국어"""
    a0, a1, items = PROFILE; out = f.copy()
    full = fr(a1)
    for (y0, y1), t in items:
        inkF = ink_of(full)[y0:y1 + 1]; inkF[:, :140] = False
        xs = np.nonzero(inkF.any(0))[0]
        if not len(xs): continue
        X0, X1 = xs.min(), xs.max()
        inkf = ink_of(f)[y0:y1 + 1]; inkf[:, :140] = False
        xf = np.nonzero(inkf.any(0))[0]
        if not len(xf): continue
        frac = (xf.max() - X0 + 1) / (X1 - X0 + 1)
        band = out[y0 - 2:y1 + 3]; m = dil(np.pad(inkf, ((2, 2), (0, 0))), 1); m[:, :140] = False
        band[m] = 0
        a = fit(t, NG, y1 - y0 - 1, 160)
        n = len(t); show = max(1, int(round(frac * n)))
        if show < n:                                                        # 앞 show 글자만(공백 포함 문자 수 기준)
            aa = fit(t[:show].rstrip() or t[0], NG, y1 - y0 - 1, 160)
            a = np.pad(aa, ((0, max(0, a.shape[0] - aa.shape[0])), (0, 0)))[:a.shape[0]]
        y = (y0 + y1 + 1) // 2 - a.shape[0] // 2
        reg = out[y:y + a.shape[0], X0:X0 + a.shape[1]]
        reg[:] = reg * (1 - a[..., None]) + 255 * a[..., None]
    return out


def sub_layer(text):
    a = fit(text, NGB, 12, 300); h, w = a.shape
    g = np.pad(a, 2); o = np.zeros_like(g)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): o = np.maximum(o, np.roll(np.roll(g, dy, 0), dx, 1))
    return g, o


def voice(i, f):
    t = TIMES[i - 1]
    for a, b, s in VOICE:
        if a <= t < b:
            g, o = sub_layer(s); h, w = g.shape; x = (320 - w) // 2; y = 198 - h
            reg = f[y:y + h, x:x + w]
            reg[:] = reg * (1 - o[..., None]) + 0 * o[..., None]
            reg[:] = reg * (1 - g[..., None]) + 255 * g[..., None]
            return f, True
    return f, False


def main(noenc=False):
    if os.path.isdir(KR): shutil.rmtree(KR)
    os.makedirs(KR)
    ev = []
    for a, b, Ti, texts in EVENTS:
        T = fr(Ti); K, ink, region, BG = make_K(T, texts); ev.append([a, b, T, K, ink, region, None, lum(BG), BG])
    for e in ev:
        oth = np.zeros_like(e[4])
        for o in ev:
            if o is not e and o[0] <= e[1] and e[0] <= o[1]: oth |= o[4]
        e[6] = e[4] & ~dil(oth, 1)
    changed = 0; prev = {}
    for i in range(1, len(TIMES) + 1):
        f0 = fr(i); f = f0.copy(); hit = False
        act = [e for e in ev if e[0] <= i <= e[1]]
        if act:
            # 같은 화소를 두 구간이 잡으면 T 일치가 많은 구간 먼저(나중 것이 덮음 → 일치 적은 것부터)
            # 구간마다 판정: 없음 / 밝기(α, 겹친 크로스페이드는 α 를 구간별로 더함) / 점무늬 디졸브(화소별)
            add = np.zeros_like(f0); dith = []; steady = []; kr_only = np.zeros_like(f0)
            uink = np.zeros(f0.shape[:2], bool)
            for e in act: uink |= e[4]
            Bf = lum(inpaint(f0, dil(uink, 2)))                                          # 프레임 바탕(글자 지운 것) — 바닥 무늬 밝기를 글자로 안 보게
            for e in act:
                a, b, T, K, ink, region, uq, lbg, BGc = e
                u = uq if uq.sum() > 20 else ink
                Lt = (lum(T) - lbg)[u]; Lf = (lum(f0) - Bf)[u]; al = float((Lf * Lt).sum() / (Lt * Lt).sum())
                fadeok = (np.abs(Lf - al * Lt) < 25).mean() > 0.8
                if al < 0.12 and fadeok: continue                                       # 없음
                if fadeok and al >= 0.9: steady.append(e)
                elif fadeok: add[region] += (al * (K - T))[region]; kr_only[region] += (al * (K - BGc))[region]
                else: dith.append(e)
            f = np.clip(f0 + add, 0, 255)
            for e in steady: f[e[5]] = np.clip(e[3] + kr_only, 0, 255)[e[5]]           # 다 보이는 구간 = 한글판 그대로(압축 잡음 잔재 없게) + 겹쳐 사라지는 구간의 한글만
            for a, b, T, K, ink, region, uq, lbg, BGc in sorted(dith, key=lambda e: (np.abs(f0 - e[2]).max(2)[e[6]] < 30).mean()):
                g = compose(f0, T, K, ink, region, uq)
                d = np.abs(g - f0).max(2) > 0.5; f[d] = g[d]
            hit = True
        if PROFILE[0] <= i <= PROFILE[1]: f = profile(i, f); hit = True
        f, v = voice(i, f); hit |= v
        if hit and np.abs(f - f0).max() > 0.5:
            Image.fromarray(np.clip(np.rint(f), 0, 255).astype(np.uint8)).save(os.path.join(KR, 'f%04d.png' % i)); changed += 1
            prev[i] = (f0, f)
    print('바뀐 프레임', changed)
    # 미리보기: 구간 대표 프레임(원본|한글)
    near = lambda s: 1 + min(range(len(TIMES)), key=lambda j: abs(TIMES[j] - s))
    pick = [86, 95, 100, 103, 112, 120, 127, 130, 131, 135, 140, 1100, 1105, 1108, 1114, 1120, 1128, 1131, 1138] + [near((a + b) / 2) for a, b, _ in VOICE]
    rows = []
    for i in pick:
        if i in prev: f0, f = prev[i]
        else: f0 = fr(i); f = f0
        rows.append(np.concatenate([f0, np.full((200, 4, 3), 255.0), f], 1))
    for k in range(0, len(rows), 6):
        Image.fromarray(np.concatenate(rows[k:k + 6], 0).astype(np.uint8)).save(os.path.join(MV, 'prev_%d.png' % (k // 6)))
    if noenc: return
    import movenc
    src = os.path.join(ROOT, 'work', 'disc0', 'P00OPEN1'); out = os.path.join(ROOT, 'work', 'build', 'files', 'P00OPEN1')
    movenc.reencode(src, FR, KR, out, os.path.getsize(src))


if __name__ == '__main__':
    main('--noenc' in sys.argv)
