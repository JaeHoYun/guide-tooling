#!/usr/bin/env python3
"""레지스트리(rules/registry.toml)에서 Claude 리뷰 체크리스트(docs/review-checklist.md)를 생성한다.

doc-review 워크플로의 Claude가 이 체크리스트를 기준으로 PR의 변경된 줄을 판정한다.
표준 라이브러리만 사용한다(Python 3.11 이상, tomllib).

사용법
  python3 tools/render_review_checklist.py           # docs/review-checklist.md 생성
  python3 tools/render_review_checklist.py --check   # 생성 결과와 저장된 파일이 다르면 종료 코드 1
"""
import argparse
import os
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "rules", "registry.toml")
OUTPUT = os.path.join(ROOT, "docs", "review-checklist.md")

INTRO = """# 문서 리뷰 체크리스트

이 문서는 `rules/registry.toml`에서 `tools/render_review_checklist.py`로 생성합니다. 직접 고치지 않습니다.

가이드 저장소의 `doc-review` 워크플로에서 Claude가 PR을 리뷰할 때 이 체크리스트를 판정 기준으로 사용합니다. 각 저장소의 CLAUDE.md 문장 규칙도 함께 따릅니다.

## 리뷰 방법

- 판정 대상은 PR에서 바뀐 Markdown 줄입니다. 바뀌지 않은 줄은 지적하지 않습니다.
- 위반이 분명할 때만 지적합니다. 확신이 없으면 지적하지 않습니다.
- 지적 하나에 규칙 ID 하나를 붙입니다. 근거를 한두 문장으로 적고, 고친 문장을 제안합니다.
- 같은 줄에 같은 규칙으로 이미 남긴 지적이 있으면 다시 남기지 않습니다.
- 소유자 확인 규칙은 판정하지 않고 요약 댓글에 확인할 위치만 적습니다.
- 리뷰 결과는 머지를 차단하지 않습니다. 작성자는 지적마다 수정하거나 사유를 답글로 남깁니다.
- 지적과 요약 댓글도 CLAUDE.md의 문장 규칙을 지켜 작성합니다.
"""


def scope_text(rule):
    return "전체 저장소" if rule["scope"] == ["all"] else ", ".join(rule["scope"])


def render(reg):
    rules = reg["rules"]
    out = [INTRO]

    out.append("## 1. 판정 규칙\n")
    out.append("Claude가 변경된 줄마다 판정합니다.\n")
    for r in rules:
        if r["level"] == "review" and r["method"] == "claude":
            out.append(f"### {r['id']}. {r['title']}\n")
            out.append(f"- 적용 범위: {scope_text(r)}")
            out.append(f"- 판정 기준: {r['criteria']}")
            if "bad" in r:
                out.append(f"- 잘못된 예: {r['bad']}")
                out.append(f"- 고친 예: {r['good']}")
            out.append("")

    out.append("## 2. 소유자 확인 규칙\n")
    out.append("Claude는 판정하지 않습니다. 해당하는 위치를 요약 댓글에 \"소유자 확인 필요\"로 적습니다.\n")
    for r in rules:
        if r["level"] == "review" and r["method"] == "owner":
            out.append(f"- **{r['id']}.** {r['title']}. {r.get('criteria', '')}".rstrip())
    out.append("")

    out.append("## 3. 경고 후보 판정\n")
    out.append(
        "`doc-verify`의 검증 스크립트가 변경된 줄에서 찾은 경고 후보를 함께 받습니다. "
        "후보마다 실제 위반인지 판정합니다. 실제 위반이면 해당 줄에 지적을 남기고, 오탐이면 지적하지 않고 요약 댓글에 개수만 적습니다. "
        "오탐이 반복되는 표현은 요약 댓글에 적어 레지스트리 예외 등록 후보로 남깁니다.\n"
    )
    out.append("| ID | 규칙 | 적용 범위 | 예외 |")
    out.append("|----|------|-----------|------|")
    for r in rules:
        if r["level"] == "warn":
            exc = ", ".join(r.get("exceptions", [])) or "—"
            out.append(f"| {r['id']} | {r['title'].replace('|', '/')} | {scope_text(r)} | {exc.replace('|', '/')} |")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="생성 결과와 저장된 파일이 같은지만 확인")
    args = ap.parse_args()
    with open(REGISTRY, "rb") as f:
        reg = tomllib.load(f)
    missing = [r["id"] for r in reg["rules"] if r["level"] == "review" and r["method"] == "claude" and "criteria" not in r]
    if missing:
        print("판정 기준(criteria)이 없는 리뷰 규칙: " + ", ".join(missing))
        return 1
    text = render(reg)
    if args.check:
        current = open(OUTPUT, encoding="utf-8").read() if os.path.exists(OUTPUT) else ""
        if current != text:
            print("docs/review-checklist.md가 레지스트리와 다릅니다. tools/render_review_checklist.py를 실행하십시오.")
            return 1
        print("docs/review-checklist.md가 레지스트리와 같습니다.")
        return 0
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("생성: docs/review-checklist.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
