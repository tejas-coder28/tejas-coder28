import os, json, urllib.request
from datetime import date, datetime, timedelta

USER = os.environ.get("GH_USER", "tejas-coder28")
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "streak-card-generator",
        },
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]


def fetch_days():
    created = gql("query($u:String!){user(login:$u){createdAt}}", {"u": USER})["user"]["createdAt"]
    start_year = int(created[:4])
    today = date.today()
    days = {}
    q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
    contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    for y in range(start_year, today.year + 1):
        f = f"{y}-01-01T00:00:00Z"
        t = f"{y}-12-31T23:59:59Z" if y < today.year else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        d = gql(q, {"u": USER, "f": f, "t": t})
        for w in d["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for c in w["contributionDays"]:
                days[c["date"]] = c["contributionCount"]
    return days


def compute(days):
    today = date.today()
    ds = sorted(date.fromisoformat(k) for k in days if date.fromisoformat(k) <= today)
    total = sum(days[d.isoformat()] for d in ds)
    first = next((d for d in ds if days[d.isoformat()] > 0), ds[0] if ds else today)

    longest, ls, le, run, rs = 0, None, None, 0, None
    for d in ds:
        if days[d.isoformat()] > 0:
            if run == 0:
                rs = d
            run += 1
            if run > longest:
                longest, ls, le = run, rs, d
        else:
            run = 0

    cur, cs, ce = 0, None, None
    d = today
    if days.get(d.isoformat(), 0) == 0:
        d -= timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        if ce is None:
            ce = d
        cs = d
        cur += 1
        d -= timedelta(days=1)
    return total, first, cur, cs, ce, longest, ls, le


def fmt(d):
    return f"{d.strftime('%b')} {d.day}" if d else "-"


def render(total, first, cur, cs, ce, longest, ls, le):
    today = date.today()
    cur_range = f"{fmt(cs)} - {fmt(ce)}" if cur else "No active streak"
    long_range = f"{fmt(ls)} - {fmt(le)}" if longest else "-"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="GitHub streak">
  <rect x="0.5" y="0.5" width="494" height="194" rx="8" fill="#0a1428" stroke="#1b2a4a"/>
  <g font-family="'Segoe UI', Ubuntu, Arial, sans-serif" text-anchor="middle">
    <line x1="165" y1="30" x2="165" y2="165" stroke="#1b2a4a" stroke-width="1.5"/>
    <line x1="330" y1="30" x2="330" y2="165" stroke="#1b2a4a" stroke-width="1.5"/>

    <text x="82" y="85" font-size="30" font-weight="700" fill="#ffffff">{total}</text>
    <text x="82" y="115" font-size="14" fill="#90e0ef">Total Contributions</text>
    <text x="82" y="140" font-size="12" fill="#00b4d8">{fmt(first)} {first.year} - Present</text>

    <circle cx="247" cy="82" r="40" fill="none" stroke="#00b4d8" stroke-width="5"/>
    <text x="247" y="92" font-size="28" font-weight="700" fill="#ffffff">{cur}</text>
    <text x="247" y="148" font-size="14" font-weight="700" fill="#ffffff">Current Streak</text>
    <text x="247" y="168" font-size="12" fill="#00b4d8">{cur_range}</text>

    <text x="412" y="85" font-size="30" font-weight="700" fill="#ffffff">{longest}</text>
    <text x="412" y="115" font-size="14" fill="#90e0ef">Longest Streak</text>
    <text x="412" y="140" font-size="12" fill="#00b4d8">{long_range}</text>
  </g>
</svg>
'''


if __name__ == "__main__":
    out = render(*compute(fetch_days()))
    with open("streak.svg", "w", encoding="utf-8") as f:
        f.write(out)
    print("streak.svg written")
