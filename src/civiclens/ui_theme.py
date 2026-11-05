"""Visual identity: CSS tokens and small HTML helpers. All model/user text is escaped before use."""
from __future__ import annotations

from html import escape

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;600&display=swap');
:root{--ink:#1B2A2F;--paper:#FAF8F3;--panel:#F0ECE2;--line:#D9D3C3;--teal:#0F6B5C;--teal-soft:#DCEFE9;--teal-ink:#0B4F43;
--amber-soft:#FBE9C6;--amber-ink:#6B4500;--red-soft:#F8DAD5;--red-ink:#7A1F14;--r:10px}
html,body,[class*="css"],.stApp,textarea,input{font-family:'Inter','Noto Sans Devanagari',system-ui,sans-serif;font-size:16px;color:var(--ink)}
.block-container{max-width:760px;padding-top:2rem;padding-bottom:4rem}
h1,h2,h3{letter-spacing:-0.01em}
.brand{display:flex;align-items:baseline;gap:12px;margin-bottom:4px}
.brand b{font-size:1.9rem;color:var(--teal)}
.brand span{color:#4A5B61}
.card{background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:16px;margin:8px 0 16px}
.obs{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px solid var(--panel)}
.obs:last-child{border-bottom:none}
.obs-text{flex:1}
.conf{color:#4A5B61;font-size:.85rem;white-space:nowrap}
.tag{font-size:.8rem;font-weight:600;padding:2px 10px;border-radius:999px;white-space:nowrap}
.tag.seen{background:var(--teal-soft);color:var(--teal-ink)}
.tag.assumed{background:var(--amber-soft);color:var(--amber-ink)}
.tag.user{background:#E3E8F6;color:#23325E}
.notice{border-radius:var(--r);padding:12px 16px;margin:8px 0 16px;font-size:.95rem}
.notice.warn{background:var(--amber-soft);color:var(--amber-ink)}
.notice.fallback{background:var(--red-soft);color:var(--red-ink);font-weight:600}
.notice.info{background:var(--teal-soft);color:var(--teal-ink)}
table.src{width:100%;border-collapse:collapse;font-size:.95rem}
table.src td{padding:8px 4px;border-bottom:1px solid var(--panel);vertical-align:top}
.stButton>button:focus-visible,.stDownloadButton>button:focus-visible{outline:3px solid #1E6FD9;outline-offset:2px}
.stButton>button,.stDownloadButton>button{border-radius:8px;min-height:44px;font-weight:600}
@media (max-width:600px){.block-container{padding-left:16px;padding-right:16px}.obs{flex-wrap:wrap}}
</style>
"""

CONF_WORDS = {"high": "fairly sure", "medium": "somewhat sure", "low": "not sure"}

DISCLAIMER = (
    "AI predictions can be wrong. Please review and edit this draft before using it. "
    "It is a draft only and has not been sent to anyone. Your photo is processed for this session and is not stored by CivicLens."
)
PRIVACY_NOTE = "Your photo may show faces or vehicle number plates. Consider cropping or blurring them before sharing the photo anywhere."
WHERE_TO_SEND = (
    "Check your local municipal body's official website or helpline for the right way to file this. "
    "CivicLens does not know or verify contact details, and does not submit anything for you."
)


def notice(kind: str, text: str) -> str:
    return f'<div class="notice {kind}">{escape(text)}</div>'


def observation_row(text: str, obs_type: str, confidence: str) -> str:
    seen = obs_type == "observed"
    tag = '<span class="tag seen">Seen in photo</span>' if seen else '<span class="tag assumed">Assumed</span>'
    return (f'<div class="obs">{tag}<span class="obs-text">{escape(text)}</span>'
            f'<span class="conf">{CONF_WORDS.get(confidence, confidence)}</span></div>')


def source_row(statement: str, label: str, kind: str) -> str:
    return f'<tr><td>{escape(statement)}</td><td><span class="tag {kind}">{escape(label)}</span></td></tr>'
