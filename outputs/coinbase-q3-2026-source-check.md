# Coinbase Q3 2026 source check

**Status: HELD.** Checked 2026-10-26 11:54 UTC. Coinbase's Q3 2026 10-Q and earnings 8-K are not on SEC EDGAR yet.

## What was checked

- EDGAR submissions index for Coinbase Global, Inc. (CIK 0001679788), `https://data.sec.gov/submissions/CIK0001679788.json`, fetched 2026-10-26 11:54 UTC. SHA-256 of the response: `de4b03da095ad880baf0f4738ca80f8ab5639972d3fbb6d430f92462de3d63ad`, identical to the frozen `data/raw/sec-submissions-cik0001679788-20261025.json`.
- The newest filing of any form was accepted 2026-10-05 21:38 UTC (a Form 4).
- The newest 10-Q is for the quarter ended 2026-06-30, accepted 2026-07-30 20:15 UTC (accession 0001679788-26-000088). The newest 8-K with Item 2.02 is the Q2 2026 results, accepted 2026-07-30 20:06 UTC (0001679788-26-000087).
- No 10-Q or 8-K Item 2.02 has a report date of 2026-09-30.
- Coinbase's date announcement is a secondary source: a search result pointed to a repost of the Business Wire release of 2026-10-14 (https://www.itiger.com/hans/news/2675522322), which says Q3 2026 results come on Thursday 2026-10-29 after market close and that the materials go on investor.coinbase.com. It was not confirmed on investor.coinbase.com.

## What this means for the 2026-10-29 18:00 ET post

No Q3 2026 card or post draft was built, because there is no filed figure to quote. The planned fallback is the Ondo card (`fri30-pm-ondo-issuance`). If the filing is out by post time, run the check again, then pick one defined figure and its Q2 comparator from the same document:

```sh
SEC_USER_AGENT="Your Name you@example.com" python3 scripts/check_coinbase_filing.py 2026-09-30
```

It prints `OUT` with each filing's URL and EDGAR acceptance time, or `HELD`. The hub's template (Coinbase Q3 2026: {metric} was {q3} versus {q2} in Q2) needs the filing's page and table cited, so a snippet or press-release summary is not enough.
