---
name: present-results
description: How to present results to the user after running a script, analysis or experiment in this project (e.g. scripts/*.py, backtests, data checks). Use every time you report numbers or findings that came out of code you ran.
---

# Presenting script results

The user gets lost in terms and numbers. Every results message follows these rules.

## 1. Start with a short summary (2–3 sentences)
- **What the script did**, in plain words ("compared the model with a simple rule on 10 two-week periods").
- **What came out**, as the one main finding ("the model was better in all 10, but only by about 4%").
- Put details below the summary, never before it.

## 2. Explain new terms the first time
- The first time a term appears in the conversation, add a short plain explanation in brackets or after a dash.
  Example: "Brier score (how far the predicted probabilities are from what happened; lower is better)".
- Don't re-explain terms already explained earlier in the conversation.
- Prefer plain words over jargon when both work ("periods" instead of "folds" when possible).

## 3. Every number gets its basis and its comparison
- **Based on what:** which data, which period, how many cases ("last 6 weeks, 24 oblasts").
- **Compared to what:** a baseline, the previous result, or a threshold ("vs 79.5% from always guessing 'no alert'").
- A number with neither is not shown. Show fewer numbers rather than unexplained ones.
- Tables: at most ~5 columns, and only columns needed for the main point. Point to the full report in `reports/` for the rest.

## 4. Mark guesses and unchecked claims
- Clearly separate **measured** (came out of the script) from **my guess / not checked** ("my guess, not checked: …").
- Say when a result rests on one period, one sample, or one day.
- If I made a mistake or changed something since the last message, say so plainly.

## 5. End with exactly one question
- One question about the next step, not a list of options or several questions.
