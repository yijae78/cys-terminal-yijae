---
# === NLC 계약 골격 (수정 금지 영역) ===
sot:
  - /docs/_root-sot.md
  - /rules.md
context:
  - /docs/_root-sot.md
  - /docs/rules/uepp.md
  - /docs/rules/scdp.md
  - /docs/rules/rcmp.md
  - /docs/project.md
  - /docs/tech-stack.md
layer: 2.5
identity: codebase-structure
relation:
  parent: tech-stack.md
  next: requirement.md
inheritance:
  - additive-only
  - override-prohibited
  - root-sot-priority
  - uepp-auto
  - scdp-auto
  - rcmp-auto
  - context-propagation-invariant
goal: define_code_structure_sot
rules:
  - four_layer_separation
  - dependency_points_inward
  - one_module_one_responsibility
outputs:
  - layer_definition
  - directory_tree
  - dependency_rules
validation:
  - dependency_direction_inward
  - no_layer_leak
path:
  output: /docs/codebase-structure.md
---

# Codebase Structure (`/docs/codebase-structure.md`)

> NLC 10단계 · 2-9 · 성격: 구조 청사진 · 핵심 질문: "코드는 어떻게 나뉘는가?"
> 코드베이스 구조의 SOT(구조 헌법). 현재 코드 설명이 아니라 구현 이전에 확정하는 계약.
> 핵심 원리: 요구사항 변경 시 **영향 범위가 좁고 명확할수록** 좋은 구조. "고칠 곳이 적은 것"보다 "어디인지 명확한 것"이 중요.
> 구조 품질 = 속도가 아니라 **변경 대응 비용**. RCMP가 영향 그래프를 정의 → 문서 구조가 "변경 시뮬레이터"가 된다.

## 4레이어 (의존성은 항상 안쪽을 향한다)
```
Presentation  ⟂  Application  ⟂  Domain  ⟂  Infrastructure
                     의존성 방향 → Domain(안쪽)
```

## Directory Tree (채움)
```
src/
  presentation/   # UI · 진입점
  application/     # 유스케이스 · 오케스트레이션
  domain/          # 순수 비즈니스 로직 (외부 의존 없음)
  infrastructure/  # DB · 외부 API · I/O
  shared/          # 공용 유틸 · 타입
  tests/
```

## SOLID
- S: 변경 이유는 하나. · O: 고치지 말고 추가. · L: 치환해도 안 깨짐. · I: 인터페이스는 작게. · D: 구현이 아닌 계약에 의존.

## 4대 분리 판단 기준
1. presentation ↔ business logic 분리.
2. pure business logic ↔ persistence 분리.
3. internal logic ↔ 외부 연동 contract/caller 분리.
4. 하나의 모듈 = 하나의 책임.

> 완료 후 `ruler apply`.
