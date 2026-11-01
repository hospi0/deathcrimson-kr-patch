# -*- coding: utf-8 -*-
r"""데스 크림존 그림 글자 한글화(2026-11-01) — 전부 VDP1 16비트 RGB 날그림(압축 없음, 0 = 투명, 0x8000 = 불투명 비트)
  메인 메뉴 P03SPRI0 @0x3E00 · 옵션 P04SPRI0 @0x3E00 · 조준 P05SPRI0 @0x16500 (320×224)
  신 제목 160×12 = 스테이지 SPRI0(회색 띠 연속 구간 시작 + 0x118 = 그림 시작, 0x100 단위)
  영문(Start Menu·Stage·Target Position·Option Setting...) 은 그대로(하스피 2026-11-01)
  python tools/gfx_dc.py          → work/build/files/<파일> + 미리보기 work/img/prev_*.png(원본|한글)
"""
import os, sys, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DISC = os.path.join(ROOT, 'work', 'disc0'); OUT = os.path.join(ROOT, 'work', 'build', 'files'); IMG = os.path.join(ROOT, 'work', 'img')
FD = r'C:\claude\utils\font'
NG = FD + r'\nanum-gothic\NanumGothic.ttf'; NGB = FD + r'\nanum-gothic\NanumGothicBold.ttf'
NM = FD + r'\nanum-myeongjo\NanumMyeongjo.ttf'; NMB = FD + r'\nanum-myeongjo\NanumMyeongjoBold.ttf'
G11 = FD + r'\Galmuri-v2.40.3\Galmuri11.ttf'; G14 = FD + r'\Galmuri-v2.40.3\Galmuri14.ttf'; G11B = FD + r'\Galmuri-v2.40.3\Galmuri11-Bold.ttf'

SCREENS = {'menu': ('P03SPRI0', 0x3E00), 'opt': ('P04SPRI0', 0x3E00), 'tgt': ('P05SPRI0', 0x16500)}
# 신 제목: 파일, 그림 시작, 한국어 이름 (일본어 고유명사 = 거센소리 규칙)
SCENES = [('P73SPRI0', 0x2D100, '1', '사로니카 마을'), ('P75SPRI0', 0x18400, '2', '림부르크 대학'), ('P71SPRI0', 0x16900, '3', '코네라토 다리'),
          ('P61SPRI0', 0x16F00, '4', '이즈킷토 강'), ('P63SPRI0', 0x15F00, '5', '앗심의 저택'), ('P51SPRI0', 0x15F00, '6', '사파루 유적'),
          ('P52SPRI0', 0x17F00, '7', '샤나파라'), ('P54SPRI0', 0x14B00, '8', '데스비스노스의 우주선')]


def load(d, o, w, h): return np.frombuffer(d[o:o + w * h * 2], '>u2').reshape(h, w).astype(int)
def chans(a): return a & 31, a >> 5 & 31, a >> 10 & 31
def pack(r, g, b): return 0x8000 | (np.clip(np.rint(b), 0, 31).astype(int) << 10) | (np.clip(np.rint(g), 0, 31).astype(int) << 5) | np.clip(np.rint(r), 0, 31).astype(int)
def rgb8(a): r, g, b = chans(a); return np.stack([r << 3, g << 3, b << 3], -1).astype(np.uint8)


def render(text, font, size, aa=True, sp=0, ss=4):
    """→ 알파(0~1) 배열, 잉크 범위로 자름. aa=False 면 비트맵 꼴 그대로(갈무리)"""
    k = ss if aa else 1; f = ImageFont.truetype(font, size * k)
    W = int(f.getlength(text) + abs(sp) * k * len(text)) + 8 * k; H = size * k * 2
    im = Image.new('L', (W, H)); dr = ImageDraw.Draw(im)
    if not aa: dr.fontmode = '1'
    x = 2 * k
    for ch in text:
        dr.text((x, size * k // 2), ch, font=f, fill=255); x += f.getlength(ch) + sp * k
    a = np.asarray(im).astype(float) / 255
    ys, xs = np.nonzero(a > 0.02); a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if aa:
        h2, w2 = -(-a.shape[0] // k) * k, -(-a.shape[1] // k) * k
        a = np.pad(a, ((0, h2 - a.shape[0]), (0, w2 - a.shape[1]))).reshape(h2 // k, k, w2 // k, k).mean((1, 3))
    else:
        a = (a > 0.5).astype(float)
    return a


def fit(text, font, h, w, aa=True, sp=0):
    """잉크 높이 h 이하·폭 w 이하가 되는 가장 큰 크기"""
    for s in range(h * 2, 6, -1):
        a = render(text, font, s, aa, sp)
        if a.shape[0] <= h and a.shape[1] <= w: return a
    raise AssertionError(('넘침', text, h, w))


def blend(bg, a, col):
    r, g, b = chans(bg); cr, cg, cb = col
    return pack(r * (1 - a) + cr * a, g * (1 - a) + cg * a, b * (1 - a) + cb * a)


def place(A, a, x0, y0, col):
    h, w = a.shape; reg = A[y0:y0 + h, x0:x0 + w]; m = a > 0.04
    reg[m] = blend(reg, a, col)[m]


def periodic_fill(A, m, P=40, keep=None):
    """40px 주기 바탕(메뉴 무늬): 지울 화소마다 ±40·80 자리 후보 중 최빈값"""
    H, W = A.shape; out = A.copy(); bad = m | (keep if keep is not None else False)
    for y, x in zip(*np.nonzero(m)):
        c = []
        for dy in (-80, -40, 0, 40, 80):
            for dx in (-80, -40, 0, 40, 80):
                if dy == dx == 0: continue
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and not bad[yy, xx]: c.append(A[yy, xx])
        if c: out[y, x] = collections.Counter(c).most_common(1)[0][0]
    return out


def dil(m, n=1):
    for _ in range(n):
        p = np.pad(m, 1); r = p.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): r |= np.roll(np.roll(p, dy, 0), dx, 1)
        m = r[1:-1, 1:-1]
    return m


def do_menu(A):
    r, g, b = chans(A)
    gm = np.zeros_like(A, bool); gm[188:222, 30:150] = ((g - r >= 2) & (g - b >= 4))[188:222, 30:150]      # 照準設定(녹색)
    pm = np.zeros_like(A, bool); pm[188:222, 175:310] = ((r - b >= 3) & (r - g >= 2))[188:222, 175:310]    # オプション(분홍)
    er = dil(gm | pm, 1) & ~((r + g + b < 30) & False)
    sat = (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) >= 4      # 무늬 아닌 색 화소는 후보 제외
    B = periodic_fill(A, er, keep=sat & ~er)
    a = fit('조준설정', NGB, 21, 100); place(B, a, 47 + (88 - a.shape[1]) // 2, 195 + (21 - a.shape[0]) // 2, (18, 21, 9))
    a = fit('옵션', NG, 20, 111); place(B, a, 187 + (111 - a.shape[1]) // 2, 194 + (20 - a.shape[0]) // 2, (25, 20, 18))
    return B


def do_tgt(A):
    r, g, b = chans(A)
    m = np.zeros_like(A, bool); m[196:220, 60:260] = ((r >= 3) & (r - g >= 3))[196:220, 60:260]          # 글자 줄만(위 y190 근처는 괴물 발톱 빨강)
    ys, xs = np.nonzero(m); box = (ys.min(), ys.max(), xs.min(), xs.max())
    er = dil(m, 1); B = A.copy()
    # 바탕 = 거의 검정(아래 원 빛 끝자락) → 같은 열 위아래 글자 밖 화소로 세로 보간
    for x in range(box[2] - 2, box[3] + 3):
        col = er[:, x]
        if not col.any(): continue
        ys_ = np.nonzero(col)[0]; y0, y1 = ys_.min() - 1, ys_.max() + 1
        y1 = min(y1, A.shape[0] - 1)
        for y in ys_:
            t = (y - y0) / max(1, y1 - y0); v0, v1 = np.array(chans(A[y0, x])), np.array(chans(A[y1, x]))
            B[y, x] = pack(*(v0 * (1 - t) + v1 * t))
    col = collections.Counter(A[m].tolist()).most_common(1)[0][0]
    a = fit('중심을 쏘아 주세요', NGB, box[1] - box[0] + 1, box[3] - box[2] + 1, sp=1)
    place(B, a, box[2] + (box[3] - box[2] + 1 - a.shape[1]) // 2, box[0] + (box[1] - box[0] + 1 - a.shape[0]) // 2, chans(col))
    return B, box


def do_opt(A):
    BG = 0x9420; WH = 0xFFDE; B = A.copy()
    # (지울 범위 y0,y1,x0,x1, 한국어, 꼴, 크기)
    items = [((176, 189, 10, 75), '사운드', G11), ((176, 189, 150, 215), '스테레오', G11), ((176, 189, 230, 300), '모노럴', G11),
             ((197, 214, 135, 180), '종료', G14)]
    for (y0, y1, x0, x1), t, f in items:
        reg = A[y0:y1, x0:x1]; ink = (reg != BG)
        ys, xs = np.nonzero(ink); ox0, ox1 = x0 + xs.min(), x0 + xs.max(); oy0, oy1 = y0 + ys.min(), y0 + ys.max()
        B[y0:y1, x0:x1] = BG
        a = render(t, f, {G11: 12, G14: 15}[f], aa=False)
        cx = (ox0 + ox1 + 1) // 2; x = cx - a.shape[1] // 2; y = oy1 - 1 - a.shape[0] + 1 if f == G11 else oy0 + (oy1 - oy0 - a.shape[0]) // 2
        g = a > 0; sh = np.zeros((a.shape[0] + 1, a.shape[1] + 1), bool); sh[1:, 1:] = g
        gg = np.zeros_like(sh); gg[:-1, :-1] = g
        reg2 = B[y:y + sh.shape[0], x:x + sh.shape[1]]
        reg2[sh & ~gg] = 0                                                     # 그림자 = 투명(뒤 검정이 비침, 원본과 같음)
        reg2[gg] = WH
    return B


def do_scene(A, num, name):
    """160×12 회색 명조 띠: «신 N» 은 원래 シーン 자리, 이름은 원래 이름 시작 자리"""
    r = A & 31; ink = r > 4
    cols = np.nonzero(ink.any(0))[0]
    # 原: シーンN · 이름 — 열 틈(4px 이상 빈 열)으로 두 덩이 나눔
    gaps = [i for i in range(len(cols) - 1) if cols[i + 1] - cols[i] > 6]
    x_s, x_n = cols[0], cols[gaps[0] + 1]
    mx = int(r[ink].max())
    assert not ((A != 0) & (r <= 1)).any() or True
    B = np.zeros_like(A)                                                   # 바탕 = 투명 0(원본 바탕도 0, 0x8000 검정 없음)
    for t, x, wmax in (('신 ' + num, x_s, x_n - x_s - 4), (name, x_n, 159 - x_n)):
        a = fit(t, NMB, 11, wmax)
        if a.shape[1] > wmax: raise AssertionError((t, a.shape))
        y = 1 + (11 - a.shape[0]) // 2
        g = np.rint(a * mx).astype(int); m = a > 0.08
        reg = B[y:y + a.shape[0], x:x + a.shape[1]]; reg[m] = 0x8000 | g[m] | g[m] << 5 | g[m] << 10
    return B


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(IMG, exist_ok=True)
    bufs = {}
    def buf(f):
        if f not in bufs: bufs[f] = bytearray(open(os.path.join(DISC, f), 'rb').read())
        return bufs[f]
    prev = []
    for key, (f, o) in SCREENS.items():
        d = buf(f); A = load(d, o, 320, 224)
        B = do_menu(A) if key == 'menu' else do_tgt(A)[0] if key == 'tgt' else do_opt(A)
        d[o:o + 320 * 224 * 2] = B.astype('>u2').tobytes(); prev.append((key, A, B))
    for f, o, n, nm in SCENES:
        d = buf(f); A = load(d, o, 160, 12); B = do_scene(A, n, nm)
        d[o:o + 160 * 12 * 2] = B.astype('>u2').tobytes(); prev.append(('scene' + n, A, B))
    for f, d in bufs.items():
        assert len(d) == os.path.getsize(os.path.join(DISC, f))
        open(os.path.join(OUT, f), 'wb').write(d)
    # 미리보기: 화면 3장(원본|한글) + 신 제목 8개 3배
    rows = []
    for key, A, B in prev[:3]:
        rows.append(np.concatenate([rgb8(A), np.full((224, 4, 3), 255, np.uint8), rgb8(B)], 1))
    im = Image.fromarray(np.concatenate(rows, 0)).resize((644 * 2, 224 * 3 * 2), Image.NEAREST); im.save(os.path.join(IMG, 'prev_screens.png'))
    sc = [np.concatenate([rgb8(A), np.full((12, 4, 3), 255, np.uint8), rgb8(B)], 1) for _, A, B in prev[3:]]
    sc = np.concatenate([np.concatenate([s, np.full((3, 324, 3), 80, np.uint8)], 0) for s in sc], 0)
    Image.fromarray(sc).resize((324 * 3, sc.shape[0] * 3), Image.NEAREST).save(os.path.join(IMG, 'prev_scenes.png'))
    print('파일', sorted(bufs), '→', OUT)


if __name__ == '__main__':
    main()
