# DESIGN — Control Center(메타버스 오피스) 업그레이드 + Safari 손상됨 근본수리

- 버전: v1.3 (v1.0 작성 → 3회 성찰(§9) → 3회 가상 시뮬레이션(§10) 반영)
- 작성: master (claude-ysfuture) · 2026-07-18
- 정본 코드 기준: `/Users/cys/dev/wt-gates-v0.12.88` (릴리스 라인 0.12.88)
  - 프론트: `cysjavis-pack/web/office3d.html` (2335줄)
  - 브리지: `cysjavis-pack/bin/javis_hud_bridge.py` (1617줄, 계약 v2)
  - 앱: `src/bin/cys.rs`, `src/bin/cysd/governance.rs`
- 구동 실측: 브리지 라이브 `localhost:8642`(설치본 `~/.cys/pack` — 구본 1841줄), `/world` v2 정상 응답

---

## 0. 요구사항 (박사님 지시 · 성공 기준은 전부 "화면 실측")

| ID | 지시 | 성공 기준 (박사님 화면에서) |
|----|------|------------------------------|
| R1 | watchdog을 실제 강아지로 돌아다니게 | 강아지가 로비·층·지하를 순찰하고, watchdog kill 이벤트 시 서버룸으로 달려가 짖는 연출이 보인다 |
| R2 | 회장실 머리 위 CYSJAVIS 문구 삭제 | 옥상 네온 'C Y S J A V I S'가 사라지고 좌상단 h1만 남는다 |
| R3 | 회장실을 넓고 멋지게 + 자리 근처 가면 자동 착석 | 회장실이 확장·고급화되고, 회장 아바타가 왕좌 근처 정지 시 항상 앉는다 |
| R4 | 층마다 개성 있는 자리배치·가구 구성 (랜덤) | 층별로 회의실·라운지·책상 배치가 서로 다르게 보인다 |
| R5 | dept 이름 숫자 금지, 개명 즉시 반영 | 화면 어디에도 `dept-N` 원시 키가 안 보이고, display_name 변경이 재시작 없이 층 라벨에 반영된다 |
| R6 | 1층 카페에서 토큰라떼·스킬·하네스 판매 | 카페 메뉴판에 실토큰 잔량이 보이고, 라떼/스킬/하네스를 "구매"하는 상호작용이 동작한다 |
| R7 | Safari 다운로드 '손상됨' 에러 근본수리 | Safari로 받은 DMG로 설치해도 앱이 자기삭제·손상됨 없이 정상 설치 경로로 유도된다 |

전 항목 공통 성공 기준: **배포 전 scoped 검증 브리지에서 화면으로 확인 → 배포 후 박사님 화면에서 재확인**. "코드가 들어갔다"는 완료가 아니다.

---

## 1. 실측된 현재 상태 (설계의 근거 — 전부 file:line 검증됨)

1. **착석 기하 결함(R3의 근원)**: `ownerHome=(1.7, -2.6)`(office3d.html:1558) ↔ `THRONE=(0.5, -3.65), nearR=0.9`(218행). 거리 ≈1.59 > 0.9 → 홈 대기 중 착석 조건 영구 거짓. `updateThroneSeat()`(1532행)는 정상이나 호출 시점의 기하가 틀렸다.
2. **고정 배치 하드코딩(R4의 제약)**: 회의실(706행 cx=4.4,cz=-2.2)·라운지(730행)·칸반(942행 "-3.2, 회의실 +x 겹침 회피" 주석)·**회의 소집 집합점(convene(): `entWalkTo(e, 4.4+…, -2.2+…)`, 주인 걷기 `(4.4, fy+0.74, -0.6)`)**이 각자 좌표를 소유. 배치를 바꾸면 회의 소집이 빈 바닥에 모이는 버그가 확정 발생.
3. **옥상 충돌(R3의 제약)**: 파라솔 x=3.4(870행). 회장실 확장 시 관통.
4. **watchdog 실존·폐기(R1)**: cysd가 `watchdog.proc_count_high`·`watchdog.duplicate_procs` 발행 + 45s/3+ 자동 kill(governance.rs:1440-1510, 불변식 3종 보유). 브리지는 `watchdog.*` 전량 폐기(hud_bridge.py:113,694 — §6.3 소음 필터).
5. **부서명(R5)**: 파이프라인은 정상 — depts.json display_name → `cys fleet`(cys.rs:5811) → 브리지 `_dept_label` → `/world` id 한글 실측 확인. 잔여 결함 2건: ①설치본(구본) 패널이 raw 키 노출(구본 1343행 `(${n.key})`) — 정본 1808행에서 이미 수리 ②개명 시 재빌드 미발동 — 형상 비교가 slug만 봄(hud_bridge.py:439-441).
6. **카페(R6)**: 순수 장식(755행). 재료 실존 — 노드별 rate 5h/7d used_pct·resets_at, `POST /command`→`cys send`(1497행), 스킬 약 90종.
7. **브리지 구동 형태**: `HUD_PORT` env로 포트, `WEB_DIR=팩루트/web` 상대 해석(29,32행) → 개발본 검증 인스턴스 구성 가능.
8. **배포 계약**: 설치 pack은 앱 릴리스의 pack 병합 이벤트로 갱신(0.12.82 "커스텀 생존(업데이트=병합 이벤트)"). **손 복사는 pack-heal이 되돌린다**(memory 실측) → 손 동기화 금지.
9. **월드 계약 가드**: `buildWorld`는 `w.v > 2`면 강제 리로드(1085-1090행) → 이번 변경은 전부 additive, **v=2 유지**.
10. **R7 원인 확정(자비스 기조사)**: Safari의 강한 quarantine → App Translocation → cys.app의 자기경로 기반 launchd/pack 로직이 임시경로에서 어긋나 자기삭제("손상됨"). 파일 자체는 정상(spctl accepted·공증·staple 확인). 0.12.87에 부분 가드(d90e471) 존재하나 Safari 경로 미차단.

---

## 2. 아키텍처 결정

### D1. FloorPlan descriptor — 층 배치 단일 SOT (R4·R1·R3의 토대, 최우선)

`office3d.html` 안에 층 배치 기술자를 신설한다. **배치 좌표의 소유권을 각 가구 함수에서 회수**해 이 객체로 옮긴다.

```js
// floorPlanOf(deptKey, seed, nodeCount) → plan
plan = {
  meeting: {x, z, w, d},        // 회의실 위치·크기
  gather:  {x, z},              // 회의 집합점 = meeting 중심 (불변식: meeting AABB 내부)
  lounge:  {x, z} | null,
  kanban:  {x},                 // 뒷벽 부착 x (불변식: meeting AABB와 비겹침)
  amenity: 'pingpong'|'plants'|'popup'|null,
  desks:   [[x, z, rotY], …],   // nodeCount개
  patrol:  [[x, z], …],         // R1 강아지 웨이포인트 (불변식: 가구 AABB 외부·슬랩 내부)
}
```

- **템플릿 뱅크 5종**(격자형·4인 클러스터형·창가 일렬형·미러 반전형·중앙 광장형)을 수제작하고, seed가 템플릿과 미세 변주(오프셋·액센트)를 선택한다.
- **seed 전략(R4 "랜덤" 의도 보존)**: 기본 = 부서 라벨 해시(같은 부서=항상 같은 배치, 재빌드 무널뜀). 좌상단 UI 토글 1개 "배치 섞기" = 세션 랜덤 seed(접속마다 새 배치). 기본값은 해시(master 권고안, 박사님 승인 완료), 랜덤 욕구는 토글로 충족.
- **소비자 전환(전수)**: `makeFloor`/`makeMeetingRoom`/`makeLounge`/`makeKanbanBoard`/`makePingPong`/`makePopupStore` 위치 인자화, `convene()`·`dismissMeeting()`의 집합·복귀 좌표 → `floorPlans.get(deptId).gather`, `slotPositions()` → `plan.desks`, 강아지 순찰 → `plan.patrol`. **좌표 리터럴이 함수 본문에 남으면 리뷰 반려 기준.**
- **회의 집합 링**: 현행 상수 반경(1.5/1.0)은 회의실이 작은 템플릿에서 유리벽 관통(§10 S1-4) — 링 반경을 `plan.meeting` 치수에서 유도(`rx=w/2-0.4, rz=d/2-0.4`)하고, 게이트 불변식은 집합점 중심이 아니라 **링 전체가 회의실 AABB 내부**로 단언.
- **"배치 섞기" 토글**: 클릭 시 `buildWorld(lastWorld)` 재호출로 세션 seed 재추첨. **replay.mode(타임머신) 중 비활성**(§10 S2-2).
- 로비(0층)·서버룸은 전용 고정 plan(전광판·카페·팝업은 로비 고정 — R6 상점 위치 안정성).

### D2. 착석 상태기계 (R3 핵심 — 시뮬레이션 결과 "1줄 수정"에서 상태기계 명세로 격상)

시뮬레이션(§10 S1-1~3)에서 착석은 단일 수치 수정으로 부족함이 판명됐다. 명세:

- **트리거 존 확장**: 왕좌 핀포인트 반경 0.9는 사용자가 자연스럽게 멈추는 책상 앞(거리 ≈1.65)을 배제한다 — 왕좌는 책상 뒤 폭 0.625 슬롯에 있어 일부러 비집고 들어가야 판정된다. 트리거를 **자리 존**(책상+왕좌를 포함하는 AABB, 대략 x∈[-0.7,1.7], z∈[-3.9,-2.2])으로 확장하고, 존 진입 + 정지 시 왕좌로 짧은 스냅 걷기 후 착석.
- **진입 3경로 모두 지원**: ①자율 idle(ownerHome을 THRONE 파생 `(THRONE.x, roofY+0.74, THRONE.z+0.65)`로 이동 — 거리 0.65<0.9) ②키보드(WASD/화살표) 접근 ③바닥 클릭 이동 접근.
- **이탈 명세(현행 결함 2건 수리)**: ⓐ기립 시 **y를 층 보행고(roofY+0.74)로 복원** — 현행 standFromThrone은 포즈만 복원해 좌면 y(+0.55)로 옥상을 침하 보행(walk는 x/z만 갱신) ⓑ**키보드 입력도 기립 트리거** — 현행은 plan 생성 경로만 standFromThrone을 불러, 키보드 이동 시 앉은 포즈로 미끄러지는 스케이팅 + ownerSeated 상태 잔류.
- THRONE SOT(217행 주석 계약) 유지. 회귀 단언: e2e에서 ①idle→착석 좌표=좌면 ②존 진입 정지→착석 ③기립 후 y=보행고 ④키보드 이동 중 착석 포즈 아님.

### D3. 회장실 확장 (R3)

- 유리 펜트하우스 w 5.0→7.0 (cx=0.5 유지, x∈[-3.0, 4.0]).
- **옥상 재배치(충돌 해소)**: 파라솔 (3.4,1.2)→(4.9,2.6)·(-4.2,1.6)→(-4.9,1.6), 라운지체어 동반 이동. SLAB_W/2=6.5 대비 여유 검증.
- 신규 집기: ①뒷벽 회장 대시보드 스크린(CanvasTexture — 부서별 진행%·비용·토큰 잔량, 기존 전광판 스로틀 패턴 재사용 ≥2s) ②서측 책장+트로피 ③게스트 체어 2 ④카펫 확대·골드 트림. 왕좌·책상 좌표는 THRONE SOT 기준 상대 배치.
- R2: `makeRooftop()`의 네온 스프라이트(882-883행) 삭제. `'회 장 실'` 라벨(859행) 유지. refitCam의 topY+2.2 여유(272행)는 유지(무해).

### D4. watchdog 강아지 (R1)

- **브리지**: 소음 필터에서 `watchdog.*`를 fx 변환 경로로 분기(틱 피드는 계속 차단 — §6.3 계약 유지). 신규 fx `{t:'dog', kind:'alert'|'kill', pid?, count?}`, 코얼레싱 ≤1건/10s. `/history` 아카이브에 자연 포함(리플레이 호환·additive).
- **프론트**: 저폴리 강아지 1마리(몸·머리·꼬리·다리 4, 꼬리 흔들기 애니메이션). 평시 `plan.patrol` 웨이포인트 순찰(로비→각 층→지하 순환). **층간 이동은 승강 코어 위치에서 페이드 전환** — 엘리베이터 카(elevCar)는 owner 라이드 전용 추적이라 공용 시 시각 경합(§10 S2-1). `kind:'kill'` 수신 시 **서버룸 중앙으로 질주(기본)** + 💢 팝, pid가 racks에 등록된 경우에만 해당 랙 LED 적색 점멸 3s — watchdog kill 대상은 대부분 scoped 등록 외 프로세스라 racks.get(pid)는 통상 miss(§10 S1-5). `kind:'alert'`는 해당 층으로 이동해 2회 짖는 팝. **강아지 메시에는 nodeKey·floorY userData 비부여**(클릭 판정 오염 방지, §10 S1-6). 재빌드(개명·토글) 시 강아지는 로비로 리셋(worldGroup 수명주기 — 기존 owner 리셋과 동일 규약).
- **정직한 사양**: watchdog 이벤트는 디바운스된 희귀 이벤트 — 평시 순찰이 주, 이벤트 반응은 보너스. 과대포장 금지.

### D5. 부서명 (R5)

- 개명 반영: 브리지 형상 비교를 `(slug, label)` 튜플로 확장(439-441행 2줄). 개명=구조 변경=전체 재빌드(드문 이벤트, 비용 수용— 회의 상태 초기화 허용).
- raw 키 비노출: 정본에서 이미 수리(1808행) — 배포로 해결. **게이트 추가**: e2e에서 화면 텍스트 전수에 `dept-\d+@surface` 패턴 부재 단언.

### D6. 카페 경제 (R6 — 단계형, 안전 경계 준수)

- **Phase A (표시·무위험)**: 카페 메뉴판 CanvasTexture — "오늘의 원두" = 부서별 5h/7d 토큰 잔량 실데이터, 라떼 가격표=예상 토큰 비용 표기. 팝업스토어 선반=스킬 진열: 브리지 신규 `GET /skills` — **스캔 소스 실측 확정(§10 S2-3)**: `~/.cys/pack/skills` + 계정 3곳(`~/.claude/skills`·`~/.claude-cysinsight/skills`·`~/.claude-ysfuture/skills`)의 SKILL.md name/description, 60s 캐시, 127.0.0.1 한정 유지, **계정별 가용성 라벨**(마스터에 보이는 스킬이 워커 계정에 없을 수 있음). 하네스 코너=`.claude/agents` 목록 진열.
- **클릭 우선순위(§10 S1-6)**: 캔버스 클릭 판정을 `nodeKey > shopItem > floorY` 순으로 명세 — 상점 아이템에 `userData.shopItem`을 부여하고 floorY보다 먼저 검사. 미명세 시 상품 클릭이 바닥 폴스루로 "주인 이동"이 되는 결함이 구현 후 확정 발생.
- **Phase B (상호작용)**: 상품 클릭→설명 패널→"선물하기"→대상 노드 선택(가드: `presence`가 waiting/drowsy인 노드만 활성, 작업 중 노드는 회색)→기존 `POST /command`로 **알림 텍스트만** 발송(`[카페 알림] ☕ 주인이 토큰라떼를 보냈습니다 — 회신 불요` / 스킬은 `[카페 알림] 🎁 스킬 '<이름>' 추천 — 필요 시 사용`). 발송 시 해당 책상에 머그 소품 60s 표시(기존 rate_limited 머그 재사용).
- **Phase C (실명령 발송) — 이번 범위에서 명시 제외**: 라떼→/clear 직결은 CSO 주관 2-phase handshake 절대규칙을 우회하는 뒷문이라 배제. 실집행 욕구는 기존 CSO 경로 유지. (박사님 재지시 시 별도 설계로.)

### D7. Safari 손상됨 근본수리 (R7 — Track T, Rust/앱)

- **T1 회귀 고정**: 0.12.87 가드(translocation/비정규 경로에서 launchd 자기등록 금지, d90e471)를 회귀 테스트로 고정.
- **T2 안전모드 부트 + 설치 도우미(신규 핵심)**: 기동 시 translocation 감지 → **데몬·pack·launchd 일체 불가동**, 단일 안내 화면: "응용 프로그램으로 이동" 버튼 → 원본 번들 경로 해석 → API 복사(NSFileManager 상당 — 서명 봉인 유지) → 사본의 `com.apple.quarantine` xattr 제거(사용자 개시 동작·무권한) → `codesign --verify`+`spctl -a` 결정론 검증 → 재실행. `/Applications` 쓰기 불가 시 `~/Applications` 폴백, 자동 이동 실패 시 Finder 드래그 안내문+xattr 명령 복사 버튼 폴백. **원본 경로 해석이 사설 API 의존이면 폴백 경로가 항상 성립해야 한다(수용 기준).**
  - **감지 규약(§10 S3-2 — 오탐=앱 무력화 방지)**: canonical allowlist(`/Applications`·`~/Applications`) 밖 + `/AppTranslocation/`·`/Volumes/`(DMG 직실행) 매치 시 발동. **개발·e2e 탈출구 `CYS_ALLOW_NONCANONICAL=1`** — 없으면 빌드 디렉토리 실행·T4 하네스 자체가 안전모드에 갇힌다. Chrome 경로도 DMG 안 직실행이면 자기경로 로직이 깨지므로(격리 무관) 감지 대상에 포함.
  - **기존 설치 위 업그레이드(§10 S3-1)**: `/Applications/cys.app` 실존+구 데몬 가동 중이면 무단 교체 금지 — 공식 종료 경로로 구 앱·데몬 정지 후 원자 교체(replaceItem 상당), 정지 실패 시 수동 안내 폴백. 안전모드의 "데몬 불가동" 원칙은 **신규 인스턴스 기동 금지**를 뜻하며, 설치된 구 데몬의 공식 정지는 허용(명세로 구분).
- **T3 즉시 완화(코드 무관·선행 배포 가능)**: cysinsight.com 다운로드 페이지에 Safari 안내 추가(배포 절차=memory `project_cysinsight_deploy_path`).
- **T4 릴리스 게이트 dogfooding**: 격리 시뮬레이션 e2e — `xattr -w com.apple.quarantine` 부여 후 DMG 마운트 상태 실행 → 안전모드 진입 + `/Applications/cys.app` 자기삭제 없음 단언. 새 강제장치는 자기 자신에 먼저 적용(memory `feedback_release_pipeline_catches_what_review_missed`).

### D8. 검증·배포 파이프라인 (전 트랙 공통)

1. **개발 검증 환경**: 개발 worktree의 브리지를 `HUD_PORT=8643 cys run --scoped -- python3 <dev>/bin/javis_hud_bridge.py`로 기동(WEB_DIR이 팩 상대경로라 개발본 web을 자동 서빙, scoped=생명주기 강제 종료). master가 브라우저로 R1~R6 전 항목 화면 실측 후에만 릴리스 단계 진입.
2. **e2e 게이트 확장**: `ui/e2e/office_detail_gate.py`를 픽셀 스냅샷 의존에서 **불변식 기반으로 확장** — ①책상-가구 AABB 비겹침(템플릿 5종 × seed 대표값 전수) ②집합점∈회의실 ③순찰점 가구 외부 ④raw 키 패턴 부재 ⑤owner idle=착석. 스냅샷(office_detail_snapshot.png)은 참고물로 강등(랜덤 배치와 픽셀 비교는 양립 불가).
3. **단일 릴리스 0.12.89**: 릴리스 라인에 feature 브랜치 → 로컬 게이트를 CI 동일 모드로 → 태그 전후 원격 태그 2회 실측(버전 선점, memory) → pack 병합 이벤트로 설치본 갱신(손 복사 절대 금지 — pack-heal이 되돌림). 문서 동기화: `docs/DESIGN-office-detail-v11.md`에 v12 증보(FloorPlan SOT·dog fx 계약).
4. **월드 계약**: 모든 필드 additive, `v:2` 유지(리로드 가드 오발동 금지). 구 프론트는 미지 fx 무시(switch default) — 하위호환 확인됨.

---

## 3. 작업 분해 · 역할 배정 ([ABSOLUTE ANCHOR for LLM Orchestration] 준수)

master는 **설계·브리프·검증·승인만** 한다. 구현 0줄. 티켓은 `javis_task.py checkout` 경유, done 전이는 `--evidence` 필수.

| 티켓 | 내용 | 담당 | 모델 | 선행 |
|------|------|------|------|------|
| W0 | 배포 상태 결정론 확인(설치 앱 버전·원격 태그·pack 병합 대기물 `.merge-pending.json`·**설치본 vs `.pristine` diff로 클린교체/3-way 분기 판정**(§10 S3-3)) | worker | sonnet(기계적·E3 게이트 충족 전제) | — |
| W1 | D1 FloorPlan SOT 리팩터 + 템플릿 5종 + seed 토글 | worker | opus | W0 |
| W2 | D2 착석 수리 + D3 회장실 확장·옥상 재배치 + R2 네온 삭제 | worker | opus | W1 |
| W3 | D4 강아지(브리지 fx + 프론트) | worker | opus | W1 |
| W4 | D5 개명 반영(브리지 2줄) + raw 키 게이트 | worker | opus | — |
| W5 | D6 카페 Phase A+B(/skills 엔드포인트 + 프론트 상점 + 가드) | worker | opus | W1 |
| W6 | D8-2 e2e 게이트 불변식 확장 | worker | opus | W1 |
| T1~T2 | D7 안전모드 부트·설치 도우미(Rust) | worker | opus | — |
| T3 | 홈페이지 Safari 안내 | worker | sonnet(정형 배포 절차) | — |
| T4 | 격리 시뮬레이션 릴리스 게이트 | worker | opus | T2 |
| R-1 | 각 티켓 산출물 적대 리뷰(반박 라운드) | reviewer1 (agy·codex) | — | 각 W/T |
| R-2 | 전체 diff 감사 + 저티어(W0·T3) 산출물 100% 감사 | reviewer2 | — | 전체 |
| V | scoped 브리지 화면 실측·diff/테스트 직접 확인·릴리스 승인 | **master** | — | 전체 |

- 리뷰어 판정은 `_round/REVIEWER_VERDICT_CONTRACT.md` 타입 스키마(verdict enum + evidence:file:line). 리뷰 프롬프트에 엄격 제약(지정 파일만) 강제.
- 병렬성: W4·T1~T3은 W1과 독립 → 즉시 병렬. W2·W3·W5·W6은 W1의 plan 인터페이스 확정 후(인터페이스 선고정으로 조기 병렬화 가능).

## 4. 파급 효과 전수 목록 (변경 → 영향)

| 변경 | 직접 영향 | 2차 영향 | 대응 |
|------|-----------|----------|------|
| FloorPlan SOT | 가구 6함수·convene/dismiss·slotPositions | e2e 스냅샷 무효화, DESIGN 문서, 강아지 경로 | W6 게이트 재설계·문서 증보 |
| ownerHome 이동 | advanceOwner 대기 위치 | 회의 소집 owner 귀환 플랜(ownerHome.clone 사용 2곳) — 자동 정합 | 회귀 단언 |
| 옥상 재배치 | makeRooftop·makeChairmanOffice | refitCam 8코너 fit(치수 불변이라 무영향), 엘리베이터 경로 | 화면 실측 |
| 브리지 형상 비교 확장 | merge_fleet | 개명 시 전체 재빌드(회의·고스트 초기화) | 허용·문서화 |
| watchdog fx 신설 | 소음 필터 §6.3·fx 계약·/history | 구 프론트(미지 fx 무시=안전)·리플레이 | additive 확인 |
| /skills 엔드포인트 | 브리지 라우팅 | CORS/보안 경계(127.0.0.1 유지)·계정별 스킬 편차 표기 | 캐시·가용성 라벨 |
| v:2 유지 | buildWorld 리로드 가드 | — | 명시 금지 규칙 |
| T2 안전모드 | 부트 체인 전체 | **정상 경로 오탐 시 앱 무력화 위험** — 감지 조건 보수적(AppTranslocation 경로 명시 매치 우선), T4로 양성·음성 케이스 모두 게이트 | 오탐 케이스 테스트 필수 |
| pack 병합 배포 | 설치본 office3d.html 대체 | 사용자 커스텀 병합 충돌 가능(`.merge-pending.json` 실존) | W0에서 대기물 선처리 |

## 5. 부트체인·온보딩 안전 점검

- 브리지·프론트 변경은 팩 **기존 파일 수정만**(신규 파일 0) → preflight 존재·매핑 검증 무영향.
- `v:2` 불변 → 구/신 프론트 어느 조합도 리로드 루프 없음.
- T2 안전모드는 **비정상 경로에서만** 발동 — 정상 부트 체인(cys boot·orchestra check)의 코드 경로와 분리. 오탐이 곧 앱 무력화이므로 T4에 "정상 /Applications 실행 → 안전모드 미진입" 음성 케이스를 반드시 포함(검증기는 음성 케이스로 검증 — memory `feedback_test_the_verifier_against_negative_cases`).
- scoped 검증 브리지는 이벤트 구독 추가 1개(읽기 전용)·작업 직후 강제 종료 — 자원 거버넌스 부합.

## 6. 명시적 제외 (범위 밖)

- 카페 Phase C(실명령 발송) — §D6 사유.
- 강아지 다중 마리·사운드 — 1마리·시각 연출만.
- 부서 개명 UI(개명 자체는 기존 depts.json/카탈로그 경로) — 이번 범위는 "반영"만.

## 7. 리스크 등록부

| 리스크 | 확률 | 완화 |
|--------|------|------|
| 템플릿-노드수 조합에서 책상 겹침 | 중 | W6 불변식 게이트 전수(템플릿×대표 노드수 1~12) |
| T2 원본 경로 해석 실패(사설 API) | 중 | 폴백 2단(수동 안내+xattr 복사 버튼)이 항상 성립 |
| pack 병합 충돌로 설치본 미갱신 | 저 | W0 선처리 + 배포 후 설치본 mtime/버전 실측 |
| 개명 재빌드 중 fx 유실 | 저 | 재빌드는 기존 경로 재사용(신규 위험 없음) |

## 8. 검증 계획 (성공 기준 대비)

1. W6 게이트 전수 green (결정론 exit code)
2. master가 scoped 브리지(8643)에서 R1~R6 화면 체크리스트 실측(스크린샷 증거 첨부)
3. T4 격리 시뮬레이션 양성+음성 green
4. 릴리스 0.12.89 → 설치본 갱신 실측(office3d.html 버전 마커) → **박사님 화면 최종 확인**

## 9. 성찰 로그 (v1.0 → v1.2 변경 사유)

- [성찰1] 강아지 순찰을 "로비만"에서 **전 층 순찰(엘리베이터 경유)**로 확장 — 박사님 지시는 "돌아다니게"(범위 한정 없음). / 하네스 판매가 표시 전용으로 축소돼 있던 것을 명시적으로 "Phase A=진열, Phase B=선물(추천 알림)"로 라떼·스킬과 동등 취급으로 승격. / R4 기본값=해시는 박사님이 권고안 승인("좋다")한 것으로 확정하되, 원지시 "랜덤"을 토글로 보존함을 명기.
- [성찰2] Phase B 알림도 stdin 주입임을 인정 — 기존 회의 소집 postCommand와 동일 패턴이므로 수용하되 "회신 불요" 문구·waiting 한정 가드를 수용 기준으로 격상. / e2e 픽셀 스냅샷과 랜덤 배치의 양립 불가를 발견 → 게이트를 불변식 기반으로 재설계(D8-2). / T2 오탐=앱 무력화 리스크 식별 → 음성 케이스 게이트 필수화.
- [성찰3] 파급 전수표(§4) 작성 과정에서 회의 소집 owner 귀환 플랜의 ownerHome 참조 2곳이 자동 정합됨을 확인(별도 수정 불요). / 배포를 "손 동기화"에서 "pack 병합 이벤트 단일 릴리스"로 교정(pack-heal 역전 실측 근거). / `v:2` 유지 규칙을 금지 규칙으로 명문화(리로드 가드 오발동 방지). / W0에 `.merge-pending.json` 선처리 추가.

## 10. 가상 시뮬레이션 로그 (v1.2 → v1.3 · 구체값을 실코드 경로에 흘린 3회 모의 실행)

### Sim 1 — 런타임 프레임 시뮬레이션 (프론트 상호작용)

- **S1-1 (중대·R3 체감 원인 후보)**: 수동 조종(MMORPG, 2026-07-07 탑재 실측)으로 회장을 몰아 책상 앞(z≈-2.0)에 세우면 왕좌(0.5,-3.65)와 거리 ≈1.65 > nearR 0.9 → 착석 불발. 왕좌 판정권은 책상 뒷면(z≈-3.28)과 이동 클램프(z≥-3.9) 사이 폭 0.625 슬롯 — 일부러 비집고 들어가야만 앉는다. "자리 근처로 가면 앉는다"는 요구와 판정 기하가 불일치. → D2 트리거 존 확장.
- **S1-2 (중대)**: 착석(y=roofY+0.55) 후 기립 시 y 미복원 — standFromThrone(1544행)은 포즈만 복원, walk 스텝(1600행)은 `d.y=0`으로 x/z만 이동 → 옥상 침하 보행 영구화. D2로 착석이 일상화되면 상시 노출되는 잠복 결함. → 기립 시 y 복원.
- **S1-3 (중대)**: 키보드 이동(ownerManualTick)은 plan을 만들지 않아 standFromThrone 미호출 → 앉은 포즈로 미끄러지는 스케이팅 + ownerSeated 잔류. → 키보드 입력도 기립 트리거.
- **S1-4**: convene() 집합 링 반경 상수(1.5/1.0)가 소형 회의실 템플릿에서 유리벽 관통. → 링 반경을 plan.meeting 치수 유도, 게이트 불변식을 링 전체로.
- **S1-5**: 강아지 kill 타깃 `racks.get(pid)`는 통상 miss — 서버룸 racks는 `cys run --scoped` 등록 프로세스만 보유(브리지 server_room 계약), watchdog kill 대상은 임의 중복 프로세스. → 기본 타깃=서버룸 중앙, pid 매치 시에만 랙 LED.
- **S1-6**: 클릭 판정 루프(1730행)는 nodeKey→floorY 2단 — 상점 아이템 클릭이 floorY 폴스루로 "주인 이동"이 됨. → nodeKey>shopItem>floorY 우선순위 명세, 강아지 메시는 양쪽 userData 비부여.

### Sim 2 — 수명주기·상태기계·동시성

- **S2-1**: 강아지 층간 이동을 엘리베이터로 하면 elevCar(owner 라이드 전용 추적, 1610행)와 시각 경합. → 승강 코어 페이드 전환으로 변경.
- **S2-2**: 재빌드(개명·배치 토글)는 worldGroup 전체 파기 → owner·강아지 위치 리셋(기존 규약과 동일·수용). 토글은 replay.mode 중 비활성.
- **S2-3**: /skills 스캔 소스 실측 — `~/.cys/pack/skills` 실재 + 계정 3곳 실재 확인. 계정별 가용성 라벨 필수(마스터·워커 스킬 편차).
- **S2-4**: 검증용 이중 브리지는 fleet 폴링 2배(부서 소켓 org.status 순회) — 검증 창 한정 + scoped 생명주기 종료로 수용.

### Sim 3 — 배포·업그레이드·Safari 경로

- **S3-1 (중대)**: 기존 설치 위 업그레이드 시나리오 — 구 cys.app·구 데몬 가동 중 번들 교체는 충돌. 안전모드 "데몬 불가동"(신규 기동 금지)과 "구 데몬 공식 정지"(허용)를 명세로 구분, 원자 교체 + 수동 폴백. → D7 T2 증보.
- **S3-2 (중대)**: T2 감지가 canonical 밖 전부를 잡으면 개발 빌드·e2e 하네스 자신이 안전모드에 갇힘 → allowlist + `CYS_ALLOW_NONCANONICAL=1` 탈출구. Chrome이라도 DMG 안 직실행은 자기경로 로직이 깨지므로(memory 실측) 감지 대상 포함.
- **S3-3**: 설치본 pack에 `.pristine` 기준선 실재 확인 → W0 분기(클린=교체/오염=3-way)가 결정론화 가능.
- **S3-4**: 배포 스큐 — 구프론트+신브리지(미지 fx 무시=안전)·신프론트+구브리지(강아지 순찰은 프론트 단독 동작=우아한 강등) 양방향 확인.
