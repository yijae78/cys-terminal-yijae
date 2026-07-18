# 뷰어 vendored OSS 대장 (W-PBa)

자비스 산출물 뷰어(`javis_view_bridge.py` 서빙 정적앱)가 사용하는 서드파티 라이브러리 대장.
전부 **로컬 vendored** — CDN 런타임 로드 없음(사이드카는 loopback 전용). 아래는 2026-07-19
다운로드 시점의 이름·버전·라이선스·출처·SHA-256.

클린룸 주의: 뷰어 앱 자체 코드(index.html·app.js·style.css·diff 렌더러)는 cmux 코드를
참조하지 않고 직접 작성했다. 아래 vendored 파일만 예외적 서드파티 반입이다.

| 파일 | 라이브러리 | 버전 | 라이선스 | SHA-256 |
|---|---|---|---|---|
| `vendor/marked.min.js` | marked | 12.0.2 | MIT | `15fabce5b65898b32b03f5ed25e9f891a729ad4c0d6d877110a7744aa847a894` |
| `vendor/highlight.min.js` | highlight.js | 11.9.0 | BSD-3-Clause | `837a6fa5b0c736b52bbde2b2b6190f305da3fc9ed41681db5321507057b5c846` |
| `vendor/github-dark.min.css` | highlight.js theme (github-dark) | 11.9.0 | BSD-3-Clause | `9f208d022102b1d0c7aebfecd8e42ca7997d5de636649d2b31ea63093d809019` |
| `vendor/github.min.css` | highlight.js theme (github) | 11.9.0 | BSD-3-Clause | `3a9a5def8b9c311e5ae43abde85c63133185eed4f0d9f67fea4b00a8308cf066` |
| `vendor/mermaid.min.js` | mermaid (UMD 자립 번들) | 10.9.1 | MIT | `61b335a46df05a7ce1c98378f60e5f3e77a7fb608a1056997e8a649304a936d6` |

## 출처 URL

- marked 12.0.2: `https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js`
  (upstream: https://github.com/markedjs/marked, MIT)
- highlight.js 11.9.0: `https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js`
  (테마: `.../build/styles/github-dark.min.css`, `.../github.min.css`)
  (upstream: https://github.com/highlightjs/highlight.js, BSD-3-Clause)
- mermaid 10.9.1: `https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js`
  (upstream: https://github.com/mermaid-js/mermaid, MIT)
  · 주의: `mermaid.esm.min.mjs` 는 청크 분할 재수출 스텁(76B)이라 자립 불가 →
    자립 UMD 번들 `mermaid.min.js` 를 반입했다.

## 라이선스 전문

각 라이브러리의 라이선스 전문은 같은 디렉토리에 동봉:
`marked.LICENSE` · `highlight.js.LICENSE` · `mermaid.LICENSE`.

## diff 렌더러 (self-authored)

diff 뷰는 서드파티(diff2html 등)를 반입하지 않고 `app.js` 안에 경량 unified-diff →
HTML 테이블 렌더러를 직접 작성했다(vendored 표면 축소 · 브리지가 이미 `git diff` 텍스트를
제공). 라이선스 의무 없음(자작).
