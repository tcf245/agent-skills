import json
import unittest

import search_quark as s


def cand(url, title, q=0, valid=None, pub=None):
    return {"title": title, "url": url, "quality_score": q, "is_tc": False,
            "valid": valid, "pub_date": pub, "source": "t", "snippet": ""}


class SortCandidates(unittest.TestCase):
    def test_valid_then_jev_then_quality_then_newer_date(self):
        cs = [cand("a", "a", q=3, valid=False), cand("b", "b", q=1, valid=True, pub="2025-01-01"),
              cand("c", "c", q=1, valid=True, pub="2026-01-01"), cand("d", "d", q=0, valid=True)]
        cs[3]["jev_score"] = 2.5
        cs[1]["jev_score"] = cs[2]["jev_score"] = 2.0
        self.assertEqual([c["url"] for c in s.sort_candidates(cs)], ["d", "c", "b", "a"])

    def test_missing_dates_and_scores_do_not_crash(self):
        cs = [cand("a", "a"), cand("b", "b", pub="2026-01-01")]
        self.assertEqual(len(s.sort_candidates(cs)), 2)


class JevRanking(unittest.TestCase):
    def test_scores_attached_from_jev_output(self):
        captured = {}

        def runner(cmd, input, **kw):
            captured["cmd"], captured["input"] = cmd, json.loads(input)
            out = "\n".join(json.dumps(r) for r in [
                {"i": 1, "score": 3.0, "conf": 0.9}, {"i": 0, "score": 0.1, "conf": 0.8}])

            class R:
                returncode, stdout, stderr = 0, out, "jev rank: 2 in"
            return R()
        cs = [cand("a", "沙丘 2021"), cand("b", "沙丘2 4K")]
        s.rank_with_jev(cs, "Dune Part Two 2024, 4K", runner=runner)
        self.assertEqual([c["jev_score"] for c in cs], [0.1, 3.0])
        self.assertIn("Dune Part Two 2024, 4K", " ".join(captured["cmd"]))
        self.assertEqual(captured["input"][1]["title"], "沙丘2 4K")
        self.assertNotIn("url", captured["input"][0])

    def test_jev_failure_leaves_candidates_unscored(self):
        def runner(cmd, input, **kw):
            raise FileNotFoundError("jev")
        cs = [cand("a", "x")]
        s.rank_with_jev(cs, "want", runner=runner)
        self.assertNotIn("jev_score", cs[0])


class ValidationOrder(unittest.TestCase):
    def test_validates_top_jev_matches_and_skips_wrong_titles(self):
        cs = [cand("a", "a", q=3), cand("b", "b", q=0), cand("c", "c", q=0)]
        cs[0]["jev_score"], cs[1]["jev_score"], cs[2]["jev_score"] = 0.2, 2.8, 1.9
        checked = []
        s.validate(cs, check=lambda u: checked.append(u) or True, limit=3, pause=0)
        self.assertEqual(checked, ["b", "c"])
        self.assertFalse(cs[0]["valid"])


class LoadCandidates(unittest.TestCase):
    def test_browser_collected_rows_are_normalized(self):
        rows = [{"title": "沙丘2 4K 杜比视界", "url": "https://pan.quark.cn/s/abc", "snippet": "2024 内封中字"},
                {"title": "无链接条目"}]
        cs = s.normalize_candidates(rows)
        self.assertEqual(len(cs), 1)
        c = cs[0]
        self.assertEqual((c["quality_score"], c["is_tc"], c["valid"], c["source"]), (3, False, None, "external"))
        self.assertEqual(c["snippet"], "2024 内封中字")


if __name__ == "__main__":
    unittest.main()
