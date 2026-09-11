# Delegated Review — interactive trigger

When Ran says "run delegated review" (or similar), do this:

## 0. Read feedback from prior sessions

In the same Supabase fetch (Step 1), read `rows[0].data.reviewFeedback` — an array of strings left by Ran during past sessions. If it exists and is non-empty:
- Read every note silently and let it influence how you run this session (classification judgment, tone, what to skip, how to present candidates, etc.)
- Do NOT list the notes back to Ran or acknowledge them verbosely — just apply them
- After applying, clear the list: set `data.reviewFeedback = []` in the PATCH at Step 5

If `reviewFeedback` is absent or empty, proceed normally.

---

**During the session**, if Ran says anything like "note for next time", "remember for next time", "next time do X", or "you should have done Y differently" — append his note as a plain string to `data.reviewFeedback` and include it in the Step 5 PATCH. Confirm with one line: "Noted — will apply next review."

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

## 4a. For PROBLEM entries → classify stakes, then generate a verdict

### Stakes classification

A verdict is **HIGH STAKES** if the solution fundamentally depends on which structural or environmental *mechanism type* is chosen — i.e., a hardware/consequence device, a social-accountability arrangement, and a scheduling/environment redesign would each produce genuinely different outcomes and it's not obvious which fits best. When the right mechanism is unclear, default to HIGH STAKES.

A verdict is **LOW STAKES** if the problem has a clear, obvious single solution path (minor friction, simple timing fix, obvious removal of one bad habit, etc.) where generating 3 mechanism alternatives would be artificial.

---

### LOW STAKES verdict (single solution, status "final", commit immediately)

```json
{
  "id": "v<unix_ms>",
  "issuedAt": "<today YYYY-MM-DD>",
  "status": "final",
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

---

### HIGH STAKES verdict (3 candidates, status "draft", wait for Ran's pick)

Generate 3 candidates with genuinely different mechanism types. Reject any candidate that is a minor variant of another already in the list.

Mechanism types to draw from (use each at most once per verdict):
- **device** — a physical object, app lock, alarm, or external consequence mechanism
- **social** — another person observes, is told, or is affected by a miss
- **environment** — scheduling change or friction removal that makes the failure mode structurally harder to reach
- **other** — anything that doesn't fit the above

```json
{
  "id": "v<unix_ms>",
  "issuedAt": "<today YYYY-MM-DD>",
  "status": "draft",
  "coveredEntryIds": ["<entry.id>"],
  "problem": "<one-sentence restatement>",
  "solution": null,
  "whyRootCause": "<one line>",
  "whyFalsifiable": "<one line>",
  "whyPatternMatch": "<one line>",
  "trialLength": "<e.g. '2 weeks'>",
  "reviewDate": null,
  "outcome": null,
  "candidates": [
    {
      "type": "device|social|environment|other",
      "solution": "<specific, concrete>",
      "whyThisType": "<one line — why this mechanism fits the root cause>"
    },
    {
      "type": "...",
      "solution": "...",
      "whyThisType": "..."
    },
    {
      "type": "...",
      "solution": "...",
      "whyThisType": "..."
    }
  ]
}
```

**Do NOT commit a draft verdict to Supabase yet.** Present the candidates to Ran first (see Step 6). Once he picks or supplies his own solution, write that into `solution`, flip `status` to `"final"`, set `trialLength` and `reviewDate` from that point, then commit.

---

Constraints (apply to all verdicts):
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

Mark all processed entries `reviewed: true`. Commit LOW STAKES verdicts and WIN provenTools entries now. Do NOT commit HIGH STAKES draft verdicts — wait for Ran's pick first.

PATCH the full data object back:

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

**For LOW STAKES verdicts (already committed):**
**Problem:** ...
**→ Try:** ...
**Root cause:** ...
**Signal:** ...
**Pattern:** ...
**Trial:** X weeks · Review DATE

**For HIGH STAKES draft verdicts (awaiting pick):**
**Problem:** ...
**Root cause:** ...
**Signal:** ...
**Pattern:** ...

Pick a solution:
**A** *(device)* — [solution]
  *→ [whyThisType]*
**B** *(social)* — [solution]
  *→ [whyThisType]*
**C** *(environment)* — [solution]
  *→ [whyThisType]*

*or: none of these — tell me what you'd rather do.*

Once Ran replies with A/B/C or his own version, write that into `solution`, flip `status` to `"final"`, set `trialLength` and `reviewDate` from today, commit to Supabase.

**For each WIN added to provenTools:**
**Win logged:** [tool name] — [evidence]

No preamble, no encouragement.
