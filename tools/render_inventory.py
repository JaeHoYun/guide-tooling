#!/usr/bin/env python3
"""규칙 레지스트리(rules/registry.toml)에서 사람이 읽는 인벤토리 문서(docs/inventory.md)를 생성한다.

표준 라이브러리만 사용한다(Python 3.11 이상, tomllib).

사용법
  python3 tools/render_inventory.py           # docs/inventory.md 생성
  python3 tools/render_inventory.py --check   # 생성 결과와 저장된 파일이 다르면 종료 코드 1
"""
import argparse
import os
import re
import sys
import tomllib
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "rules", "registry.toml")
OUTPUT = os.path.join(ROOT, "docs", "inventory.md")

LEVELS = {"error": "오류", "warn": "경고", "review": "리뷰"}
METHODS = {
    "regex": "정규식",
    "wordlist": "단어 목록",
    "structure": "구조",
    "link": "링크",
    "repo-meta": "저장소 설정값",
    "claude": "Claude 리뷰",
    "owner": "소유자 확인",
    "process": "작업 절차",
}
GROUPS = [
    ("SYM", "기호"),
    ("DASH", "대시"),
    ("STR", "구조"),
    ("LINK", "링크"),
    ("WORD", "어휘"),
    ("CNT", "내용"),
    ("PRS", "문체"),
    ("PROC", "작업 절차"),
    ("META", "저장소 설정값"),
]
REQUIRED = ("id", "title", "level", "method", "scope", "status", "sources")


def load():
    with open(REGISTRY, "rb") as f:
        data = tomllib.load(f)
    errors = []
    ids = set()
    profiles = set(data.get("profiles", {}))
    for r in data["rules"]:
        for key in REQUIRED:
            if key not in r:
                errors.append(f"{r.get('id', '?')}: 필수 필드 {key} 없음")
        if r["id"] in ids:
            errors.append(f"{r['id']}: ID 중복")
        ids.add(r["id"])
        if r["level"] not in LEVELS:
            errors.append(f"{r['id']}: 알 수 없는 level {r['level']}")
        if r["method"] not in METHODS:
            errors.append(f"{r['id']}: 알 수 없는 method {r['method']}")
        for s in r["scope"]:
            if s != "all" and s not in profiles:
                errors.append(f"{r['id']}: 알 수 없는 프로필 {s}")
        if "pattern" in r:
            try:
                re.compile(r["pattern"])
            except re.error as e:
                errors.append(f"{r['id']}: 정규식 오류 {e}")
    conflict_ids = {c["id"] for c in data.get("conflicts", [])}
    for r in data["rules"]:
        if "conflict" in r and r["conflict"] not in conflict_ids:
            errors.append(f"{r['id']}: 충돌 기록 {r['conflict']} 없음")
    return data, errors


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def scope_text(scope):
    return "전체" if scope == ["all"] else ", ".join(scope)


def render(data):
    rules = data["rules"]
    out = []
    out.append("# 문서 규칙 인벤토리")
    out.append("")
    out.append("이 문서는 `rules/registry.toml`에서 `tools/render_inventory.py`로 생성합니다. 직접 고치지 않습니다.")
    out.append("")
    out.append(f"레지스트리 상태: {data.get('status', '')}. 기준선: {data['baseline']['declaration']}")
    out.append("")

    out.append("## 요약")
    out.append("")
    lv = Counter(r["level"] for r in rules)
    st = Counter(r["status"] for r in rules)
    out.append("| 구분 | 규칙 수 |")
    out.append("|------|--------:|")
    out.append(f"| 전체 | {len(rules)} |")
    for k, name in LEVELS.items():
        out.append(f"| 수준: {name} | {lv.get(k, 0)} |")
    for k in ("기존 검사", "범위 확대", "문서 규칙만 존재", "신규", "충돌 정리"):
        if st.get(k):
            out.append(f"| 상태: {k} | {st[k]} |")
    sv = sum(1 for r in rules if any(s.startswith("skill-vault:") for s in r["sources"]))
    out.append(f"| skill-vault를 출처로 포함 | {sv} |")
    out.append("")

    for prefix, name in GROUPS:
        group = [r for r in rules if r["id"].split("-")[0] == prefix]
        if not group:
            continue
        out.append(f"## {name}")
        out.append("")
        out.append("| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |")
        out.append("|----|------|------|------|-----------|------|------|")
        for r in group:
            out.append(
                "| {id} | {title} | {level} | {method} | {scope} | {status} | {sources} |".format(
                    id=r["id"],
                    title=cell(r["title"]),
                    level=LEVELS[r["level"]],
                    method=METHODS[r["method"]],
                    scope=cell(scope_text(r["scope"])),
                    status=r["status"],
                    sources=cell("<br>".join(r["sources"])),
                )
            )
        out.append("")

    out.append("## 충돌 기록")
    out.append("")
    out.append("| ID | 주제 | 각 출처의 입장 | 정리 방침 | 근거 결정 |")
    out.append("|----|------|----------------|-----------|-----------|")
    for c in data.get("conflicts", []):
        out.append(
            f"| {c['id']} | {cell(c['topic'])} | {cell('<br>'.join(c['sides']))} | "
            f"{cell(c['resolution'])} | {cell(c['decision'])} |"
        )
    out.append("")

    out.append("## 저장소 프로필")
    out.append("")
    out.append("| 프로필 | 저장소 | H1 형식 | 기준선 적용 | CONVENTIONS 적용 |")
    out.append("|--------|--------|---------|-------------|------------------|")
    for pid, p in data["profiles"].items():
        h1 = f"`{p['h1_example']}`" if "h1_example" in p else "—"
        out.append(
            f"| {pid} | {p['repo']} | {h1} | {'예' if p.get('uses_baseline') else '아니요'} | "
            f"{'예' if p.get('uses_conventions') else '아니요'} |"
        )
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="생성 결과와 저장된 파일이 같은지만 확인")
    args = ap.parse_args()

    data, errors = load()
    if errors:
        for e in errors:
            print(f"레지스트리 오류  {e}")
        return 1
    text = render(data)
    if args.check:
        current = open(OUTPUT, encoding="utf-8").read() if os.path.exists(OUTPUT) else ""
        if current != text:
            print("docs/inventory.md가 레지스트리와 다릅니다. tools/render_inventory.py를 실행하십시오.")
            return 1
        print("docs/inventory.md가 레지스트리와 같습니다.")
        return 0
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"생성: docs/inventory.md (규칙 {len(data['rules'])}개, 충돌 {len(data.get('conflicts', []))}건)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
