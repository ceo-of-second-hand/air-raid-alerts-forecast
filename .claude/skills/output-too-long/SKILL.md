---
name: output-too-long
description: Move a long answer into a Markdown file and open it in VS Code. Use ONLY when the user explicitly says "output too long!" (or "output too long"). Never trigger on your own judgement about length.
---

# Output too long → Markdown in VS Code

Trigger: the user writes **"output too long!"**. Nothing else triggers this skill.

## What to do

1. **Pick the content.**
   - If the user says it about your *previous* reply, take that reply in full.
   - If they say it in the same message as a new request, write that new answer.
   - Don't shorten it or drop details. The point is a better place to read it, not less content.

2. **Write it to a file.**
   - Folder: `.claude/long-outputs/` in the project root (create it if it's missing).
   - Name: `YYYY-MM-DD_HHMM_<short-kebab-topic>.md`, using the local time.
   - Start with an `# H1` title. Use headings, tables and lists so it's easy to scan.

3. **Open it in VS Code**, reusing the open window:
   ```bash
   code -r "<absolute path to file>"
   ```

4. **Chat reply**: at most 2–3 lines. Give the file path (as a clickable `path:line` reference) and a one-sentence gist. Don't repeat the content in the chat.

## Notes
- `.claude/long-outputs/` is scratch output. Suggest adding it to `.gitignore` once the repo is initialised.
- If `code` is not on PATH, report that and give the file path instead.
