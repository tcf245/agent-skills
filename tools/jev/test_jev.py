import io
import json
import unittest

import jev


def fake_call(answers_for):
    """Return a call(state, questions) stub; answers_for(state, questions) -> answers dict."""
    calls = []

    def call(state, questions, model="jev-latest"):
        calls.append((state, questions))
        return {"model": "jev-test", "answers": answers_for(state, questions),
                "usage": {"input_tokens": 100, "output_tokens": 5}}
    call.calls = calls
    return call


class ParseItems(unittest.TestCase):
    def test_json_array(self):
        self.assertEqual(jev.parse_items('[{"a":1},"x"]'), [{"a": 1}, "x"])

    def test_jsonl(self):
        self.assertEqual(jev.parse_items('{"a":1}\n\n{"a":2}\n'), [{"a": 1}, {"a": 2}])

    def test_plain_lines(self):
        self.assertEqual(jev.parse_items("foo bar\n\nbaz\n"), ["foo bar", "baz"])


class Filter(unittest.TestCase):
    def test_keeps_items_above_threshold_sorted_desc(self):
        probs = {"a": 0.9, "b": 0.2, "c": 0.6}
        call = fake_call(lambda s, q: {"q": {"type": "noul", "noul": probs[s["item"]]}})
        out, stats = jev.run_filter(["a", "b", "c"], "is it good?", call=call, threshold=0.5)
        self.assertEqual([(r["i"], r["p"]) for r in out], [(0, 0.9), (2, 0.6)])
        self.assertEqual(stats["n"], 3)
        self.assertEqual(stats["input_tokens"], 300)

    def test_context_is_shared_in_state(self):
        call = fake_call(lambda s, q: {"q": {"type": "noul", "noul": 1.0}})
        jev.run_filter(["a"], "q?", call=call, context="we want 4K")
        state, questions = call.calls[0]
        self.assertEqual(state, {"context": "we want 4K", "item": "a"})
        self.assertEqual(questions["q"]["type"], "noul")


class Rank(unittest.TestCase):
    def test_sorted_by_score_and_top_n(self):
        scores = {"a": 0.4, "b": 2.0, "c": 1.1}
        call = fake_call(lambda s, q: {"q": {"type": "score", "score": scores[s["item"]], "confidence": 0.8}})
        out, _ = jev.run_rank(["a", "b", "c"], "how good?", ["bad", "ok", "great"], call=call, top=2)
        self.assertEqual([r["i"] for r in out], [1, 2])
        self.assertEqual(out[0]["score"], 2.0)
        self.assertEqual(call.calls[0][1]["q"]["criteria"], ["bad", "ok", "great"])


class Classify(unittest.TestCase):
    def test_returns_choice_and_confidence_in_input_order(self):
        labels = {"a": "x", "b": "y"}
        call = fake_call(lambda s, q: {"q": {"type": "choice", "choice": labels[s["item"]], "confidence": 0.7,
                                             "probabilities": {"x": 0.5, "y": 0.5}}})
        out, _ = jev.run_classify(["a", "b"], "which?", {"x": "X things", "y": None}, call=call)
        self.assertEqual([(r["i"], r["choice"]) for r in out], [(0, "x"), (1, "y")])


class Lines(unittest.TestCase):
    def test_windows_numbered_and_hits_with_context(self):
        lines = [f"line {i}" for i in range(10)]

        def answers(state, q):
            # window 1 = lines 0-4 (nothing), window 2 = lines 5-9 (hit on line 7)
            if "L0007" in state["log"]:
                return {"where": {"type": "choice", "choice": "L0007", "confidence": 0.9,
                                  "probabilities": {"L0005": 0.02, "L0007": 0.95, "L0008": 0.03}},
                        "exists": {"type": "noul", "noul": 0.97}}
            return {"where": {"type": "choice", "choice": "L0000", "confidence": 0.1,
                              "probabilities": {"L0000": 0.3}},
                    "exists": {"type": "noul", "noul": 0.02}}
        call = fake_call(answers)
        out, stats = jev.run_lines(lines, "where is the error?", call=call, window=5, around=1)
        self.assertEqual(len(call.calls), 2)
        self.assertEqual(stats["windows_hit"], 1)
        self.assertEqual([r["line"] for r in out], [7])
        self.assertEqual(out[0]["text"], "line 7")
        self.assertEqual(out[0]["context"], ["line 6", "line 7", "line 8"])

    def test_choice_options_capped_at_255(self):
        with self.assertRaises(ValueError):
            jev.run_lines(["x"] * 10, "q", call=fake_call(lambda s, q: {}), window=300)


class Project(unittest.TestCase):
    def test_fields_and_truncation(self):
        self.assertEqual(jev.project({"title": "t", "url": "u", "big": "z"}, ["title", "url"], 100),
                         {"title": "t", "url": "u"})
        self.assertEqual(jev.project("abcdef", None, 3), "abc…")


class Retry(unittest.TestCase):
    def test_retries_on_429_then_succeeds(self):
        attempts = []

        def post(body):
            attempts.append(1)
            if len(attempts) < 3:
                raise jev.Retryable("429")
            return {"answers": {}, "usage": {}}
        self.assertEqual(jev.with_retry(post, {}, sleep=lambda s: None), {"answers": {}, "usage": {}})
        self.assertEqual(len(attempts), 3)


class Unavailability(unittest.TestCase):
    def test_retry_exhaustion_raises_unavailable(self):
        def post(body):
            raise jev.Retryable("529")
        with self.assertRaises(jev.Unavailable):
            jev.with_retry(post, {}, tries=3, sleep=lambda s: None)

    def test_cli_exits_3_when_service_down(self):
        def down(state, questions, model="jev-latest"):
            raise jev.Unavailable("connection refused")
        orig_call, orig_key, orig_stdin = jev.make_call, jev.api_key, jev.sys.stdin
        jev.make_call, jev.api_key = (lambda model, key: down), (lambda: "k")
        jev.sys.stdin = io.StringIO("a\nb\n")
        try:
            with self.assertRaises(SystemExit) as cm:
                jev.main(["filter", "-q", "x?"])
            self.assertEqual(cm.exception.code, 3)
        finally:
            jev.make_call, jev.api_key, jev.sys.stdin = orig_call, orig_key, orig_stdin

    def test_missing_key_is_unavailable(self):
        orig_env = jev.os.environ.pop("TYPESAFE_API_KEY", None)
        orig_run = jev.subprocess.run

        def fail(*a, **k):
            raise jev.subprocess.CalledProcessError(44, "security")
        jev.subprocess.run = fail
        try:
            with self.assertRaises(jev.Unavailable):
                jev.api_key()
        finally:
            jev.subprocess.run = orig_run
            if orig_env:
                jev.os.environ["TYPESAFE_API_KEY"] = orig_env


if __name__ == "__main__":
    unittest.main()
