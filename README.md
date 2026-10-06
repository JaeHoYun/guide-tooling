# guide-tooling

VCF Private AI 가이드 시리즈와 AX 가이드에 적용하는 문서 규칙을 한곳에서 관리하는 저장소입니다. 규칙 레지스트리, 검증 스크립트, 리뷰 체크리스트를 보관합니다.

## 왜 만들었나

문서 규칙이 다섯 곳에 흩어져 있었습니다. 세 저장소의 CLAUDE.md, vcf-private-ai의 CONVENTIONS.md와 `verify_repo.py`, 작성자의 전역 지침, skill-vault 스킬 문서입니다. 같은 규칙이 출처마다 조금씩 달랐고, 서로 충돌하는 규칙도 있었습니다. 검증 스크립트는 vcf-private-ai 한 저장소만 검사했습니다.

이 저장소는 규칙의 원본을 `rules/registry.toml` 한 파일로 모읍니다. 규칙의 문장은 `templates/`에 있습니다. 각 저장소 CLAUDE.md의 규칙 부분, 검증 스크립트의 검사 정의, 인벤토리는 모두 이 두 곳에서 생성합니다.

## 구성

| 경로 | 내용 |
|------|------|
| `rules/registry.toml` | 규칙 레지스트리. 규칙, 기준선, 저장소 프로필, 충돌 기록의 유일한 원본 |
| `docs/inventory.md` | 레지스트리에서 생성한 인벤토리 표. 직접 고치지 않음 |
| `tools/render_inventory.py` | 인벤토리 생성기. `--check`는 생성 결과와 저장된 파일이 같은지 확인 |
| `tools/verify.py` | 검증 스크립트. 레지스트리를 읽어 저장소 프로필에 맞는 오류, 경고 규칙을 실행 |
| `templates/` | 가이드 저장소 CLAUDE.md와 CONVENTIONS.md 생성 구간의 문장 원본 |
| `tools/render_claude_md.py` | 생성기. 레지스트리와 템플릿으로 각 저장소의 생성 구간을 다시 생성 |
| `CLAUDE.md` | 이 저장소에서 규칙을 바꾸는 절차 |
| `tests/test_verify.py` | 검증 스크립트 회귀 테스트 |
| `ci/doc-verify.yml` | 가이드 저장소용 GitHub Actions 워크플로 원본. 각 저장소의 `.github/workflows/doc-verify.yml`은 이 파일의 복사본 |
| `.github/workflows/tooling-test.yml` | 이 저장소의 CI. 테스트, 인벤토리 일치, 가이드 저장소 4개 main의 오류 검사 |

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

규칙 52개와 충돌 7건을 기록했습니다. 오류와 경고 규칙 31개는 `tools/verify.py`가 모두 검사합니다. 리뷰 규칙 21개는 Claude 리뷰 단계에서 다룹니다. 리뷰 체크리스트 생성과 Claude 리뷰 연동은 다음 단계에서 진행합니다. 설계 경과는 [vcf-private-ai#66](https://github.com/JaeHoYun/vcf-private-ai/issues/66)에 기록합니다.

## 실행

Python 3.11 이상과 표준 라이브러리만 사용합니다.

```bash
python3 tools/render_inventory.py           # docs/inventory.md 생성
python3 tools/render_inventory.py --check   # 레지스트리와 인벤토리가 같은지 확인
python3 -m unittest discover -s tests       # 회귀 테스트
```

검증 스크립트는 가이드 저장소를 이 저장소와 같은 상위 폴더에 clone해 두고 실행합니다. 프로필은 저장소 폴더 이름으로 정합니다. 형제 저장소가 같은 폴더에 있으면 저장소 간 링크와 앵커도 검사합니다.

```bash
python3 tools/verify.py --repo ../vcf-private-ai                   # 오류와 경고 전체
python3 tools/verify.py --repo ../vcf-private-ai --level error     # 오류만
python3 tools/verify.py --repo ../vcf-private-ai --rule DASH-JOIN  # 규칙 하나만
python3 tools/verify.py --repo ../vcf-private-ai --diff-base origin/main   # 변경된 줄 전용 규칙 포함
python3 tools/verify.py --profile vcf-private-ai --description "저장소 설명"  # 저장소 설명(About) 검사
python3 tools/verify.py --list                                     # 규칙별 구현 상태
```

- 오류가 하나라도 있으면 종료 코드 1을 반환합니다. 경고는 종료 코드에 영향을 주지 않습니다.
- `--format github`는 GitHub Actions 주석 형식으로 출력합니다.
- `CUSTOMER_NAMES` 환경 변수(쉼표나 줄바꿈으로 구분)가 있을 때만 익명화 검사를 실행합니다. 고객사 이름은 이 저장소에 기록하지 않습니다.

## CI

GitHub Actions가 PR과 main 반영 시점에 검사를 자동으로 실행합니다.

| 저장소 | 워크플로 | 검사 이름 | 내용 |
|--------|----------|-----------|------|
| 가이드 저장소 4개 | `.github/workflows/doc-verify.yml` | `doc-verify` | 이 저장소의 main을 내려받아 문서 규칙을 검사합니다. 오류가 있으면 실패합니다. PR에서는 경고를 변경된 줄에 대해서만 표시합니다. 저장소 설명(About)도 검사합니다. |
| guide-tooling | `.github/workflows/tooling-test.yml` | `tooling-test` | 회귀 테스트, 인벤토리 일치, 가이드 저장소 4개 main의 오류 검사, 워크플로 복사본 일치를 확인합니다. |

가이드 저장소의 `doc-verify`는 항상 이 저장소의 main을 사용합니다. 그래서 레지스트리나 스크립트를 바꾸는 PR은 `tooling-test`에서 가이드 저장소 4개 main이 여전히 통과하는지 먼저 확인합니다. 규칙을 강화해 기존 문서가 위반하게 되면, 문서를 고치는 PR을 먼저 머지한 뒤 이 저장소의 PR을 머지합니다.

워크플로를 바꿀 때는 `ci/doc-verify.yml`을 고친 뒤 4개 저장소에 그대로 복사합니다. 복사본이 원본과 다르면 `tooling-test`가 경고를 표시합니다.

### 머지 차단 설정

검사 결과로 머지를 차단하려면 저장소마다 아래 설정이 필요합니다. 저장소 소유자가 GitHub 웹에서 설정합니다.

1. 저장소의 Settings > Rules > Rulesets에서 New ruleset > New branch ruleset을 선택합니다.
2. Enforcement status를 Active로, Target branches에 기본 브랜치(main)를 추가합니다.
3. Require a pull request before merging을 켭니다. 승인자 수는 0으로 두어도 됩니다.
4. Require status checks to pass를 켜고 검사 이름(`doc-verify`, guide-tooling은 `tooling-test`)을 추가합니다. 검사 이름은 해당 저장소에서 검사가 한 번 이상 실행된 뒤에 목록에 나타납니다.
5. 소유자 본인의 직접 수정도 막으려면 Bypass list를 비워 둡니다.

### 익명화 검사

고객사 이름 목록은 저장소마다 Settings > Secrets and variables > Actions에서 `CUSTOMER_NAMES` secret으로 등록합니다. 쉼표나 줄바꿈으로 구분합니다. 등록하지 않으면 익명화 검사를 건너뛰고 그 사실을 결과 요약에 표시합니다.

## 생성 구간

가이드 저장소의 CLAUDE.md(vcf-private-ai는 CONVENTIONS.md 3, 4, 5, 7절도)에는 아래 표시로 둘러싼 생성 구간이 있습니다. 생성 구간 밖은 저장소마다 직접 작성합니다.

```
<!-- guide-tooling:begin claude -->
...레지스트리와 템플릿에서 생성한 내용...
<!-- guide-tooling:end claude sha256=XXXXXXXXXXXX -->
```

종료 표시에는 생성 내용의 sha256 앞 12자리를 기록합니다. `doc-verify`의 STR-GENERATED-SYNC 검사가 이 값으로 상태를 판정합니다.

| 상태 | 판정 | 조치 |
|------|------|------|
| 생성 구간을 손으로 고침(내용과 sha256이 다름) | 오류 | 변경을 되돌리고 레지스트리나 템플릿을 고칩니다. |
| 레지스트리나 템플릿이 바뀌어 다시 생성해야 함 | 경고 | `python3 tools/render_claude_md.py --repo ../<저장소>`로 다시 생성하고 PR을 만듭니다. |
| 생성 구간이 없음 | 경고 | CLAUDE.md에 시작, 종료 표시를 넣고 생성기를 실행합니다. |

레지스트리 변경을 오류가 아니라 경고로 처리하는 이유는 순서 때문입니다. 오류로 처리하면 guide-tooling을 머지하기 전에는 가이드 저장소에서 새 내용으로 다시 생성할 수 없고, 머지한 뒤에는 가이드 저장소 4개가 동시에 실패합니다.

### 오탐 처리

규칙 전체에 해당하는 예외는 레지스트리 규칙의 `allow`(정규식)에 등록합니다. 특정 문장 하나만 예외로 할 때는 레지스트리의 `[[waivers]]`에 규칙, 저장소, 파일, 메시지에 포함된 문자열, 사유를 등록합니다. 문서 안에 무시 주석을 넣지 않습니다. 사용되지 않는 예외 등록은 실행 결과에 표시됩니다.
