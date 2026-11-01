# 데스 크림존 (세가 새턴 일본판) 한글 패치

> **내려받기:** [릴리즈 페이지](https://github.com/hospi0/deathcrimson-kr-patch/releases/latest) — 최신 v0.9. 적용 방법·원본 MD5 는 패치 묶음의 readme 에 있습니다.
>
> 이 저장소에는 도구와 작업 문서만 있습니다(ROM·빌드 결과물 없음).

## 내용

- 오프닝 동영상(FILM/cinepak): 화면에 박힌 글자·이름 소개표를 한글로 다시 그리고, 음성 대사에 한글 자막을 넣어 바뀐 키 프레임 구간만 다시 구움(`tools/opsub_dc.py`, `tools/movenc.py`, `tools/filmcpk.py`)
- 메인 메뉴(조준설정·옵션)·조준 설정 안내·옵션 화면·신 1\~8 제목 — VDP1 16비트 RGB 날그림을 제자리에서 고침(`tools/gfx_dc.py`)
- 영문 제목 그림(Start Menu·Stage·Target Position·Option Setting...)과 로고는 원본 그대로

## 빌드 순서

```
python tools/disc.py dump 0
python tools/gfx_dc.py
python tools/opsub_dc.py
python tools/discbuild.py --write
python tools/make_dist.py
```

조사 기록: `docs/00_초기조사.md`
