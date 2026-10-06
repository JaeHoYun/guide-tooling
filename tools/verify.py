#!/usr/bin/env python3
"""가이드 저장소 문서 검증 스크립트.

규칙 정의는 rules/registry.toml에서 읽는다. 표준 라이브러리만 사용한다(Python 3.11 이상).

수준
  error   위반이 하나라도 있으면 종료 코드 1
  warn    후보만 출력하고 통과
  review  이 스크립트가 검사하지 않음(Claude 리뷰와 소유자 확인)

사용법
  python3 tools/verify.py --repo ../vcf-private-ai
  python3 tools/verify.py --repo ../vcf-private-ai --level error        # 오류만 출력
  python3 tools/verify.py --repo ../vcf-private-ai --rule DASH-JOIN     # 특정 규칙만
  python3 tools/verify.py --repo . --profile JaeHoYun                   # 프로필 지정
  python3 tools/verify.py --repo ../vcf-private-ai --diff-base origin/main   # 변경된 줄 전용 규칙 포함
  python3 tools/verify.py --profile vcf-private-ai --description "저장소 설명"  # 저장소 설명(About)만 검사
  python3 tools/verify.py --list                                         # 규칙별 구현 상태

형제 저장소는 --siblings 위치(기본: --repo의 상위 폴더)에서 저장소 이름으로 찾는다.
CUSTOMER_NAMES 환경 변수(쉼표나 줄바꿈으로 구분)가 있으면 익명화 검사를 실행한다.
"""
import argparse
import os
import re
import subprocess
import sys
import tomllib
import urllib.parse
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "rules", "registry.toml")
OWNER = "JaeHoYun"
LEVEL_ORDER = {"error": 0, "warn": 1}

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
GH_RE = re.compile(
    rf"^https://github\.com/{OWNER}/([^/#]+)(?:/(?:blob|tree)/([^/#]+)(/[^#]*)?)?/?(?:#(.*))?$"
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HANGUL = "가-힣"


# ---------------------------------------------------------------------------
# 문서 읽기
# ---------------------------------------------------------------------------


class Doc:
    """Markdown 문서 하나. 코드 블록 밖의 줄과 각 줄이 속한 헤딩 경로를 보관한다."""

    def __init__(self, path, rel):
        self.path = path
        self.rel = rel.replace(os.sep, "/")
        self.base = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            self.text = f.read()
        self.lines = []  # (줄 번호, 원문, 코드 스팬을 지운 줄, 현재 H2 제목)
        in_fence = False
        h2 = ""
        for no, line in enumerate(self.text.split("\n"), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = HEADING_RE.match(line)
            if m and len(m.group(1)) == 2:
                h2 = m.group(2)
            self.lines.append((no, line, strip_code(line), h2))

    def paragraphs(self):
        """빈 줄로 나뉜 단락을 (시작 줄 번호, 줄 목록)으로 돌려준다. 표와 헤딩은 제외한다."""
        buf, start = [], None
        for no, _, plain, _ in self.lines:
            s = plain.strip()
            if not s or s.startswith("#") or s.startswith("|"):
                if buf:
                    yield start, buf
                buf, start = [], None
                continue
            if start is None:
                start = no
            buf.append((no, plain))
        if buf:
            yield start, buf


def strip_code(line):
    return re.sub(r"`[^`]*`", "", line)


def strip_link_targets(line):
    """링크 대상 URL과 맨 URL을 지운다. 링크 텍스트는 남긴다."""
    line = re.sub(r"\]\([^)]*\)", "]", line)
    return re.sub(r"https?://\S+", "", line)


def md_files(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if not d.startswith(".") and d != "node_modules")
        for f in sorted(fn):
            if f.endswith(".md"):
                yield os.path.join(dp, f)


# ---------------------------------------------------------------------------
# 검사 컨텍스트
# ---------------------------------------------------------------------------


class Context:
    def __init__(self, registry, profile_id, repo_root, siblings_dir, diff_lines):
        self.reg = registry
        self.profile_id = profile_id
        self.profile = registry["profiles"][profile_id]
        self.root = repo_root
        self.repo_name = self.profile["repo"].split("/")[1]
        self.rule_docs = set(registry.get("rule_documents", []))
        self.diff_lines = diff_lines  # None이면 변경된 줄 전용 규칙을 건너뜀
        self.roots = {}
        if repo_root:
            self.roots[self.repo_name] = repo_root
        for pid, p in registry["profiles"].items():
            name = p["repo"].split("/")[1]
            cand = os.path.join(siblings_dir, name) if siblings_dir else None
            if name not in self.roots and cand and os.path.isdir(cand):
                self.roots[name] = cand
        self.findings = []
        self.notes = []
        self.link_checked = 0
        self.link_skipped = 0
        self._anchor_cache = {}

    def add(self, rule, doc, no, msg):
        self.findings.append((rule["level"], rule["id"], f"{doc.rel}:{no}" if doc else "-", msg))

    def anchors(self, path):
        if path not in self._anchor_cache:
            found, count = set(), {}
            with open(path, encoding="utf-8") as f:
                text = f.read()
            in_fence = False
            for line in text.split("\n"):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                m = HEADING_RE.match(line)
                if m:
                    base = slug(m.group(2))
                    n = count.get(base, 0)
                    count[base] = n + 1
                    found.add(base if n == 0 else f"{base}-{n}")
            found.update(re.findall(r'<a\s+(?:name|id)="([^"]+)"', text))
            self._anchor_cache[path] = found
        return self._anchor_cache[path]


def slug(heading):
    """GitHub 앵커 규칙: 소문자화, 문자, 숫자, 한글, 하이픈, 밑줄, 공백 외 제거, 공백은 하이픈."""
    h = re.sub(r"<[^>]+>", "", heading).strip().lower()
    h = re.sub(r"[^0-9a-z가-힣ㄱ-ㅎㅏ-ㅣ①-⑳\-_ ]", "", h)
    return h.replace(" ", "-")


def in_scope(rule, profile_id):
    return rule["scope"] == ["all"] or profile_id in rule["scope"]


def allowed(rule, text):
    return any(re.search(a, text) for a in rule.get("allow", []))


# ---------------------------------------------------------------------------
# 줄 단위 정규식 검사
# ---------------------------------------------------------------------------


def line_regex(pattern_of, prepare=None, skip_rule_docs=True):
    """줄마다 정규식을 적용하는 검사를 만든다. allow에 걸리는 부분은 지운 뒤 판정한다."""

    def check(ctx, rule, doc):
        if skip_rule_docs and doc.base in ctx.rule_docs:
            return
        pattern = re.compile(pattern_of(rule))
        for no, line, plain, h2 in doc.lines:
            t = prepare(plain, ctx, rule) if prepare else plain
            for a in rule.get("allow", []):
                t = re.sub(a, " ", t)
            m = pattern.search(t)
            if m:
                ctx.add(rule, doc, no, f"{rule['title']}: {snippet(t, m)}")

    return check


def snippet(text, m, width=24):
    s = max(0, m.start() - width)
    e = min(len(text), m.end() + width)
    return ("…" if s else "") + text[s:e].strip() + ("…" if e < len(text) else "")


def prep_urls(plain, ctx, rule):
    return strip_link_targets(plain)


def prep_dash(plain, ctx, rule):
    t = plain
    h1 = ctx.profile.get("h1_pattern", "")
    if "—" in h1 and re.match(r"^# [A-Z]?\d+ — ", t):
        t = re.sub(r"^# [A-Z]?\d+ — ", "# ", t)
    # 외부 자료 링크 텍스트(원래 제목과 출처 표기)는 예외
    t = LINK_RE.sub(
        lambda m: "" if m.group(2).startswith("http") and f"github.com/{OWNER}/" not in m.group(2) else m.group(1),
        t,
    )
    return strip_link_targets(t)


def pat_dash_join(rule):
    # 값 없음을 뜻하는 단독 셀(| — |)은 대시 한쪽에 내용이 없어 걸리지 않는다.
    return r"[^\s|]\s*—\s*[^\s|]"


def prep_hyphen(plain, ctx, rule):
    t = re.sub(r"^\s*(?:>\s*)*(?:[-*+]|\d+\.)\s+", "", plain)  # 인용 블록과 목록 기호
    t = re.sub(r"\|\s*-+\s*(?=\|)", "|", t)  # 값 없음 셀
    return strip_link_targets(t)


def prep_range(plain, ctx, rule):
    t = strip_link_targets(plain)
    t = re.sub(r"\b(19|20)\d{2}-\d{2}(-\d{2})?\b", " ", t)  # 날짜(연-월, 연-월-일)
    t = re.sub(r"[\w.]*[A-Za-z][\w.]*-[\w.-]+", " ", t)  # 영문이 섞인 식별자와 제품명
    return t


# ---------------------------------------------------------------------------
# 개별 검사
# ---------------------------------------------------------------------------


def check_h1(ctx, rule, doc):
    files = ctx.profile.get("h1_files")
    pat = ctx.profile.get("h1_pattern")
    if not files or not pat or not re.search(files, doc.rel):
        return
    for no, line, _, _ in doc.lines:
        if line.startswith("# "):
            if not re.match(pat, line):
                ctx.add(rule, doc, no, f"H1 형식은 {ctx.profile['h1_example']}")
            return
    ctx.add(rule, doc, 1, "H1 없음")


def doc_number(doc):
    m = re.match(r"([A-Z]?\d+)-", doc.base)
    if not m or not re.search(r"(^|/)(docs|appendix)/", doc.rel):
        return None
    n = m.group(1)
    return n if n[0].isalpha() else str(int(n))


def heading_iter(doc):
    for no, line, _, _ in doc.lines:
        m = HEADING_RE.match(line)
        if m:
            yield no, len(m.group(1)), m.group(2)


def is_meta(rule_or_ctx_titles, title):
    t = re.sub(r"^[A-Z]?\d+(\.\d+)*\s+", "", title)
    return any(re.fullmatch(p, t) for p in rule_or_ctx_titles)


def check_heading_number(ctx, rule, doc):
    num = doc_number(doc)
    if num is None or num.startswith("E"):
        return
    meta = ctx.reg.get("meta_titles", [])
    for no, lvl, title in heading_iter(doc):
        if allowed(rule, title):
            continue
        if lvl == 2 and not is_meta(meta, title) and not re.match(rf"{re.escape(num)}\.\d+\s", title):
            ctx.add(rule, doc, no, f"H2는 '{num}.M 제목' 형식: {title}")
        elif lvl == 3 and re.match(r"\d+(\.\d+)+\s", title) and not re.match(rf"{re.escape(num)}\.\d+\.\d+\s", title):
            ctx.add(rule, doc, no, f"H3 번호는 '{num}.M.K' 형식: {title}")
        elif lvl >= 4 and re.match(r"[A-Z]?\d+(\.\d+)+\s", title):
            ctx.add(rule, doc, no, f"H4 이하는 번호를 붙이지 않음: {title}")


def check_meta_unnumbered(ctx, rule, doc):
    meta = ctx.reg.get("meta_titles", [])
    for no, lvl, title in heading_iter(doc):
        if lvl >= 2 and re.match(r"[A-Z]?\d+(\.\d+)+\s", title) and is_meta(meta, title):
            ctx.add(rule, doc, no, f"메타 섹션은 번호를 붙이지 않음: {title}")


def check_circled_heading(ctx, rule, doc):
    for no, lvl, title in heading_iter(doc):
        if lvl >= 2 and re.search(r"[①-⑳]", title) and not allowed(rule, title):
            ctx.add(rule, doc, no, f"본문 헤딩에 원숫자: {title}")


def check_file_layout(ctx, rule, doc):
    rel = doc.rel
    if doc.base == "README.md" or allowed(rule, rel):
        return
    if "/docs/" in f"/{rel}" and not re.search(r"(^|/)docs/(\d{2}|E0)-[a-z0-9-]+\.md$", rel):
        ctx.add(rule, doc, 1, "docs/ 파일 이름은 NN-slug.md 또는 E0-slug.md")
    elif "/appendix/" in f"/{rel}" and not re.search(r"(^|/)appendix/A\d+-[a-z0-9-]+\.md$", rel):
        ctx.add(rule, doc, 1, "appendix/ 파일 이름은 AN-slug.md")


def check_label(ctx, rule, doc):
    if doc.base in ctx.rule_docs:
        return
    pat = re.compile(rule["pattern"])
    for no, line, plain, _ in doc.lines:
        m = pat.search(plain)
        if m and not allowed(rule, plain):
            ctx.add(rule, doc, no, f"라벨은 '**라벨.** 본문' 형식: {snippet(plain, m)}")


def check_no_form(ctx, rule, doc):
    if doc.base in ctx.rule_docs or allowed(rule, doc.rel):
        return
    rows, start = [], None

    def flush():
        body = [r for r in rows[2:]] if len(rows) > 2 else []
        cells = [c for r in body for c in r]
        if len(body) >= 3 and cells and sum(1 for c in cells if not c) / len(cells) >= 0.5:
            ctx.add(rule, doc, start, f"빈 셀이 절반 이상인 표(행 {len(body)}개)")

    for no, line, plain, _ in doc.lines:
        s = plain.strip()
        if line.strip().startswith("|"):
            if not rows:
                start = no
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        if rows:
            flush()
            rows = []
        if re.search(r"_{4,}", s) or re.match(r"^[-*+]\s+\[ \]", s):
            ctx.add(rule, doc, no, f"빈칸이나 체크박스: {s[:40]}")
    if rows:
        flush()


def check_link_target(ctx, rule, doc):
    for no, line, _, _ in doc.lines:
        for m in LINK_RE.finditer(line):
            url = m.group(2)
            gm = GH_RE.match(url)
            if gm:
                repo, ref, sub, anc = gm.groups()
                if ref and ref != "main":
                    continue  # 태그와 커밋 고정 링크는 검사하지 않음
                if repo not in ctx.roots:
                    ctx.link_skipped += 1
                    continue
                target = ctx.roots[repo] + (urllib.parse.unquote(sub) if sub else "")
                target = target.rstrip("/") or ctx.roots[repo]
            elif re.match(r"^[a-z][a-z0-9+.-]*:", url):
                continue  # 외부 URL과 mailto는 검사하지 않음
            else:
                part, _, anc = url.partition("#")
                target = doc.path if not part else os.path.normpath(
                    os.path.join(os.path.dirname(doc.path), urllib.parse.unquote(part))
                )
            ctx.link_checked += 1
            err = link_error(ctx, target, anc)
            if err:
                ctx.add(rule, doc, no, f"{url} ({err})")


def link_error(ctx, path, anchor):
    if not os.path.exists(path):
        return "대상 파일 없음"
    if os.path.isdir(path):
        if not anchor:
            return None
        path = os.path.join(path, "README.md")
        if not os.path.exists(path):
            return "앵커가 있으나 폴더에 README.md 없음"
    if anchor and path.endswith(".md"):
        a = urllib.parse.unquote(anchor)
        if a not in ctx.anchors(path):
            return f"앵커 없음 #{a}"
    return None


def check_link_text(ctx, rule, doc):
    for no, line, _, _ in doc.lines:
        for m in LINK_RE.finditer(line):
            text, url = m.group(1), m.group(2)
            if re.search(r"(^|/)[A-Z]?\d{2}-[^/]*\.md", url) and re.match(r"^[A-Z]?\d{2}\s*[—:.\-]\s", text):
                ctx.add(rule, doc, no, f"링크 텍스트는 '번호 제목' 형식: [{text}]")


def detect_entries(rule):
    """detect가 없으면 words로 검출 목록을 만든다."""
    if "detect" in rule:
        return rule["detect"]
    return [[re.escape(w), rule["title"]] for w in rule.get("words", [])]


def check_detect_list(ctx, rule, doc):
    """registry의 detect 목록([정규식, 안내])을 줄마다 적용한다."""
    if doc.base in ctx.rule_docs:
        return
    detect = [(re.compile(p), hint) for p, hint in detect_entries(rule)]
    for no, line, plain, h2 in doc.lines:
        t = strip_link_targets(plain)
        for a in rule.get("allow", []):
            t = re.sub(a, " ", t)
        for pat, hint in detect:
            m = pat.search(t)
            if m:
                ctx.add(rule, doc, no, f"{hint}: {snippet(t, m)}")


def check_translationese(ctx, rule, doc):
    if doc.base in ctx.rule_docs:
        return
    pats = [re.compile(p) for p, _ in rule.get("detect", [])]
    need = rule.get("min_per_paragraph", 2)
    for start, lines in doc.paragraphs():
        hits = []
        for no, plain in lines:
            for p in pats:
                hits += [(no, m.group(0)) for m in p.finditer(plain)]
        if len(hits) >= need:
            words = ", ".join(sorted({h[1] for h in hits}))
            ctx.add(rule, doc, hits[0][0], f"한 단락에 번역투 표현 {len(hits)}회({words})")


def check_source(ctx, rule, doc):
    if doc.base in ctx.rule_docs:
        return
    num = re.compile(rule["number_pattern"])
    for start, lines in doc.paragraphs():
        text = " ".join(p for _, p in lines)
        if num.search(text) and "](" not in text and "확인 필요" not in text and "http" not in text:
            m = num.search(text)
            ctx.add(rule, doc, start, f"수치가 있으나 같은 단락에 출처 링크 없음: {snippet(text, m)}")


def skip_file(ctx, rule, doc):
    return doc.base in ctx.rule_docs or any(re.search(a, doc.rel) for a in rule.get("allow_files", []))


def check_not_ga(ctx, rule, doc):
    if skip_file(ctx, rule, doc):
        return
    pat = re.compile("|".join(re.escape(w) for w in rule["words"]))
    for no, line, plain, h2 in doc.lines:
        if any(re.search(s, h2) for s in rule.get("allow_sections", [])):
            continue
        t = strip_link_targets(plain)
        m = pat.search(t)
        if m and not allowed(rule, t):
            ctx.add(rule, doc, no, f"GA 전 기능 표현: {snippet(t, m)}")


def check_baseline(ctx, rule, doc):
    if skip_file(ctx, rule, doc):
        return
    decl = ctx.reg["baseline"]["declaration"]
    old = re.compile(rule["old_version_pattern"])
    for no, line, plain, h2 in doc.lines:
        if any(re.search(s, h2) for s in rule.get("allow_sections", [])):
            continue
        t = strip_link_targets(plain)
        if "기준선" in t and re.search(r"VCF\s?\d", t) and decl not in t and not allowed(rule, t):
            ctx.add(rule, doc, no, f"기준선 선언 문구는 '{decl}': {t.strip()[:60]}")
            continue
        m = old.search(t)
        if m and not allowed(rule, t):
            ctx.add(rule, doc, no, f"이전 버전 표기, 이력 문맥인지 확인: {snippet(t, m)}")


def check_anonymize(ctx, rule, doc):
    names = [n.strip() for n in re.split(r"[,\n]", os.environ.get("CUSTOMER_NAMES", "")) if n.strip()]
    if not names:
        return
    pat = re.compile("|".join(re.escape(n) for n in names))
    for no, line, plain, _ in doc.lines:
        if pat.search(plain):
            ctx.add(rule, doc, no, "고객사 이름이 포함됨")


def check_changed_only(inner):
    def check(ctx, rule, doc):
        if ctx.diff_lines is None:
            return
        changed = ctx.diff_lines.get(doc.rel, set())
        if not changed:
            return
        before = len(ctx.findings)
        inner(ctx, rule, doc)
        kept = [f for f in ctx.findings[before:] if int(f[2].rsplit(":", 1)[1]) in changed]
        ctx.findings[before:] = kept

    return check


CHECKS = {
    "SYM-TILDE": line_regex(lambda r: r["pattern"], prep_urls),
    "SYM-EMOJI": line_regex(lambda r: r["pattern"]),
    "SYM-MIDDOT": line_regex(lambda r: r["pattern"]),
    "SYM-SECTION": line_regex(lambda r: r["pattern"]),
    "SYM-RANGE": line_regex(lambda r: r["pattern"], prep_range),
    "DASH-JOIN": line_regex(pat_dash_join, prep_dash),
    "DASH-HYPHEN-JOIN": line_regex(lambda r: r["pattern"], prep_hyphen),
    "STR-H1": check_h1,
    "STR-HEADING-NUMBER": check_heading_number,
    "STR-META-UNNUMBERED": check_meta_unnumbered,
    "STR-CIRCLED-HEADING": check_circled_heading,
    "STR-FILE-LAYOUT": check_file_layout,
    "STR-LABEL": check_label,
    "STR-NO-FORM": check_no_form,
    "STR-CALC-TABLE-TERM": check_detect_list,
    "LINK-TARGET": check_link_target,
    "LINK-TEXT": check_link_text,
    "WORD-ONE-SYLLABLE": check_detect_list,
    "WORD-GE-DOEDA": check_detect_list,
    "WORD-SPATIAL": check_detect_list,
    "WORD-TRANSLATIONESE": check_translationese,
    "WORD-CLICHE": check_detect_list,
    "WORD-QUOTED-HEADLINE": line_regex(lambda r: r["pattern"]),
    "CNT-SOURCE": check_source,
    "CNT-NOT-GA": check_not_ga,
    "CNT-BASELINE": check_baseline,
    "CNT-VENDOR-NEUTRAL": line_regex(lambda r: r["pattern"], prep_urls),
    "CNT-ANONYMIZE": check_anonymize,
    "PRS-PAREN-CONFLATE": check_changed_only(line_regex(lambda r: r["pattern"], prep_urls)),
}
# 저장소 설명(About)에 적용하는 규칙. META-REPO-DESCRIPTION의 applies 목록과 함께 사용한다.
DESCRIPTION_PREP = {"DASH-JOIN": prep_dash, "SYM-TILDE": prep_urls}


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------


def load_registry():
    with open(REGISTRY, "rb") as f:
        return tomllib.load(f)


def git_diff_lines(repo, base):
    """--diff-base 대비 변경된 줄 번호를 파일별로 돌려준다."""
    out = subprocess.run(
        ["git", "-C", repo, "diff", "-U0", f"{base}...HEAD", "--", "*.md"],
        capture_output=True, text=True, check=True,
    ).stdout
    result, cur = defaultdict(set), None
    for line in out.split("\n"):
        if line.startswith("+++ b/"):
            cur = line[6:]
        elif line.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            start, count = int(m.group(1)), int(m.group(2) or 1)
            result[cur].update(range(start, start + count))
    return result


def apply_waivers(reg, ctx):
    waivers = [w for w in reg.get("waivers", []) if w["repo"] == ctx.repo_name]
    kept, used = [], Counter()
    for f in ctx.findings:
        level, rid, loc, msg = f
        hit = None
        for i, w in enumerate(waivers):
            if w["rule"] == rid and loc.rsplit(":", 1)[0] == w["file"] and w["contains"] in msg:
                hit = i
                break
        if hit is None:
            kept.append(f)
        else:
            used[hit] += 1
    ctx.findings = kept
    for i, w in enumerate(waivers):
        if not used[i]:
            ctx.notes.append(f"사용되지 않는 예외 등록: {w['rule']} {w['file']} '{w['contains']}'")
    return sum(used.values())


def run_description(reg, ctx, text):
    meta = next(r for r in reg["rules"] if r["id"] == "META-REPO-DESCRIPTION")
    by_id = {r["id"]: r for r in reg["rules"]}
    for rid in meta["applies"]:
        rule = by_id[rid]
        t = DESCRIPTION_PREP.get(rid, lambda s, c, r: s)(text, ctx, rule)
        if "detect" in rule or "words" in rule:
            for p, hint in detect_entries(rule):
                m = re.search(p, t)
                if m:
                    ctx.findings.append(("warn", "META-REPO-DESCRIPTION", "저장소 설명", f"{rid} {hint}: {snippet(t, m)}"))
        else:
            pat = pat_dash_join(rule) if rid == "DASH-JOIN" else rule["pattern"]
            m = re.search(pat, t)
            if m:
                ctx.findings.append(("warn", "META-REPO-DESCRIPTION", "저장소 설명", f"{rid} {rule['title']}: {snippet(t, m)}"))


def verify(reg, ctx, only=None, description=None):
    """프로필에 해당하는 규칙을 실행하고 예외 등록을 적용한다. (ctx, 예외로 제외한 건수)를 돌려준다."""
    rules = [r for r in reg["rules"] if r["level"] != "review" and in_scope(r, ctx.profile_id)]
    if only:
        rules = [r for r in rules if r["id"] in only]
    if ctx.root:
        docs = [Doc(p, os.path.relpath(p, ctx.root)) for p in md_files(ctx.root)]
        for rule in rules:
            fn = CHECKS.get(rule["id"])
            if fn is None:
                continue
            for doc in docs:
                fn(ctx, rule, doc)
        if any(r["id"] == "CNT-ANONYMIZE" for r in rules) and not os.environ.get("CUSTOMER_NAMES"):
            ctx.notes.append("CUSTOMER_NAMES가 없어 CNT-ANONYMIZE를 건너뜀")
        if any(r["id"] == "PRS-PAREN-CONFLATE" for r in rules) and ctx.diff_lines is None:
            ctx.notes.append("--diff-base가 없어 PRS-PAREN-CONFLATE를 건너뜀")
    if description is not None and (not only or "META-REPO-DESCRIPTION" in only):
        run_description(reg, ctx, description)
    waived = apply_waivers(reg, ctx) if ctx.root else 0
    return ctx, waived


def detect_profile(reg, repo_root):
    name = os.path.basename(os.path.abspath(repo_root))
    for pid, p in reg["profiles"].items():
        if p["repo"].split("/")[1] == name:
            return pid
    return None


def list_rules(reg):
    for r in reg["rules"]:
        if r["level"] == "review":
            state = "리뷰(검사 대상 아님)"
        elif r["id"] == "META-REPO-DESCRIPTION":
            state = "구현(--description)"
        elif r["id"] in CHECKS:
            state = "구현"
        else:
            state = "미구현"
        print(f"{r['id']:24} {r['level']:6} {state}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", help="검사할 저장소 경로")
    ap.add_argument("--profile", help="저장소 프로필(기본: 저장소 폴더 이름으로 판단)")
    ap.add_argument("--siblings", help="형제 저장소 clone 위치(기본: --repo의 상위 폴더)")
    ap.add_argument("--level", choices=["error", "warn"], default="warn", help="출력할 최저 수준(기본: warn)")
    ap.add_argument("--rule", action="append", help="실행할 규칙 ID(여러 번 지정 가능)")
    ap.add_argument("--diff-base", help="변경된 줄 전용 규칙의 비교 기준(예: origin/main)")
    ap.add_argument("--description", help="저장소 설명(About) 문자열")
    ap.add_argument("--format", choices=["text", "github"], default="text", help="github는 Actions 주석 형식")
    ap.add_argument("--list", action="store_true", help="규칙별 구현 상태 출력")
    args = ap.parse_args()

    reg = load_registry()
    if args.list:
        list_rules(reg)
        return 0
    if not args.repo and args.description is None:
        ap.error("--repo 또는 --description이 필요합니다")

    repo = os.path.abspath(args.repo) if args.repo else None
    profile_id = args.profile or (detect_profile(reg, repo) if repo else None)
    if profile_id not in reg["profiles"]:
        ap.error(f"프로필을 정할 수 없습니다: {profile_id}. --profile로 지정하십시오.")
    siblings = os.path.abspath(args.siblings) if args.siblings else (os.path.dirname(repo) if repo else None)
    diff_lines = git_diff_lines(repo, args.diff_base) if args.diff_base and repo else None
    ctx = Context(reg, profile_id, repo, siblings, diff_lines)

    if args.rule:
        unknown = set(args.rule) - {r["id"] for r in reg["rules"]}
        if unknown:
            ap.error(f"알 수 없는 규칙: {', '.join(sorted(unknown))}")
    ctx, waived = verify(reg, ctx, args.rule, args.description)
    shown = [f for f in ctx.findings if LEVEL_ORDER[f[0]] <= LEVEL_ORDER[args.level]]
    shown.sort(key=lambda f: (LEVEL_ORDER[f[0]], f[1], f[2]))
    for level, rid, loc, msg in shown:
        if args.format == "github" and ":" in loc:
            file, line = loc.rsplit(":", 1)
            kind = "error" if level == "error" else "warning"
            print(f"::{kind} file={file},line={line},title={rid}::{msg}")
        else:
            print(f"{'오류' if level == 'error' else '경고'}  {rid:22} {loc}  {msg}")

    errors = Counter(f[1] for f in ctx.findings if f[0] == "error")
    warns = Counter(f[1] for f in ctx.findings if f[0] == "warn")
    print(f"\n프로필: {profile_id}")
    if repo:
        print(f"링크 {ctx.link_checked}개 검사, 형제 저장소가 없어 건너뜀 {ctx.link_skipped}개 (확인한 저장소: {', '.join(sorted(ctx.roots))})")
    if waived:
        print(f"예외 등록으로 제외: {waived}건")
    for n in ctx.notes:
        print(f"참고: {n}")
    print("오류: " + (", ".join(f"{k} {v}" for k, v in sorted(errors.items())) or "0"))
    print("경고: " + (", ".join(f"{k} {v}" for k, v in sorted(warns.items())) or "0"))
    print("결과: " + ("통과" if not errors else f"실패(오류 {sum(errors.values())}건)"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
