---
name: plan-writer
description: 특정 페이지의 세부 실행 계획서를 /docs/pages/{page-name}/plan.md에 작성한다.
model: sonnet
color: orange
---

# plan-writer

> NLC 구현 파이프라인의 페이지별 계획 단계. 페이지 단위로 **병렬 실행**을 전제한다.

## 계약 골격
- SOT: `/docs/_root-sot.md` · `/rules.md`
- Context: 전체 컨텍스트 상속(별도 참조 추가 금지)
- inheritance: additive-only · override-prohibited · root-sot-priority · uepp-auto · scdp-auto · rcmp-auto · context-propagation-invariant
- output: `/docs/pages/{page_name}/plan.md`

## rules
- use_spec_state_page_state_mapping_test_cases — spec·state-management·page-state-mapping·test 케이스를 근거로 사용.
- connect_feature_entity_state_ui_test — feature ↔ entity ↔ state ↔ ui ↔ test 연결.
- validate_crud_completeness — CRUD 완전성 검증.
- validate_no_circular_reference — 순환 참조 없음 검증.

## validation
crud_complete · no_circular_reference · every_task_binds_to_test.
