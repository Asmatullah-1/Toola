#!/usr/bin/env python3
"""Techsneurons Radar: crawls 100+ feeds for AI news + professional pain points."""
import calendar, random, concurrent.futures as cf, datetime as dt, html, json, os, re, smtplib, socket, ssl, time
from email.mime.text import MIMEText
import feedparser
from sources import INDUSTRIES, SECTOR_OF, news_sources, pain_sources

UA = "Mozilla/5.0 (compatible; TechsneuronsRadar/2.0)"
HOURS, PAIN_HOURS, MAX = int(os.getenv("DIGEST_HOURS", "30")), int(os.getenv("PAIN_HOURS", "72")), 8
socket.setdefaulttimeout(20)
HOT = ["launch", "release", "introducing", "announc", "new model", "open-source", "open source", "agent", "gpt",
       "claude", "gemini", "llama", "qwen", "deepseek", "mistral", "benchmark", "pricing", "now available", "beta"]
PAPER = ["new model", "benchmark", "agent", "open-source", "state-of-the-art", "outperform"]
PAIN = ["how do i automate", "is there a tool", "is there an app", "is there a way to", "any software", "alternative to",
        "wasting", "tedious", "manual", "takes hours", "spend hours", "repetitive", "can ai", "chatgpt for",
        "struggling with", "so much time", "there must be a better way", "how do you handle", "time consuming", "takes forever", "rotoscop", "transcri", "subtitle", "caption", "remove background", "batch process", "upscal", "voice clon"]
AIW = ["ai", "chatgpt", "gpt", "llm", "automat", "copilot", "claude", "gemini"]


def clean(s, n=240):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    s = re.sub(r"submitted by.*|\[link\]|\[comments\]", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", s).strip()[:n]


def hits(text, words):
    low = text.lower()
    return [w for w in words if w in low]


STOP = set("the and for with how new you your from this that are can any not use using into about what why".split())


def toks(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in STOP}


def parse(url):
    """Retry, then fall back to old.reddit.com (cloud IPs are sometimes blocked on www)."""
    p = None
    if "reddit.com" in url:
        time.sleep(random.uniform(0, 4))  # spread requests so Reddit is less likely to rate-limit
    for u in dict.fromkeys([url, url.replace("www.reddit.com", "old.reddit.com")]):
        for _ in range(2):
            p = feedparser.parse(u, agent=UA)
            if p.entries:
                return p
            time.sleep(1.5)
    return p


KW = {  # news is tagged with industries by keyword; names must match sources.INDUSTRIES
    "Video Editing": ["video", "sora", "veo ", "runway", "premiere", "davinci", "text-to-video"],
    "Photo Editing": ["image generat", "midjourney", "photoshop", "stable diffusion", "flux", "text-to-image"],
    "Graphic Design": ["design tool", "figma", "canva", "logo"],
    "Writing & Publishing": ["writing", "writer", "essay", "novel", "authors"],
    "Audio Engineering": ["audio", "speech", "text-to-speech", "voice"],
    "Music Production": ["music", "suno", "udio", "song"],
    "Software Development": ["coding", "code ", "developer", "github", "cursor", "sdk", "copilot"],
    "Data Science": ["dataset", "machine learning", "fine-tun", "benchmark", "open-weight"],
    "Cybersecurity": ["security", "vulnerab", "malware", "phishing"],
    "Marketing": ["marketing", "advertis", "seo"],
    "E-commerce": ["ecommerce", "e-commerce", "shopping", "retail"],
    "Sales": ["sales", "crm"],
    "Customer Service": ["customer support", "chatbot", "customer service"],
    "Human Resources": ["hiring", "recruit", "hr "],
    "Accounting": ["accounting", "tax ", "invoice", "bookkeeping"],
    "Finance & Investing": ["finance", "trading", "banking"],
    "Law Firms": ["legal", "lawyer", "contract"],
    "Health IT": ["health", "medical", "clinical", "drug discovery"],
    "K-12 Teaching": ["education", "student", "school", "teacher", "tutor"],
    "Game Development": ["game", "gaming"],
    "Manufacturing": ["robot", "factory", "manufactur"],
    "Project Management": ["meeting", "productivity", "workflow", "agent"],
}


def tag(text):
    low = text.lower()
    return [n for n, ws in KW.items() if any(w in low for w in ws)][:3] or ["General AI"]


def fetch(src):
    name, url, cat, kind = src
    try:
        p = parse(url)
    except Exception as e:
        return src, [], "error", str(e)[:60]
    if not p.entries:
        return src, [], "empty", f"HTTP {p.get('status', '?')}" + (" · parse issue" if p.get("bozo") else "")
    cutoff = time.time() - (PAIN_HOURS if kind == "pain" else HOURS) * 3600
    items = []
    for e in p.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")
        if not t or calendar.timegm(t) < cutoff:
            continue
        title, snip = clean(e.get("title"), 200), clean(e.get("summary"))
        text = f"{title} {snip}"
        if kind == "pain":
            m = hits(text, PAIN)
            if not m:
                continue
            tags, score = m[:3], len(m) + len(hits(text, AIW))
        else:
            if kind == "paper" and not hits(text, PAPER):
                continue
            tags = hits(text, HOT)[:3]
            score = len(tags)
        items.append(dict(title=title, link=e.get("link", ""), source=name, cat=cat, ts=calendar.timegm(t),
                          snip=snip[:200], tags=tags, score=score, p=kind == "pain", inds=[cat] if kind == "pain" else tag(text)))
    items.sort(key=lambda x: (-x["score"], -x["ts"]))
    return src, items[:MAX], "ok", ""


def cluster(items, thr, w):
    """Merge near-duplicate titles. News: 'covered by N sources'. Pain: 'N similar posts' (opportunity)."""
    out = []
    for it in items:
        t = toks(it["title"])
        for c in out:
            if len(t & c["_t"]) / max(1, len(t | c["_t"])) >= thr:
                c["also"].append(dict(source=it["source"], link=it["link"]))
                c["n"] += 1
                break
        else:
            it.update(_t=t, also=[], n=1)
            out.append(it)
    for c in out:
        c.pop("_t")
        c["score"] += min(c["n"] - 1, 3) * w
    return sorted(out, key=lambda x: (-x["score"], -x["ts"]))


def run():
    srcs = news_sources() + pain_sources()
    news, pain, health, seen = [], [], [], set()
    with cf.ThreadPoolExecutor(16) as ex:
        for src, items, status, note in ex.map(fetch, srcs):
            health.append(dict(title=src[0], link=src[1], source=src[2], cat=src[2], status=status, note=note, n=len(items), score=0))
            for it in items:
                key = re.sub(r"\W+", "", it["title"].lower())[:80]
                if key in seen:
                    continue
                seen.add(key)
                (pain if src[3] == "pain" else news).append(it)
    news, pain = cluster(news, 0.5, 1), cluster(pain, 0.35, 2)
    live = sum(h["status"] == "ok" for h in health)
    if live < len(health) / 2:
        print(f"[WARN] only {live}/{len(health)} sources responded: network or blocking issue?")
    for h in health:
        if h["status"] != "ok":
            print(f"[feed problem] {h['title']}: {h['status']} {h['note']}")
    return dict(sectors={**SECTOR_OF, "General AI": "General"}, gen_ts=int(time.time()), generated=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), hours=HOURS,
                total_sources=len(health), industries=len(INDUSTRIES.strip().splitlines()), live_sources=live, news=news, pain=pain,
                health=sorted(health, key=lambda h: h["status"] == "ok"))


def email(d):
    keys = [os.getenv(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "DIGEST_TO")]
    if not all(keys):
        return print("[info] SMTP not set; skipping email")
    host, user, pwd, to = keys
    li = lambda xs: "".join(f"<li><a href='{html.escape(i['link'])}'>{html.escape(i['title'])}</a> <small>({html.escape(i['source'])})</small></li>" for i in xs)
    body = f"<h2>Hot AI news</h2><ul>{li(d['news'][:25])}</ul><h2>Pain points to write about</h2><ul>{li(d['pain'][:15])}</ul>"
    m = MIMEText(body, "html"); m["Subject"], m["From"], m["To"] = "Techsneurons Radar", user, to
    with smtplib.SMTP_SSL(host, int(os.getenv("SMTP_PORT") or 465), context=ssl.create_default_context()) as s:
        s.login(user, pwd); s.sendmail(user, [to], m.as_string())


if __name__ == "__main__":
    d = run()
    os.makedirs("docs", exist_ok=True)
    blob = json.dumps(d).replace("</", "<\\/")
    open("docs/data.json", "w", encoding="utf-8").write(json.dumps(d))
    open("docs/index.html", "w", encoding="utf-8").write(open("template.html", encoding="utf-8").read().replace("__DATA__", blob))
    print(f"{len(d['news'])} news, {len(d['pain'])} pain points, {d['live_sources']}/{d['total_sources']} sources live")
    email(d)
