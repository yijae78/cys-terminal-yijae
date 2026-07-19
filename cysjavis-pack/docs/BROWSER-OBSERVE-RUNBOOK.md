# browserd 관측(observe) 런북 — P2-a

관측의 벽 넘기: 에이전트가 보는 브라우저를 사람(박사님·마스터)이 같이 본다.

## 절차
1. `python3 $PACK/bin/javis_browser.py observe <url>` — browserd가 headful Chromium을 기동해 URL을 연다.
   (`--headless`는 무시된다 — 관측은 사람이 창을 보는 것이 본질.)
2. headful Chrome 창을 **cys-terminal 옆에 수동 배치**한다(macOS: 창을 드래그해 반쪽 정렬 또는 Rectangle 등 창 관리자). AppleScript 자동 배치는 취약해 도입하지 않는다.
3. 반환 JSON의 `url`·`control`·`last_evidence_path`로 현재 관측 상태를 확인한다. web pane 상태 스트립도 같은 값을 표시한다.

## 조작권 규약
- 기본 `control: agent`. 에이전트 검증 동사가 그 창을 조작한다.
- 사람이 직접 조작하려면 `control acquire --actor human`으로 조작권을 사람에게 넘긴다(이후 에이전트 변경 동사는 `HUMAN_ACTIVE`로 거부). 끝나면 `control release`.
- 조작권은 **컨텍스트(창)별**이라 사람의 human 브라우징이 다른 창의 agent 검증을 막지 않는다.

## SOT
- `python3 $PACK/bin/javis_browser.py sot` = NotebookLM(박사님 생각 SOT)을 human 프로필로 관측(CEO 결재 경유).
