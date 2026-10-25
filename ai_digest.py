#!/usr/bin/env python3
"""Techsneurons daily AI digest.

Pulls RSS/Atom feeds, keeps items from the last N hours, ranks them by
"launch-y" keywords, and writes docs/index.html (and emails it if SMTP
secrets are set).
"""
import calendar
import datetime as dt
import html
import os
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import feedparser

feedparser.USER_AGENT = "TechsneuronsDigest/1.0 (+https://example.com)"

HOURS = int(os.getenv("DIGEST_HOURS", "26"))
MAX_PER_FEED = 8

# (name, url, must_match_keywords)  -> must_match=True keeps only keyword hits
FEEDS = {
    "Model & lab releases": [
        ("OpenAI news", "https://openai.com/news/rss.xml", False),
        ("Google AI blog", "https://blog.google/technology/ai/rss/", False),
        ("Hugging Face blog", "https://huggingface.co/blog/feed.xml", False),
    ],
    "SDK & tool releases (GitHub)": [
        ("openai-python", "https://github.com/openai/openai-python/releases.atom", False),
        ("anthropic-sdk-python", "https://github.com/anthropics/anthropic-sdk-python/releases.atom", False),
        ("google-genai", "https://github.com/googleapis/python-genai/releases.atom", False),
        ("mistral client", "https://github.com/mistralai/client-python/releases.atom", False),
        ("Ollama", "https://github.com/ollama/ollama/releases.atom", False),
        ("LangChain", "https://github.com/langchain-ai/langchain/releases.atom", False),
    ],
    "Community buzz": [
        ("r/LocalLLaMA", "https://www.reddit.com/r/LocalLLaMA/.rss", False),
        ("Hacker News (AI)", "https://hnrss.org/newest?q=LLM+OR+AI+OR+GPT+OR+Claude+OR+Gemini&points=30", False),
    ],
    "Analysis & newsletters": [
        ("Simon Willison", "https://simonwillison.net/atom/everything/", False),
        ("AINews (smol.ai)", "https://news.smol.ai/rss.xml", False),
        ("Latent Space", "https://www.latent.space/feed", False),
    ],
    "Research (filtered)": [
        ("arXiv cs.AI", "https://rss.arxiv.org/rss/cs.AI", True),
        ("arXiv cs.CL", "https://rss.arxiv.org/rss/cs.CL", True),
    ],
}

HOT = [
    "launch", "release", "introducing", "announc", "new model", "open-source",
    "open source", "agent", "gpt", "claude", "gemini", "llama", "qwen",
    "deepseek", "mistral", "benchmark", "api", "pricing", "v2", "v3", "v4", "v5",
]
PAPER_MUST = ["new model", "benchmark", "agent", "open-source", "state-of-the-art", "outperform"]


def ts(entry):
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    return calendar.timegm(t) if t else None


def score(text, words):
    low = text.lower()
    return sum(1 for w in words if w in low)


def collect():
    cutoff = time.time() - HOURS * 3600
    out = {}
    for section, feeds in FEEDS.items():
        items = []
        for name, url, must in feeds:
            try:
                parsed = feedparser.parse(url)
            except Exception as exc:  # network or parse failure
                print(f"[warn] {name}: {exc}")
                continue
            if not parsed.entries:
                print(f"[warn] {name}: no entries (feed may have moved)")
                continue
            kept = []
            for e in parsed.entries:
                t = ts(e)
                if t is None or t < cutoff:
                    continue
                title = e.get("title", "").strip()
                text = f"{title} {e.get('summary', '')}"
                if must and score(text, PAPER_MUST) == 0:
                    continue
                kept.append({
                    "source": name,
                    "title": title,
                    "link": e.get("link", ""),
                    "time": t,
                    "score": score(text, HOT),
                })
            kept.sort(key=lambda x: (-x["score"], -x["time"]))
            items.extend(kept[:MAX_PER_FEED])
        items.sort(key=lambda x: (-x["score"], -x["time"]))
        out[section] = items
    return out


def render(data):
    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total = sum(len(v) for v in data.values())
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Techsneurons Daily AI Digest</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:0 auto;padding:16px;line-height:1.45}"
        "h1{font-size:1.4rem}h2{font-size:1.1rem;margin-top:1.6rem;border-bottom:1px solid #8884}"
        "li{margin:.5rem 0}small{color:#888}a{text-decoration:none}</style></head><body>",
        f"<h1>Techsneurons Daily AI Digest</h1><small>{now} · last {HOURS}h · {total} items</small>",
    ]
    for section, items in data.items():
        parts.append(f"<h2>{html.escape(section)}</h2>")
        if not items:
            parts.append("<small>Nothing new.</small>")
            continue
        parts.append("<ul>")
        for it in items:
            flame = "🔥 " if it["score"] >= 2 else ""
            parts.append(
                f"<li>{flame}<a href='{html.escape(it['link'])}'>{html.escape(it['title'])}</a> "
                f"<small>— {html.escape(it['source'])}</small></li>"
            )
        parts.append("</ul>")
    parts.append("</body></html>")
    return "\n".join(parts)


def send_email(body_html):
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")
    to = os.getenv("DIGEST_TO")
    if not all([host, user, pwd, to]):
        print("[info] SMTP not configured; skipping email.")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Techsneurons Daily AI Digest"
    msg["From"] = user
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP_SSL(host, int(os.getenv("SMTP_PORT", "465")), context=ssl.create_default_context()) as s:
        s.login(user, pwd)
        s.sendmail(user, [to], msg.as_string())
    print("[info] Email sent.")


if __name__ == "__main__":
    page = render(collect())
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(page)
    print("Wrote docs/index.html")
    send_email(page)
