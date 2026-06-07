# JLPT N2 Coach Workflow Reference

Use this reference when processing mock tests, updating the wiki, calculating accuracy, or generating drills.

## Wiki Pages

Primary pages:

| Page | Role |
|---|---|
| `wiki/records/YYYY-MM-DD JLPT N2 Mock Test Review.md` | One dated test session, score, diagnosis, source links |
| `wiki/concepts/JLPT N2 Error Bank.md` | Active wrong-answer and knowledge-point bank |
| `wiki/concepts/JLPT N2 Exam Strategy.md` | Current strategy to reach 50%+ |
| `wiki/concepts/Japanese N2 Grammar.md` | Grammar reference and contrast buckets |
| `raw/YYYY-MM-DD JLPT N2 Mock Test Photos.md` | Raw source note for original images |
| `raw/YYYY-MM-DD JLPT N2 Mock Test OCR.md` | Raw OCR output and quality notes |

Always update `index.md` and `log.md` after creating new pages.

## Record Page Template

```markdown
---
title: YYYY-MM-DD JLPT N2 Mock Test Review
tags:
  - record
  - japanese
  - jlpt
  - n2
  - mock-test
  - language-learning
created: YYYY-MM-DD
status: active
source: "[[YYYY-MM-DD JLPT N2 Mock Test Photos]]"
---

# YYYY-MM-DD JLPT N2 Mock Test Review

## Source

- Raw photo set:
- OCR pass:
- Answer key:

## Score Baseline

| Item | Value |
|---|---:|
| Total questions |  |
| Correct |  |
| Wrong |  |
| Accuracy |  |
| Delta vs previous test |  |
| Gap to 50% |  |

## Diagnosis

| Weakness | Evidence | Training target |
|---|---|---|

## High-Priority Wrong Items

| No. | Correct phrase | Why it matters |
|---|---|---|

## Next Drill

```

## Error Bank Row Schema

```markdown
| Date | No. | Section | Prompt | Correct | Chosen | Error type | Fix phrase | Next review |
|---|---|---|---|---|---|---|---|---|
```

Recommended `Error type` values:

- `reading`
- `spelling`
- `collocation`
- `grammar-connector`
- `reading-detail`
- `reading-purpose`
- `reading-main-idea`
- `strategy`

## OCR Commands

Basic:

```bash
tesseract input.jpg output -l jpn+eng --psm 6
```

Try alternatives when quality is bad:

```bash
tesseract input.jpg output-psm4 -l jpn+eng --psm 4
tesseract input.jpg output-psm11 -l jpn+eng --psm 11
```

Rotate sideways pages:

```bash
sips -r 90 input.jpg --out rotated-r90.jpg
sips -r 270 input.jpg --out rotated-r270.jpg
```

Quality rules:

- Page 1 of the first test was low quality because of perspective and handwriting.
- Two-page spreads should be split or photographed one page at a time.
- OCR text is raw evidence only; manually verify before marking correctness.

## Accuracy Math

Use exact counts when available:

```text
accuracy_percent = correct / total * 100
gap_to_50_correct = ceil(total * 0.50) - correct
```

For 54 questions:

| Correct | Accuracy |
|---:|---:|
| 16 | 29.6% |
| 22 | 40.7% |
| 27 | 50.0% |

Eric's first confirmed baseline is under 30%, so fewer than 16 correct out of 54.

## Study Plan Logic

Stage 1: under 30% -> 40%

- prioritize readings, fixed compounds, obvious collocations
- daily 10-minute wrong-word deck
- avoid long-form grammar theory unless it appears in wrong answers

Stage 2: 40% -> 50%

- prioritize grammar connectors and short reading question types
- drill reason, contrast, result, purpose, author opinion

Stage 3: 50%+

- add longer reading, inference, time management, mixed mock sections

## Drill Generation Template

When user asks for five questions:

1. Pick 2 vocabulary/kanji items.
2. Pick 2 grammar connector or collocation items.
3. Pick 1 short reading or paraphrase item.
4. Do not give answers until the user responds, unless requested.

Question format:

```markdown
## N2 Mini Drill

1. バスの（　）を払う。
   1. うんしん  2. うんちん  3. うんにん  4. うんりん

...
```

Grading format:

```markdown
| No. | Your answer | Correct | Result | Point |
|---|---|---|---|---|
```

After grading, add repeated misses back to the error bank with updated `Next review`.
