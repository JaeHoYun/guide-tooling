# guide-tooling

VCF Private AI 가이드 시리즈와 AX 가이드에 적용하는 문서 규칙을 한곳에서 관리하는 저장소입니다. 규칙 레지스트리, 검증 스크립트, 리뷰 체크리스트를 보관합니다.

## 왜 만들었나

문서 규칙이 다섯 곳에 흩어져 있었습니다. 세 저장소의 CLAUDE.md, vcf-private-ai의 CONVENTIONS.md와 `verify_repo.py`, 작성자의 전역 지침, skill-vault 스킬 문서입니다. 같은 규칙이 출처마다 조금씩 달랐고, 서로 충돌하는 규칙도 있었습니다. 검증 스크립트는 vcf-private-ai 한 저장소만 검사했습니다.

이 저장소는 규칙의 원본을 `rules/registry.toml` 한 파일로 모읍니다. 각 저장소의 CLAUDE.md 문장 규칙 절, 검증 스크립트의 검사 정의, Claude 리뷰 체크리스트는 모두 이 파일에서 생성합니다.

## 구성

| 경로 | 내용 |
|------|------|
| `rules/registry.toml` | 규칙 레지스트리. 규칙, 기준선, 저장소 프로필, 충돌 기록의 유일한 원본 |
| `docs/inventory.md` | 레지스트리에서 생성한 인벤토리 표. 직접 고치지 않음 |
| `tools/render_inventory.py` | 인벤토리 생성기. `--check`는 생성 결과와 저장된 파일이 같은지 확인 |

## 검사 대상

| 저장소 | H1 형식 | 기준선 적용 |
|--------|---------|-------------|
| JaeHoYun/vcf-private-ai | `# 05 — 제목` | 예 |
| JaeHoYun/vcf-private-ai-apps | `# 05 — 제목` | 예 |
| JaeHoYun/enterprise-ax-methodology | `# 03. 제목` | 아니요(벤더 중립) |
| JaeHoYun/JaeHoYun | 해당 없음 | 예 |

GitHub 저장소 설명(About)도 검사합니다.

## 규칙 수준

| 수준 | 처리 |
|------|------|
| 오류 | 검증 스크립트가 실패시키고, 필수 상태 검사로 머지를 차단합니다. |
| 경고 | 후보 목록만 출력하고 통과시킵니다. |
| 리뷰 | PR마다 Claude가 변경된 줄을 리뷰해 댓글을 남깁니다. 머지는 차단하지 않습니다. 소유자 확인 항목은 소유자가 판단합니다. |

## skill-vault와의 관계

skill-vault는 읽기 전용 참조 출처입니다. 문서에 적용되는 skill-vault 규칙은 레지스트리에 옮겨 적고 출처(파일과 절)만 기록합니다. 이 저장소는 skill-vault 파일을 생성하거나 수정하지 않습니다. 레지스트리와 skill-vault 규칙이 달라지면 비교표로만 보고합니다.

## 현재 상태

레지스트리 초안 단계입니다. 규칙 51개와 충돌 7건을 기록했습니다. 검증 스크립트 개정, CLAUDE.md 생성, GitHub Actions 연동은 다음 단계에서 진행합니다. 설계 경과는 [vcf-private-ai#66](https://github.com/JaeHoYun/vcf-private-ai/issues/66)에 기록합니다.

## 실행

Python 3.11 이상과 표준 라이브러리만 사용합니다.

```bash
python3 tools/render_inventory.py           # docs/inventory.md 생성
python3 tools/render_inventory.py --check   # 레지스트리와 인벤토리가 같은지 확인
```
