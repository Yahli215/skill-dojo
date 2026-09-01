# Delegated Review — interactive trigger

When Ran says "run delegated review" (or similar), do this:

## 1. Fetch from Supabase

```bash
curl -s "https://ssrqtdpxursgohhhsxvf.supabase.co/rest/v1/skillquest?google_user_id=eq.sokolovski2112%40gmail.com&select=data" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNzcnF0ZHB4dXJzZ29oaGhzeHZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcyNzU4OTUsImV4cCI6MjA5Mjg1MTg5NX0.4_13QxDm4aivMhO4DEwNpMk_aJQECdHz2dqekUQMWDY" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNzcnF0ZHB4dXJzZ29oaGhzeHZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcyNzU4OTUsImV4cCI6MjA5Mjg1MTg5NX0.4_13QxDm4aivMhO4DEwNpMk_aJQECdHz2dqekUQMWDY"
```

Parse `rows[0].data.delegatedReview`. Find entries where `reviewed === false`.

Each entry now has a single `text` field (older entries may have `worked` and/or `newProblem` instead — treat them the same way).

## 2. If no unreviewed entries

Say: "Nothing unreviewed." Stop.

## 3. Classify each entry

For each unreviewed entry, read the `text` (or `worked`/`newProblem` in legacy entries) and classify it as:

- **PROBLEM** — describes something that didn't work, a recurring difficulty, a friction, a struggle, or a question about how to handle something.
- **WIN** — describes something that worked, a positive observation, a useful discovery, or progress.
- **MIXED** — contains both. Split into problem part and win part and handle each separately.

## 4a. For PROBLEM entries → generate a verdict

```json
{
  "id": "v<unix_ms>",
  "issuedAt": "<today YYYY-MM-DD>",
  "coveredEntryIds": ["<entry.id>"],
  "problem": "<one-sentence restatement>",
  "solution": "<specific, concrete experiment — not generic advice>",
  "whyRootCause": "<one line: root cause or symptom? why?>",
  "whyFalsifiable": "<one line: what observable change in 1-3 weeks confirms it?>",
  "whyPatternMatch": "<one line: what known pattern — habit loop, avoidance, energy, etc.?>",
  "trialLength": "<e.g. '2 weeks'>",
  "reviewDate": "<YYYY-MM-DD>",
  "outcome": null
}
```

Constraints:
- Root cause > symptom
- Specific > generic ("Do X at Y time" beats "be more consistent")
- Ran's context: 19yo chess GM, 90-min focus blocks, chess ends 22:30, sleep 00:00, daily sport. Urgency hurts his chess. Slow/deep is the right gear.
- If problem is chess-specific: note it belongs with Aagaard, skip verdict

## 4b. For WIN entries → add to proven tools

If the win describes a tool or habit that worked, add it to `data.provenTools` as:

```json
{
  "id": "pt<unix_ms>",
  "domain": "<chess|sleep|anxiety|general life|other>",
  "tool": "<short name of what worked>",
  "evidence": "<one sentence: what happened that showed it worked>",
  "addedAt": "<today YYYY-MM-DD>",
  "source": "delegated-review"
}
```

If it's just a positive observation with no clear reusable tool, note it briefly in the output but don't add to provenTools.

## 5. Write back

Mark all processed entries `reviewed: true`. PATCH the full data object back:

```bash
curl -s -X PATCH \
  "https://ssrqtdpxursgohhhsxvf.supabase.co/rest/v1/skillquest?google_user_id=eq.sokolovski2112%40gmail.com" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNzcnF0ZHB4dXJzZ29oaGhzeHZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcyNzU4OTUsImV4cCI6MjA5Mjg1MTg5NX0.4_13QxDm4aivMhO4DEwNpMk_aJQECdHz2dqekUQMWDY" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNzcnF0ZHB4dXJzZ29oaGhzeHZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcyNzU4OTUsImV4cCI6MjA5Mjg1MTg5NX0.4_13QxDm4aivMhO4DEwNpMk_aJQECdHz2dqekUQMWDY" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d '{"data": <FULL_DATA_WITH_UPDATES>}'
```

## 6. Output format

For each PROBLEM verdict:
**Problem:** ...
**→ Try:** ...
**Root cause:** ...
**Signal:** ...
**Pattern:** ...
**Trial:** X weeks · Review DATE

For each WIN added to provenTools:
**Win logged:** [tool name] — [evidence]

No preamble, no encouragement.
