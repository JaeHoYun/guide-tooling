#!/usr/bin/env python3
"""레지스트리와 템플릿으로 가이드 저장소 규칙 문서의 생성 구간을 만든다.

생성 구간은 아래 표시 사이의 내용이다. 종료 표시에는 생성 내용의 sha256 앞 12자리를 기록한다.

  <!-- guide-tooling:begin NAME -->
  ...생성 내용...
  <!-- guide-tooling:end NAME sha256=XXXXXXXXXXXX -->

구간 이름과 대상 파일
  claude                 CLAUDE.md (모든 프로필)
  conventions-structure  CONVENTIONS.md 3, 4, 5절 (uses_conventions 프로필)
  conventions-symbols    CONVENTIONS.md 7절 (uses_conventions 프로필)

사용법
  python3 tools/render_claude_md.py --repo ../vcf-private-ai           # 생성 구간 갱신
  python3 tools/render_claude_md.py --repo ../vcf-private-ai --check   # 갱신이 필요하면 종료 코드 1
  python3 tools/render_claude_md.py --profile vcf-private-ai --print claude   # 생성 내용 출력

표준 라이브러리만 사용한다(Python 3.11 이상).
"""
import argparse
import hashlib
import os
import re
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "rules", "registry.toml")
TEMPLATES = os.path.join(ROOT, "templates")
LEVELS = {"error": "오류", "warn": "경고", "review": "리뷰"}

BLOCKS = {
    "claude": ("CLAUDE.md", "claude.md.tmpl"),
    "conventions-structure": ("CONVENTIONS.md", "conventions-structure.md.tmpl"),
    "conventions-symbols": ("CONVENTIONS.md", "conventions-symbols.md.tmpl"),
}
BLOCK_RE = re.compile(
    r"<!-- guide-tooling:begin (?P<name>[\w-]+) -->\n(?P<body>.*?)<!-- guide-tooling:end (?P=name) sha256=(?P<sha>[0-9a-f]{12}) -->",
    re.S,
)


def load_registry():
    with open(REGISTRY, "rb") as f:
        return tomllib.load(f)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def blocks_for(profile):
    names = ["claude"]
    if profile.get("uses_conventions"):
        names += ["conventions-structure", "conventions-symbols"]
    return names


# ---------------------------------------------------------------------------
# 템플릿 값
# ---------------------------------------------------------------------------


def in_scope(rule, profile_id):
    return rule["scope"] == ["all"] or profile_id in rule["scope"]


def values(reg, profile_id):
    p = reg["profiles"][profile_id]
    b = reg["baseline"]
    rules = {r["id"]: r for r in reg["rules"]}

    if p.get("baseline_text"):
        baseline = p["baseline_text"].format(**b)
    elif p.get("uses_baseline"):
        baseline = (
            f"{b['declaration']}({b['pais_ga']} GA)입니다. "
            f"이전 기준선({b['previous']}) 문서는 태그 `{b['previous_tag']}`에 보존합니다."
        )
        if p.get("baseline_extra"):
            baseline += " " + p["baseline_extra"]
    else:
        baseline = ""

    spatial = rules["WORD-SPATIAL"]
    table = ["| 피할 표현 | 대체 표현 |", "|-----------|-----------|"]
    table += [f"| {a} | {c} |" for a, c in spatial["replace"]]

    trans = rules["WORD-TRANSLATIONESE"]
    in_profile = [r for r in reg["rules"] if in_scope(r, profile_id)]
    rule_table = ["| ID | 규칙 | 수준 |", "|----|------|------|"]
    for r in in_profile:
        title = r["title"].replace("|", "\\|")
        rule_table.append(f"| {r['id']} | {title} | {LEVELS[r['level']]} |")

    return {
        "profile": profile_id,
        "h1_example": p.get("h1_example", ""),
        "h1_pattern": p.get("h1_pattern", ""),
        "h1_dash": "—" in p.get("h1_pattern", ""),
        "baseline_text": baseline,
        "form_title": p.get("form_title", "양식 대신 운영 기준"),
        "form_text": p.get("form_text", ""),
        "spatial_table": "\n".join(table),
        "spatial_watch": ", ".join(spatial.get("watch", [])),
        "translationese_list": ", ".join(h for _, h in trans["detect"]),
        "translationese_examples": ", ".join(f"{a} → {c}" for a, c in trans["replace"]),
        "meta_titles": ", ".join(reg.get("meta_titles", [])),
        "rule_table": "\n".join(rule_table),
        "_rules": rules,
        "_in_profile": {r["id"] for r in in_profile},
    }


def render_template(text, v):
    def cond(expr):
        if expr.startswith("rule:"):
            return expr[5:] in v["_in_profile"]
        return bool(v.get(expr))

    # 조건 구간: {{#if 조건}}...{{/if}} (중첩 없음)
    text = re.sub(r"\{\{#if ([^}]+)\}\}(.*?)\{\{/if\}\}", lambda m: m.group(2) if cond(m.group(1)) else "", text, flags=re.S)

    def field(m):
        key = m.group(1)
        if ":" in key:
            kind, rid = key.split(":", 1)
            rule = v["_rules"][rid]
            if kind == "exceptions":
                return ", ".join(rule.get("exceptions", []))
            if kind == "words":
                return ", ".join(rule.get("words", []))
            if kind in ("bad", "good"):
                return rule[kind]
            raise KeyError(key)
        val = v[key]
        if isinstance(val, bool):
            raise KeyError(key)
        return str(val)

    out = re.sub(r"\{\{([^#/}][^}]*)\}\}", field, text)
    if "{{" in out:
        raise ValueError("처리되지 않은 템플릿 표시가 남았습니다")
    return out


def render_block(reg, profile_id, name):
    _, tmpl = BLOCKS[name]
    with open(os.path.join(TEMPLATES, tmpl), encoding="utf-8") as f:
        text = f.read()
    body = render_template(text, values(reg, profile_id))
    return body if body.endswith("\n") else body + "\n"


def wrap(name, body):
    return f"<!-- guide-tooling:begin {name} -->\n{body}<!-- guide-tooling:end {name} sha256={digest(body)} -->"


# ---------------------------------------------------------------------------
# 파일 갱신과 검사
# ---------------------------------------------------------------------------


def find_blocks(text):
    return {m.group("name"): m for m in BLOCK_RE.finditer(text)}


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n"), crlf


def write(path, text, crlf):
    if crlf:
        text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def status(reg, profile_id, repo):
    """구간별 상태를 돌려준다: (파일, 구간, 상태). 상태는 ok, missing, edited, stale."""
    result = []
    for name in blocks_for(reg["profiles"][profile_id]):
        fname, _ = BLOCKS[name]
        path = os.path.join(repo, fname)
        if not os.path.exists(path):
            result.append((fname, name, "missing"))
            continue
        text, _ = read(path)
        m = find_blocks(text).get(name)
        if not m:
            result.append((fname, name, "missing"))
        elif digest(m.group("body")) != m.group("sha"):
            result.append((fname, name, "edited"))
        elif m.group("body") != render_block(reg, profile_id, name):
            result.append((fname, name, "stale"))
        else:
            result.append((fname, name, "ok"))
    return result


def update(reg, profile_id, repo):
    changed = []
    for name in blocks_for(reg["profiles"][profile_id]):
        fname, _ = BLOCKS[name]
        path = os.path.join(repo, fname)
        if not os.path.exists(path):
            print(f"건너뜀: {fname} 없음")
            continue
        text, crlf = read(path)
        m = find_blocks(text).get(name)
        if not m:
            print(f"건너뜀: {fname}에 '{name}' 구간 표시 없음")
            continue
        new = text[: m.start()] + wrap(name, render_block(reg, profile_id, name)) + text[m.end():]
        if new != text:
            write(path, new, crlf)
            changed.append(f"{fname}:{name}")
    return changed


def detect_profile(reg, repo):
    name = os.path.basename(os.path.abspath(repo))
    for pid, p in reg["profiles"].items():
        if p["repo"].split("/")[1] == name:
            return pid
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", help="대상 저장소 경로")
    ap.add_argument("--profile", help="프로필(기본: 저장소 폴더 이름으로 판단)")
    ap.add_argument("--check", action="store_true", help="갱신이 필요하면 종료 코드 1")
    ap.add_argument("--print", dest="print_block", help="지정한 구간의 생성 내용을 출력")
    args = ap.parse_args()

    reg = load_registry()
    profile_id = args.profile or (detect_profile(reg, args.repo) if args.repo else None)
    if profile_id not in reg["profiles"]:
        ap.error(f"프로필을 정할 수 없습니다: {profile_id}")
    if args.print_block:
        print(render_block(reg, profile_id, args.print_block), end="")
        return 0
    if not args.repo:
        ap.error("--repo가 필요합니다")
    if args.check:
        bad = [s for s in status(reg, profile_id, args.repo) if s[2] != "ok"]
        for fname, name, st in bad:
            print(f"{fname} '{name}' 구간: {st}")
        return 1 if bad else 0
    changed = update(reg, profile_id, args.repo)
    print("갱신: " + (", ".join(changed) if changed else "없음"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
