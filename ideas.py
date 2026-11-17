"""Turns the Radar's strongest finds into a SHORT list of article ideas and asks you (via a GitHub issue) to write them.
Quality over quantity: strict thresholds and a weekly cap. Tune the numbers below."""
import json, os, re, time, urllib.request

MAX_PER_WEEK, MAX_PER_RUN = 3, 2          # hard caps on new ideas
NEWS_MIN_SOURCES, NEWS_MIN_SCORE = 2, 4   # a news story needs 2+ outlets and strong launch signals
PAIN_MIN_POSTS, PAIN_MIN_SCORE = 3, 6     # a problem needs 3+ similar posts
STATE = "docs/ideas.json"
RULES = ("Use ONLY the facts below. Never invent numbers, quotes, prices or dates. Mark gaps as [VERIFY: ...] and spots that "
         "need our own hands-on test as [ADD OUR TEST: ...]. Plain English, short paragraphs, link claims to their sources. "
         "End each point with a verdict (Act, Watch or Skip) and one sentence of reasoning. Output: a TITLE line, a META line, "
         "then the article body as simple HTML.")
STOP = set("the and for with how new you your from this that are can any not use using into about what why".split())


def toks(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in STOP}


def similar(a, b):
    x, y = toks(a), toks(b)
    return len(x & y) / max(1, len(x | y)) >= 0.5


def load():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return []


def build_prompt(kind, it):
    facts = [f"- {it['title']} | {it['source']} | {it['link']}" + (f" | {it['snip']}" if it.get("snip") else "")]
    facts += [f"- also covered by: {a['source']} | {a['link']}" for a in it.get("also", [])[:4]]
    task = (f"Write a practical how-to article for {it['cat']} professionals that answers the recurring problem in the FACTS."
            if kind == "howto" else "Write a verdict article about this update.")
    return f"{task}\nReaders: team leads, product managers, founders, operators.\nRULES: {RULES}\nFACTS:\n" + "\n".join(facts)


def build_reasons(kind, it, now):
    """Plain-language 'why write this' lines. Built only from what the Radar actually saw."""
    n, tags = it.get("n", 1), ", ".join(it.get("tags", [])) or "none"
    hrs = max(0, (now - it["ts"]) / 3600)
    age = "under an hour" if hrs < 1 else f"{int(hrs)}h" if hrs < 48 else f"{int(hrs // 24)} days"
    inds = [x for x in it.get("inds", []) if x != "General AI"]
    who = ("Professionals in " + ", ".join(inds[:2])) if inds else "Team leads, product managers, founders and operators weighing AI tools"
    if kind == "verdict":
        return [["Why now", f"First seen {age} ago and already covered by {n} outlets, so readers are looking for a clear take."],
                ["Who it helps", who],
                ["Evidence", f"Launch signals: {tags}. Main source: {it['source']}" + (f" plus {n - 1} more." if n > 1 else ".")],
                ["Angle", "Give a clear Act, Watch or Skip verdict and say who it applies to."],
                ["Check first", "Confirm key facts on the official source. Search demand and competing articles are not checked automatically, so look at Google before writing."]]
    return [["Why now", f"{n} similar posts in the last 3 days, so this is a recurring problem, not a one-off."],
            ["Who it helps", who],
            ["Evidence", f"Phrases people used: {tags}. First post seen {age} ago."],
            ["Angle", "A step-by-step AI workflow for this problem, with the mistakes to avoid."],
            ["Check first", "Test a tool on this task yourself before recommending one. Search demand and competition are not checked automatically."]]


def create_issue(idea):
    tok, repo = os.getenv("GITHUB_TOKEN"), os.getenv("GITHUB_REPOSITORY")
    if not (tok and repo):
        return ""
    body = ("### Why write this\n" + "".join(f"- **{l}:** {x}\n" for l, x in idea.get("reasons", [])) + f"\n**Suggested type:** {idea['label']}\n**Main source:** {idea['link']}\n\n"
            "### Your steps\n- [ ] Paste your master writing rules into Claude, then the prompt below\n"
            "- [ ] Audit it in ChatGPT with the audit rules (fix once, audit again)\n- [ ] Visual briefs and visual check\n"
            "- [ ] Your checks: tested it? screenshots genuine, image rights, facts current\n- [ ] Publish, then close this issue\n\n"
            "### Prompt to paste\n```text\n" + idea["prompt"] + "\n```")
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues",
                                 json.dumps({"title": "Article idea: " + idea["title"][:110], "body": body, "labels": ["article-idea"]}).encode(),
                                 {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json", "User-Agent": "radar",
                                  "X-GitHub-Api-Version": "2022-11-28"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))["html_url"]
    except Exception as e:
        print("[issue failed]", e)
        return ""


def make_ideas(d):
    now, state = int(time.time()), load()
    room = min(MAX_PER_RUN, max(0, MAX_PER_WEEK - sum(1 for i in state if now - i["ts"] < 7 * 86400)))
    cands = [("verdict", it) for it in d["news"] if it.get("n", 1) >= NEWS_MIN_SOURCES and it["score"] >= NEWS_MIN_SCORE]
    cands += [("howto", it) for it in d["pain"] if it.get("n", 1) >= PAIN_MIN_POSTS and it["score"] >= PAIN_MIN_SCORE]
    cands.sort(key=lambda c: (-c[1]["score"], -c[1]["ts"]))
    for kind, it in cands:
        if room <= 0:
            break
        if any(similar(it["title"], s["title"]) for s in state):
            continue
        n, tags = it.get("n", 1), ", ".join(it.get("tags", []))
        why = (f"Covered by {n} sources; signals: {tags}" if kind == "verdict"
               else f"{n} similar posts in {it['cat']}: a recurring problem; phrases: {tags}")
        idea = dict(title=it["title"], link=it["link"], kind=kind, label="Verdict article" if kind == "verdict" else "How-to for " + it["cat"],
                    why=why, reasons=build_reasons(kind, it, now), ts=now, cat=it["cat"], inds=it.get("inds", [it["cat"]]), prompt=build_prompt(kind, it))
        idea["url"] = create_issue(idea)
        state.append(idea)
        room -= 1
    state = state[-60:]
    os.makedirs("docs", exist_ok=True)
    json.dump(state, open(STATE, "w", encoding="utf-8"))
    return [dict(title=i["title"], link=i["url"] or i["link"], source="Radar pick", cat=i["label"], ts=i["ts"], snip="" if i.get("reasons") else i["why"], reasons=i.get("reasons"),
                 tags=[i["kind"]], score=2, p=False, n=1, also=[], inds=i["inds"], prompt=i["prompt"]) for i in reversed(state[-20:])]
