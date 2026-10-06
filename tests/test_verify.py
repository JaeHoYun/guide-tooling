"""tools/verify.py 회귀 테스트. 실행: python3 -m unittest discover -s tests"""
import copy
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import verify  # noqa: E402

REG = verify.load_registry()


def run(files, profile="vcf-private-ai", only=None, reg=None, diff_lines=None):
    """임시 저장소에 files({경로: 내용})를 만들고 검사 결과 (수준, 규칙, 위치) 목록을 돌려준다."""
    reg = reg or REG
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, reg["profiles"][profile]["repo"].split("/")[1])
        for rel, text in files.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        ctx = verify.Context(reg, profile, root, tmp, diff_lines)
        ctx, _ = verify.verify(reg, ctx, only)
        return [(lv, rid, loc) for lv, rid, loc, _ in ctx.findings]


def ids(findings):
    return sorted({f[1] for f in findings})


class SymbolTests(unittest.TestCase):
    def test_tilde(self):
        self.assertEqual(ids(run({"a.md": "1~3일\n"}, only=["SYM-TILDE"])), ["SYM-TILDE"])

    def test_tilde_in_code_and_url_allowed(self):
        text = "`~/dev` 경로\n\n```\nls ~\n```\n\n[링크](https://example.com/~user)\n"
        self.assertEqual(run({"a.md": text}, only=["SYM-TILDE"]), [])

    def test_emoji_and_middot_and_section(self):
        text = "완료 \U0001F680\n검토·설정\n§3 참조\n"
        self.assertEqual(ids(run({"a.md": text}, only=["SYM-EMOJI", "SYM-MIDDOT", "SYM-SECTION"])),
                         ["SYM-EMOJI", "SYM-MIDDOT", "SYM-SECTION"])

    def test_arrow_and_circled_numbers_allowed(self):
        self.assertEqual(run({"a.md": "① → ②\n"}, only=["SYM-EMOJI"]), [])

    def test_rule_documents_excluded(self):
        self.assertEqual(run({"CLAUDE.md": "검토·설정, 1~3\n"}, only=["SYM-MIDDOT", "SYM-TILDE"]), [])


class DashTests(unittest.TestCase):
    def test_dash_join(self):
        self.assertEqual(ids(run({"a.md": "단편적 해결의 한계 — 동시 해결 필요\n"}, only=["DASH-JOIN"])), ["DASH-JOIN"])

    def test_h1_separator_lone_cell_external_title_allowed(self):
        text = (
            "# 05 — 제목\n\n| 항목 | 값 |\n|---|---|\n| A | — |\n\n"
            "[Release Notes — 3.0](https://techdocs.broadcom.com/x)\n"
        )
        self.assertEqual(run({"docs/05-a.md": text}, only=["DASH-JOIN"]), [])

    def test_h1_separator_not_allowed_for_ax(self):
        found = run({"docs/03-a.md": "# 03 — 제목\n"}, profile="enterprise-ax-methodology", only=["DASH-JOIN"])
        self.assertEqual(ids(found), ["DASH-JOIN"])

    def test_hyphen_join_warn_but_math_and_list_allowed(self):
        self.assertEqual(ids(run({"a.md": "비용 절감 - 라이선스 통합 효과\n"}, only=["DASH-HYPHEN-JOIN"])), ["DASH-HYPHEN-JOIN"])
        text = "- 목록 항목\n> - 인용 목록\n| 거리 | 1 - cosine |\n| A | - |\n"
        self.assertEqual(run({"a.md": text}, only=["DASH-HYPHEN-JOIN"]), [])


class StructureTests(unittest.TestCase):
    def test_h1_per_profile(self):
        self.assertEqual(run({"docs/03-a.md": "# 03 — 제목\n"}, only=["STR-H1"]), [])
        self.assertEqual(ids(run({"docs/03-a.md": "# 03. 제목\n"}, only=["STR-H1"])), ["STR-H1"])
        self.assertEqual(run({"docs/03-a.md": "# 03. 제목\n"}, profile="enterprise-ax-methodology", only=["STR-H1"]), [])

    def test_heading_number(self):
        text = "# 03 — 제목\n\n## 3.1 개요\n\n### 3.1.1 세부\n\n#### 항목\n\n## 참고 출처\n"
        self.assertEqual(run({"docs/03-a.md": text}, only=["STR-HEADING-NUMBER", "STR-META-UNNUMBERED"]), [])
        bad = "# 03 — 제목\n\n## 개요\n\n#### 3.1.1.1 항목\n\n## 3.9 참고 출처\n"
        self.assertEqual(ids(run({"docs/03-a.md": bad}, only=["STR-HEADING-NUMBER", "STR-META-UNNUMBERED"])),
                         ["STR-HEADING-NUMBER", "STR-META-UNNUMBERED"])

    def test_circled_heading_cross_reference_allowed(self):
        self.assertEqual(run({"docs/07-a.md": "## 7.2 ③ 관측성 스택 연계\n"}, only=["STR-CIRCLED-HEADING"]), [])
        self.assertEqual(ids(run({"docs/07-a.md": "## 7.2 ① 개요\n"}, only=["STR-CIRCLED-HEADING"])), ["STR-CIRCLED-HEADING"])

    def test_no_form_ignores_code_only_cells(self):
        code_table = "| 필드 | 예시 |\n|---|---|\n| `a` | `x` |\n| `b` | `y` |\n| `c` | `z` |\n"
        self.assertEqual(run({"a.md": code_table}, only=["STR-NO-FORM"]), [])
        blank_table = "| 항목 | 값 |\n|---|---|\n| A |  |\n| B |  |\n| C |  |\n"
        self.assertEqual(ids(run({"a.md": blank_table}, only=["STR-NO-FORM"])), ["STR-NO-FORM"])

    def test_label(self):
        self.assertEqual(ids(run({"a.md": "**배경**: 본문\n"}, only=["STR-LABEL"])), ["STR-LABEL"])
        self.assertEqual(run({"a.md": "**배경.** 본문\n"}, only=["STR-LABEL"]), [])


class LinkTests(unittest.TestCase):
    def test_relative_link_and_anchor(self):
        files = {"docs/01-a.md": "## 1.1 개요\n", "docs/02-b.md": "[01 개요](01-a.md#11-개요)\n[없음](01-a.md#없는-앵커)\n"}
        found = run(files, only=["LINK-TARGET"])
        self.assertEqual([f[2] for f in found], ["docs/02-b.md:2"])


class WordTests(unittest.TestCase):
    def test_one_syllable(self):
        self.assertEqual(ids(run({"a.md": "| 비용 | 이전 비용이 큼 |\n"}, only=["WORD-ONE-SYLLABLE"])), ["WORD-ONE-SYLLABLE"])
        allowed = "- 토큰을 회전해야 함\n결과를 적어 둡니다.\n여지를 둡니다.\n읽기/쓰기 성능\n"
        self.assertEqual(run({"a.md": allowed}, only=["WORD-ONE-SYLLABLE"]), [])

    def test_spatial_and_exceptions(self):
        self.assertEqual(ids(run({"a.md": "PAIS 위에서 실행합니다.\n"}, only=["WORD-SPATIAL"])), ["WORD-SPATIAL"])
        allowed = "우선순위에서 밀립니다.\n위에서 설명한 대로\n되돌리기 어려운 결정\n병목이 생깁니다.\n"
        self.assertEqual(run({"a.md": allowed}, only=["WORD-SPATIAL"]), [])

    def test_translationese_needs_repetition(self):
        self.assertEqual(run({"a.md": "성능에 대한 설명입니다.\n"}, only=["WORD-TRANSLATIONESE"]), [])
        text = "성능에 대한 설명과 비용에 대한 설명을 API를 통해 제공합니다.\n"
        self.assertEqual(ids(run({"a.md": text}, only=["WORD-TRANSLATIONESE"])), ["WORD-TRANSLATIONESE"])


class ContentTests(unittest.TestCase):
    def test_anonymize_uses_environment(self):
        os.environ["CUSTOMER_NAMES"] = "가상고객사"
        try:
            self.assertEqual(ids(run({"a.md": "가상고객사 사례\n"}, only=["CNT-ANONYMIZE"])), ["CNT-ANONYMIZE"])
        finally:
            del os.environ["CUSTOMER_NAMES"]
        self.assertEqual(run({"a.md": "가상고객사 사례\n"}, only=["CNT-ANONYMIZE"]), [])

    def test_vendor_neutral_only_ax(self):
        self.assertEqual(ids(run({"a.md": "VCF 9.1 기준\n"}, profile="enterprise-ax-methodology",
                                 only=["CNT-VENDOR-NEUTRAL"])), ["CNT-VENDOR-NEUTRAL"])
        self.assertEqual(run({"a.md": "VCF 9.1 기준\n"}, only=["CNT-VENDOR-NEUTRAL"]), [])

    def test_paren_conflate_only_on_changed_lines(self):
        text = "가중치(파라미터)를 조정합니다.\n"
        self.assertEqual(run({"a.md": text}, only=["PRS-PAREN-CONFLATE"]), [])
        found = run({"a.md": text}, only=["PRS-PAREN-CONFLATE"], diff_lines={"a.md": {1}})
        self.assertEqual(ids(found), ["PRS-PAREN-CONFLATE"])


class ChangedLineTests(unittest.TestCase):
    def test_in_changed_lines(self):
        diff = {"a.md": {2}}
        self.assertTrue(verify.in_changed_lines(("warn", "X", "a.md:2", ""), diff))
        self.assertFalse(verify.in_changed_lines(("warn", "X", "a.md:1", ""), diff))
        self.assertFalse(verify.in_changed_lines(("warn", "X", "b.md:2", ""), diff))
        self.assertTrue(verify.in_changed_lines(("warn", "X", "저장소 설명", ""), diff))


class WaiverTests(unittest.TestCase):
    def test_waiver_suppresses_finding(self):
        reg = copy.deepcopy(REG)
        reg["waivers"] = [{"rule": "SYM-TILDE", "repo": "vcf-private-ai", "file": "a.md",
                           "contains": "1~3", "reason": "테스트"}]
        self.assertEqual(run({"a.md": "1~3일\n"}, only=["SYM-TILDE"], reg=reg), [])


class RegistryTests(unittest.TestCase):
    def test_every_checked_rule_is_implemented(self):
        for r in REG["rules"]:
            if r["level"] != "review" and r["id"] != "META-REPO-DESCRIPTION":
                self.assertIn(r["id"], verify.CHECKS, r["id"])


import render_claude_md as rcm  # noqa: E402


class GeneratedBlockTests(unittest.TestCase):
    def make_repo(self, tmp, profile="vcf-private-ai"):
        root = os.path.join(tmp, REG["profiles"][profile]["repo"].split("/")[1])
        os.makedirs(root)
        names = rcm.blocks_for(REG["profiles"][profile])
        files = {}
        for name in names:
            fname = rcm.BLOCKS[name][0]
            files.setdefault(fname, "# 제목\n\n직접 작성한 설명\n\n")
            files[fname] += f"<!-- guide-tooling:begin {name} -->\n<!-- guide-tooling:end {name} sha256=000000000000 -->\n\n"
        for fname, text in files.items():
            with open(os.path.join(root, fname), "w", encoding="utf-8") as f:
                f.write(text)
        return root

    def test_every_profile_renders(self):
        for pid, p in REG["profiles"].items():
            for name in rcm.blocks_for(p):
                body = rcm.render_block(REG, pid, name)
                self.assertNotIn("{{", body)
                self.assertTrue(body.endswith("\n"))

    def test_update_then_ok_and_handwritten_part_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            rcm.update(REG, "vcf-private-ai", root)
            self.assertEqual({s[2] for s in rcm.status(REG, "vcf-private-ai", root)}, {"ok"})
            with open(os.path.join(root, "CLAUDE.md"), encoding="utf-8") as f:
                self.assertIn("직접 작성한 설명", f.read())

    def test_edited_is_error_and_stale_is_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            rcm.update(REG, "vcf-private-ai", root)
            path = os.path.join(root, "CLAUDE.md")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.replace("## 문장 규칙", "## 문장 규칙 수정", 1))
            ctx = verify.Context(REG, "vcf-private-ai", root, tmp, None)
            ctx, _ = verify.verify(REG, ctx, ["STR-GENERATED-SYNC"])
            self.assertEqual([f[0] for f in ctx.findings], ["error"])

            reg = copy.deepcopy(REG)
            reg["baseline"]["pais_ga"] = "2099-01-01"
            rcm.update(REG, "vcf-private-ai", root)
            ctx = verify.Context(reg, "vcf-private-ai", root, tmp, None)
            ctx, _ = verify.verify(reg, ctx, ["STR-GENERATED-SYNC"])
            self.assertEqual([f[0] for f in ctx.findings], ["warn"])

    def test_crlf_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp, "JaeHoYun")
            path = os.path.join(root, "CLAUDE.md")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(text.replace("\n", "\r\n"))
            rcm.update(REG, "JaeHoYun", root)
            with open(path, encoding="utf-8", newline="") as f:
                raw = f.read()
            self.assertNotIn("\n", raw.replace("\r\n", ""))
            self.assertEqual({s[2] for s in rcm.status(REG, "JaeHoYun", root)}, {"ok"})


if __name__ == "__main__":
    unittest.main()
