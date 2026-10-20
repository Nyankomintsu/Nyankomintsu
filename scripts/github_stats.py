"""Read public profile numbers from the GitHub GraphQL API."""
from __future__ import annotations

import json
import os
import random
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone

API = "https://api.github.com/graphql"
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

MAIN = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    following { totalCount }
    all: repositories(ownerAffiliations: OWNER, privacy: PUBLIC) { totalCount }
    own: repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""

YEAR = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""


def _gql(query: str, variables: dict, token: str) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "nyankomint-profile"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if data.get("errors"):
        raise RuntimeError(f"GitHub API error: {data['errors']}")
    return data["data"]


def _streaks(days: list[tuple[str, int]]) -> tuple[int, int]:
    """(current, best) runs of days with at least one contribution."""
    best = run = 0
    for _, n in days:
        run = run + 1 if n > 0 else 0
        best = max(best, run)
    rev = days[::-1]
    if rev and rev[0][1] == 0:  # today isn't over yet
        rev = rev[1:]
    current = 0
    for _, n in rev:
        if n == 0:
            break
        current += 1
    return current, best


def fetch(login: str, exclude: list[str]) -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set (run with --sample for a local preview)")
    u = _gql(MAIN, {"login": login}, token)["user"]
    cc = u["contributionsCollection"]
    weeks = [[(d["date"], LEVEL[d["contributionLevel"]], d["contributionCount"]) for d in w["contributionDays"]]
             for w in cc["contributionCalendar"]["weeks"]]

    # every day since the account was created, for the longest streak
    created = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    seen: dict[str, int] = {}
    start = created
    while start < now:
        end = min(start + timedelta(days=365), now)
        y = _gql(YEAR, {"login": login, "from": start.isoformat(), "to": end.isoformat()}, token)
        for w in y["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                seen[d["date"]] = d["contributionCount"]
        start = end
    current, best = _streaks(sorted(seen.items()))

    skip = {e.lower() for e in exclude}
    langs: Counter = Counter()
    stars = 0
    per_repo = []
    for repo in u["own"]["nodes"]:
        stars += repo["stargazerCount"]
        per_repo.append(f"{repo['name']} ★{repo['stargazerCount']}")
        if repo["name"].lower() in skip:
            continue
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]

    summary = (f"{u['all']['totalCount']} public repos ({', '.join(per_repo)}), "
               f"{cc['contributionCalendar']['totalContributions']} contributions in the last year, "
               f"streak {current} (best {best})")
    print("  " + summary)
    if os.environ.get("GITHUB_ACTIONS"):  # also shown on the workflow run page
        print(f"::notice title=Profile stats::{summary}")
    return {
        "days": (now.date() - created.date()).days,
        "repos": u["all"]["totalCount"],
        "stars": stars,
        "commits": cc["totalCommitContributions"],
        "prs": cc["totalPullRequestContributions"],
        "issues": cc["totalIssueContributions"],
        "followers": u["followers"]["totalCount"],
        "following": u["following"]["totalCount"],
        "contributions": cc["contributionCalendar"]["totalContributions"],
        "streak": current,
        "best_streak": best,
        "languages": langs.most_common(),
        "weeks": weeks,
        "year_label": "the last year",
    }


def sample() -> dict:
    """Made-up numbers, only for previewing the layout locally."""
    rnd = random.Random(42)
    today = date.today()
    start = today - timedelta(days=364 + (today.weekday() + 1) % 7)
    weeks, week = [], []
    d = start
    while d <= today:
        n = rnd.choice([0, 0, 0, 1, 2, 3, 5, 8]) if rnd.random() < 0.8 else 0
        lv = 0 if n == 0 else min(4, 1 + n // 2)
        week.append((d.isoformat(), lv, n))
        if len(week) == 7:
            weeks.append(week)
            week = []
        d += timedelta(days=1)
    if week:
        weeks.append(week)
    total = sum(n for w in weeks for _, _, n in w)
    return {
        "days": 393, "repos": 3, "stars": 2, "commits": 128, "prs": 4, "issues": 3, "followers": 4,
        "following": 2, "contributions": total, "streak": 3, "best_streak": 9,
        "languages": [("Python", 52000), ("C++", 21000), ("HTML", 9000), ("JavaScript", 4000)],
        "weeks": weeks, "year_label": "the last year",
    }
