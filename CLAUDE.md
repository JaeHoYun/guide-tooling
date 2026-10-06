# CLAUDE.md

이 저장소는 가이드 저장소 4개(vcf-private-ai, vcf-private-ai-apps, enterprise-ax-methodology, JaeHoYun 프로필)에 적용하는 문서 규칙의 원본과 검증 도구를 보관합니다. 이 저장소의 문서도 가이드 저장소와 같은 문장 규칙을 따릅니다. 문장 규칙 전문은 [vcf-private-ai의 CLAUDE.md](https://github.com/JaeHoYun/vcf-private-ai/blob/main/CLAUDE.md)에 생성되어 있습니다.

## 파일의 역할

| 경로 | 역할 | 직접 고치는지 |
|------|------|---------------|
| `rules/registry.toml` | 규칙, 기준선, 저장소 프로필, 충돌 기록, 예외 등록의 원본 | 예 |
| `templates/*.md.tmpl` | 가이드 저장소 CLAUDE.md와 CONVENTIONS.md 생성 구간의 문장 원본 | 예 |
| `tools/verify.py` | 검증 스크립트 | 예 |
| `tools/render_claude_md.py` | 생성 구간 생성기 | 예 |
| `tools/render_inventory.py` | 인벤토리 생성기 | 예 |
| `docs/inventory.md` | 레지스트리에서 생성한 인벤토리 | 아니요 |
| `ci/doc-verify.yml` | 가이드 저장소 워크플로 원본 | 예. 고친 뒤 4개 저장소에 그대로 복사 |

## 규칙을 바꾸는 절차

1. 레지스트리나 템플릿을 고칩니다. 검출 규칙을 바꾸면 `tests/test_verify.py`에 사례를 추가합니다.
2. `python3 tools/render_inventory.py`로 인벤토리를 다시 생성합니다.
3. `python3 -m unittest discover -s tests`와 `python3 tools/render_inventory.py --check`를 실행합니다.
4. 가이드 저장소 4개를 같은 상위 폴더에 clone하고 `python3 tools/verify.py --repo ../<저장소> --level error`로 오류가 새로 생기지 않는지 확인합니다.
5. PR을 만들고 `tooling-test` 검사가 통과한 뒤 머지합니다.
6. 머지한 뒤 가이드 저장소마다 `python3 tools/render_claude_md.py --repo ../<저장소>`로 생성 구간을 다시 생성하고 PR을 만듭니다. 생성 구간이 오래되면 `doc-verify`가 경고를 표시합니다.

규칙을 강화해 가이드 저장소 main이 오류를 내게 되면 `tooling-test`가 실패합니다. 이때는 가이드 저장소의 문서를 먼저 고쳐 머지한 뒤 이 저장소의 PR을 머지합니다.

## 지켜야 할 원칙

- **skill-vault는 읽기 전용 참조입니다.** skill-vault의 규칙은 레지스트리에 옮겨 적고 출처만 기록합니다. skill-vault 파일을 생성하거나 수정하지 않습니다.
- **고객사 이름을 이 저장소에 기록하지 않습니다.** 익명화 검사 목록은 각 가이드 저장소의 Actions secret `CUSTOMER_NAMES`에 보관합니다.
- **예외는 레지스트리에만 등록합니다.** 규칙 전체의 예외는 규칙의 `allow`에, 문장 하나의 예외는 `[[waivers]]`에 사유와 함께 등록합니다. 가이드 문서 안에 무시 주석을 넣지 않습니다.
- **표준 라이브러리만 사용합니다.** Python 3.11 이상에서 실행되어야 합니다.
- main에는 직접 커밋할 수 없습니다. 브랜치에서 작업하고 PR을 만듭니다.
