# VIBECODING CONSTITUTION — 10조 (v3 개정판)

> 출처(정본): `_research/vibecoding-mastery/PROPOSAL-jarvis-vibecoding-system-v3.md` §5 (L83-96).
> 본 문서는 그 조문의 **전문 이식본**이다. 각 조문의 집행 주체·증거·예외는 `VIBECODING_ENFORCEMENT.md`
> (§C1 enforcement · §C2 precedence·waiver · §C3 identity · §C11 scribe)가 기계검증 가능하게 확정한다.
> 이 헌법은 **상시 로드(짧게)**, 시행령(§C 조문·skill·rule)은 온디맨드다(대립점 2 결론).
>
> **기존 `cys approval`(pack 배포 승인)과의 관계**: `cys approval` 은 pack 릴리스·배포 승인 체계이고,
> 본 헌법의 APR ledger(§C1.3)·waiver(§C2.3)·break-glass(§C3.4)는 **바이브코딩 작업 게이트**의 승인 체계다 —
> **별개 층위**로, 서로를 대체하지 않는다.

---

## 개정 요지 (v2 → v3)

- **6조**(결정권/기록권 분리 — A-3 수용): 인간=결정권, 에이전트=기록권(서기)만. 전사는 §C11로만.
- **9조**(read-only 대상 명시 — A-2 수용): read-only 대상 = 프로덕션 런타임 데이터플레인. 개발 저장소(코드·규칙 md·memory·커밋)는 무관.
- **10조**(lifecycle 참조 — B-8): 증류는 §C8 lifecycle(canonical SOT·rule_id·승격/대체/폐기)을 따른다.

각 조문의 집행 주체·증거·예외는 §C1(enforcement contract)·§C2(precedence·waiver)가 기계검증 가능하게 확정한다.

---

## 10조 전문

1. **Spec 선행** — Level 임계 이상에서 설계 문서 없는 프로덕션 구현 금지. [집행: §C1 표의 R1행 · Level 판정: §C4]

2. **검증수단 동봉** — pass/fail 신호 없는 구현 위임 금지. "검증 불가=미완". 검증기 자체의 공허 통과(vacuous pass) 방지는 §C10.

3. **구현자≠검증자** — 자기채점 금지, fresh verifier + 이종모델 검증. 벤더 장애 시 failover는 §C10.3.

4. **Regression 게이트** — 기존 기능 자동 검증 통과 전 done 금지. 무테스트 legacy의 예외 경로는 §C2.3 waiver.

5. **스코프 크립 차단** — 명시 안 된 기능 추가 금지, critic 감사 층 상시. 오너 승인 요구 변경은 §C2.2 change-delta로 흡수.

6. **인간 고정 영역 (v3 개정)** — 상태 경계·전이 규칙 + 도메인 특화·보안 크리티컬 로직은 **결정권이 인간에게** 있다. 에이전트는 인간 결정의 **기록권(서기·scribe)**만 가지며, 전사는 §C11의 표준 입력 명세를 통해서만 수행한다(해석·보완 금지). "인간"의 actor 정의와 master 대행 가능 범위는 §C1.2.

7. **복잡도 라우팅** — Level 판정 후 절차 강도. 격상 허용·격하 금지. 단 §C4.5의 승인된 재분류(명시 승인자+reason code)만 예외. silent Level 변경은 어떤 주체든 금지.

8. **doc-sync** — 행동·구조·계약·상태 변경은 문서 동반 갱신 없이 미완. 단 인간 결정 영역 문서(상태 명세 등)는 §C11 전사 프로토콜로만 갱신(에이전트 자율 갱신 금지 — 데드락 해소). L1의 문서 예산 충돌은 §C2.1 우선순위표를 따른다.

9. **프로덕션 인프라 강제 (v3 개정)** — 보안 게이트(Tier 1) 통과 + 에이전트 prod read-only. 지시 아닌 인프라 레벨. **read-only의 대상은 프로덕션 런타임 데이터플레인**(운영 DB·인프라·라이브 서비스 커넥션)이며, **개발 저장소(코드·규칙 md·memory·커밋)는 무관**하다 — 10조의 증류 쓰기와 모순 없음(A-2 판정). identity 분리·배포 주체·break-glass는 §C3.

10. **실수→규칙 증류 (v3 개정)** — 에러 수정·리뷰 수반 작업 종결마다 재발 방지 규칙 증류 의무(모든 done 의무 아님 — 의례화 방지). 증류는 §C8 lifecycle(canonical SOT·rule_id·승격/대체/폐기)을 따른다. 각 작업이 다음 작업을 쉽게 만든다.

---

## 집행 참조 색인 (조문 → 집행 계약)

| 조 | 집행 계약 | 도구/증거 |
|---|---|---|
| 1 Spec 선행 | §C1(R1행)·§C4(Level 판정) | `javis_viberoute.py`(Phase 1) |
| 2 검증수단 동봉 | §C10(vacuous pass 방지) | mutation/negative test |
| 3 구현자≠검증자 | §C1.1(verifier)·§C10.3(failover) | agy·codex 이종모델 |
| 4 Regression 게이트 | §C2.3 waiver | `javis_waiver.py` |
| 5 스코프 크립 차단 | §C2.2 change-delta | scope-delta 문서(approval_id) |
| 6 인간 고정 영역 | §C1.2·§C11 전사 | `javis_decision.py` |
| 7 복잡도 라우팅 | §C4.5 재분류(APR+reason code) | §C4 route-contract |
| 8 doc-sync | §C2.1 우선순위·§C11 | `javis_decision.py` |
| 9 프로덕션 인프라 강제 | §C3 identity·break-glass | prod 권한 거부 E2E |
| 10 실수→규칙 증류 | §C8 lifecycle | rule_id·canonical SOT |
