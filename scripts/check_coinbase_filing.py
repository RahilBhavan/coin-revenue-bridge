#!/usr/bin/env python3
"""Report whether Coinbase's 10-Q and earnings 8-K (Item 2.02) for a quarter are on SEC EDGAR.

    python3 scripts/check_coinbase_filing.py [PERIOD_END]     # default 2026-09-30 (Q3 2026)

Reads https://data.sec.gov/submissions/CIK0001679788.json (Coinbase Global, Inc.) and prints OUT with the
filing URL and EDGAR acceptance time for each filing found, or HELD with the newest 10-Q and 8-K 2.02 it
did see. It also prints the SHA-256 of the response so the check can be cited. Needs SEC_USER_AGENT (a contact string; the
SEC rejects anonymous requests). Network access only; it writes nothing. Exit 0 when OUT, 1 when HELD, 2 on a fetch error.
"""
import hashlib
import json
import os
import sys
import urllib.request

CIK = "0001679788"
URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"
ENV = "SEC_USER_AGENT"  # SEC rejects requests without a contact, e.g. "Your Name you@example.com"


def filings(data, period_end):
    """Rows (form, filed, accepted, report_date, items, url) for 10-Q and 8-K 2.02 filings, newest first."""
    r = data["filings"]["recent"]
    rows = []
    for i, form in enumerate(r["form"]):
        if form == "10-Q" or (form == "8-K" and "2.02" in r["items"][i].split(",")):
            acc = r["accessionNumber"][i]
            url = (f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc.replace('-', '')}/"
                   f"{r['primaryDocument'][i]}")
            rows.append((form, r["filingDate"][i], r["acceptanceDateTime"][i], r["reportDate"][i], r["items"][i], url))
    return rows


def main(argv):
    period_end = argv[0] if argv else "2026-09-30"
    agent = os.environ.get(ENV)
    if not agent:
        print(f"ERROR: set {ENV} to a contact string such as 'Your Name you@example.com'; the SEC rejects anonymous requests")
        return 2
    try:
        request = urllib.request.Request(URL, headers={"User-Agent": agent})
        body = urllib.request.urlopen(request, timeout=30).read()
        data = json.loads(body)
    except Exception as error:  # network, HTTP or JSON failure: report, do not guess
        print(f"ERROR fetching {URL}: {error}")
        return 2
    rows = filings(data, period_end)
    print(f"EDGAR submissions {URL} sha256 {hashlib.sha256(body).hexdigest()}")
    found = [r for r in rows if r[3] == period_end or (r[0] == "8-K" and r[1] >= period_end[:7] and r[3] > period_end)]
    if found:
        print(f"OUT: Coinbase filings for the quarter ending {period_end}")
        for form, filed, accepted, report, items, url in found:
            print(f"  {form} filed {filed}, accepted {accepted}, items {items or '-'}: {url}")
        return 0
    newest_q = next(r for r in rows if r[0] == "10-Q")
    newest_k = next(r for r in rows if r[0] == "8-K")
    print(f"HELD: no 10-Q or 8-K Item 2.02 for the quarter ending {period_end}")
    print(f"  newest 10-Q: period {newest_q[3]}, accepted {newest_q[2]}, {newest_q[5]}")
    print(f"  newest 8-K 2.02: filed {newest_k[1]}, accepted {newest_k[2]}, {newest_k[5]}")
    print(f"  newest filing of any form: {data['filings']['recent']['acceptanceDateTime'][0]}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
