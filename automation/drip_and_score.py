#!/usr/bin/env python3
"""
Aegis Capital RE — Seller Drip Sequences + Lead Scoring
========================================================
Run standalone or import into daily_runner.py.

Drip sequence: Day 1, 3, 7, 14, 30 emails to motivated sellers.
Lead scoring:  Composite 0-100 based on motivation, equity, ARV fit, condition.
Hot lead alerts: SMS + email when score >= threshold.

Usage:
  python3 drip_and_score.py --run-drip        # Send today's scheduled drip emails
  python3 drip_and_score.py --score           # Score all leads, print ranking
  python3 drip_and_score.py --alerts          # Send hot lead alerts
  python3 drip_and_score.py --all             # Run everything
"""

import sqlite3
import smtplib
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — fill in before using
# ─────────────────────────────────────────────────────────────────────────────
CONFIG = {
    "db_path": Path(__file__).parent.parent / "backend" / "aegis.db",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "",          # your Gmail address
    "smtp_pass": "",          # Gmail App Password
    "from_name": "Chris @ Aegis Capital RE",
    "reply_to": "",           # your business email
    "twilio_sid": "",
    "twilio_token": "",
    "twilio_from": "",        # your Twilio number e.g. +17135550000
    "your_cell": "",          # your cell for hot lead alerts
    "arv_min": 350000,
    "arv_max": 450000,
    "hot_score_threshold": 70,  # score >= this → SMS alert to you
}

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(CONFIG["db_path"])
    conn.row_factory = lambda c, r: {d[0]: r[i] for i, d in enumerate(c.description)}
    return conn


def ensure_drip_table():
    """Create drip tracking table if it doesn't exist."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drip_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            day_num     INTEGER NOT NULL,
            sent_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            status      TEXT DEFAULT 'sent',
            FOREIGN KEY (property_id) REFERENCES properties(id),
            UNIQUE(property_id, day_num)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lead_scores (
            property_id  INTEGER PRIMARY KEY,
            score        INTEGER,
            breakdown    TEXT,
            scored_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        )
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# LEAD SCORING
# ─────────────────────────────────────────────────────────────────────────────

MOTIVATION_SCORES = {
    "pre-foreclosure":   40,
    "foreclosure":       40,
    "divorce":           35,
    "financial hardship":35,
    "behind on payments":30,
    "tax delinquent":    30,
    "estate":            25,
    "probate":           25,
    "tired landlord":    20,
    "inherited":         20,
    "relocation":        15,
    "job":               15,
    "investor":          10,
}


def score_lead(p: dict) -> tuple[int, dict]:
    """
    Score a property lead 0–100.
    Returns (score, breakdown_dict).
    """
    breakdown = {}

    # 1. Motivation (0-40 pts)
    mot = (p.get("motivation") or "").lower()
    mot_score = 10  # default
    for kw, pts in MOTIVATION_SCORES.items():
        if kw in mot:
            mot_score = pts
            break
    breakdown["motivation"] = mot_score

    # 2. Equity (0-30 pts) — (ARV - asking) / ARV
    arv = p.get("arv") or 0
    asking = p.get("asking_price") or 0
    if arv > 0 and asking > 0:
        equity_pct = (arv - asking) / arv
        equity_pts = min(30, max(0, int(equity_pct * 60)))
    else:
        equity_pts = 0
    breakdown["equity"] = equity_pts

    # 3. ARV fit (0-20 pts) — sweet spot $350K–$450K
    if CONFIG["arv_min"] <= arv <= CONFIG["arv_max"]:
        arv_pts = 20
    elif (CONFIG["arv_min"] - 50000) <= arv <= (CONFIG["arv_max"] + 50000):
        arv_pts = 10
    elif arv > 0:
        arv_pts = 5
    else:
        arv_pts = 0
    breakdown["arv_fit"] = arv_pts

    # 4. Condition (0-10 pts)
    cond_map = {"C1": 2, "C2": 4, "C3": 6, "C4": 9, "C5": 10, "C6": 8}
    cond_pts = cond_map.get(p.get("condition", ""), 5)
    breakdown["condition"] = cond_pts

    total = min(99, mot_score + equity_pts + arv_pts + cond_pts)
    return total, breakdown


def run_scoring() -> list:
    """Score all active leads. Save to DB. Return sorted list."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM properties WHERE status IN ('lead','analyzing')"
    ).fetchall()

    scored = []
    for p in rows:
        score, breakdown = score_lead(p)
        scored.append({**p, "score": score, "breakdown": breakdown})
        conn.execute("""
            INSERT INTO lead_scores (property_id, score, breakdown, scored_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(property_id) DO UPDATE SET
                score=excluded.score,
                breakdown=excluded.breakdown,
                scored_at=excluded.scored_at
        """, (p["id"], score, json.dumps(breakdown)))

    conn.commit()
    conn.close()

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _send_email(to: str, subject: str, html: str, text: str = ""):
    if not CONFIG["smtp_user"] or not CONFIG["smtp_pass"]:
        print(f"  [SKIP] Email not configured. Would send to {to}: {subject}")
        return False
    msg = MIMEMultipart("alternative")
    msg["From"]     = f"{CONFIG['from_name']} <{CONFIG['smtp_user']}>"
    msg["To"]       = to
    msg["Reply-To"] = CONFIG.get("reply_to") or CONFIG["smtp_user"]
    msg["Subject"]  = subject
    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP(CONFIG["smtp_host"], CONFIG["smtp_port"]) as s:
            s.starttls()
            s.login(CONFIG["smtp_user"], CONFIG["smtp_pass"])
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"  [ERROR] Email failed: {e}")
        return False


def _send_sms(to: str, body: str):
    if not CONFIG["twilio_sid"] or not CONFIG["twilio_token"]:
        print(f"  [SKIP] Twilio not configured. SMS would send to {to}: {body[:80]}")
        return False
    try:
        from twilio.rest import Client
        client = Client(CONFIG["twilio_sid"], CONFIG["twilio_token"])
        client.messages.create(body=body, from_=CONFIG["twilio_from"], to=to)
        return True
    except ImportError:
        print("  [SKIP] twilio package not installed. Run: pip install twilio")
        return False
    except Exception as e:
        print(f"  [ERROR] SMS failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# DRIP EMAIL TEMPLATES  (Day 1, 3, 7, 14, 30)
# ─────────────────────────────────────────────────────────────────────────────

def _base_style():
    return """
    <style>
      body { margin:0; padding:0; font-family:'Segoe UI',Arial,sans-serif; background:#f4f4f4; }
      .wrap { max-width:600px; margin:0 auto; background:#fff; }
      .header { background:#0D0D0D; padding:24px 32px; }
      .header-logo { color:#C9A84C; font-size:14px; letter-spacing:2px; text-transform:uppercase; }
      .body { padding:32px; color:#333; line-height:1.6; }
      .body h2 { font-size:22px; color:#0D0D0D; margin-bottom:12px; }
      .body p { margin-bottom:14px; }
      .cta { display:inline-block; background:#C9A84C; color:#0D0D0D; font-weight:700;
             padding:14px 28px; border-radius:6px; text-decoration:none; margin:8px 0; }
      .footer { background:#f9f9f9; border-top:1px solid #eee; padding:20px 32px;
                font-size:12px; color:#999; line-height:1.5; }
      .highlight { background:#FFF9EC; border-left:4px solid #C9A84C; padding:14px 18px;
                   border-radius:0 6px 6px 0; margin:16px 0; }
    </style>
    """


def drip_template(day: int, prop: dict) -> tuple[str, str, str]:
    """Returns (subject, html, plain_text) for drip day N."""
    name = (prop.get("seller_name") or "").split()[0] or "there"
    addr = prop.get("address", "your property")
    from_name = CONFIG["from_name"].split("@")[0].strip()

    templates = {
        1: {
            "subject": f"We received your info about {addr} — next step",
            "headline": f"Hi {name}, we're pulling comps now",
            "body": f"""
              <p>We just received your info about <strong>{addr}</strong> and our team is already running comps on similar homes that have sold in the area.</p>
              <div class="highlight">
                <strong>What happens next:</strong><br>
                Within 24 hours, one of us will reach out with a no-obligation cash offer based on the real numbers — not a range.
              </div>
              <p>If you have any questions in the meantime, just reply to this email or text/call us directly.</p>
              <p>We work with homeowners in every situation — inherited properties, foreclosures, divorces, relocations — and we close fast, usually in 7–14 days.</p>
            """,
            "cta_text": "Reply with Questions",
            "cta_link": f"mailto:{CONFIG.get('reply_to') or CONFIG['smtp_user']}?subject=Question about {addr}"
        },
        3: {
            "subject": f"Quick update on {addr}",
            "headline": f"Still working on your offer, {name}",
            "body": f"""
              <p>Just wanted to follow up — we're still putting together the numbers for <strong>{addr}</strong>.</p>
              <p>The Houston market has been moving fast in your area, and we want to make sure the offer reflects current comps so it's actually worth your time.</p>
              <div class="highlight">
                <strong>Did your situation change?</strong><br>
                If you need to move faster or have additional details to share, reply here and we'll prioritize your offer.
              </div>
              <p>No pressure — we're just here when you're ready to talk numbers.</p>
            """,
            "cta_text": "I'm Ready to Talk",
            "cta_link": f"mailto:{CONFIG.get('reply_to') or CONFIG['smtp_user']}?subject=Ready to talk - {addr}"
        },
        7: {
            "subject": f"{name}, we can close in 7 days — here's how",
            "headline": "How a cash sale actually works",
            "body": f"""
              <p>We know you might be weighing your options on <strong>{addr}</strong>, so we wanted to share exactly how our process works — no surprises.</p>
              <p><strong>Step 1:</strong> You accept our offer (or counter — we're flexible)</p>
              <p><strong>Step 2:</strong> We open title — you don't need to do anything</p>
              <p><strong>Step 3:</strong> We close on YOUR timeline, as fast as 7 days</p>
              <p><strong>Step 4:</strong> You get cash at closing. No commissions, no repairs, no showings</p>
              <div class="highlight">
                Sellers typically net <strong>6–8% more</strong> than they would after paying agent commissions, repairs, and months of carrying costs on a traditional listing.
              </div>
              <p>Ready to see your number? Reply and we'll schedule a quick 10-minute call.</p>
            """,
            "cta_text": "Schedule a Call",
            "cta_link": f"mailto:{CONFIG.get('reply_to') or CONFIG['smtp_user']}?subject=Schedule call - {addr}"
        },
        14: {
            "subject": f"Two weeks out — what's your plan for {addr.split(',')[0]}?",
            "headline": f"Still here for you, {name}",
            "body": f"""
              <p>It's been two weeks since you reached out about <strong>{addr}</strong>. Life gets busy — we get it.</p>
              <p>Whether you've decided to wait, list with an agent, or you're still weighing options — we respect whatever path is right for you.</p>
              <div class="highlight">
                <strong>One thing we hear often:</strong><br>
                "I wish I called you sooner." We've helped sellers avoid months of showings, open houses, and price reductions with a simple, certain close.
              </div>
              <p>If circumstances have changed — or if you just want to know what number we'd put on paper — reply here. No obligation, ever.</p>
            """,
            "cta_text": "Get My Number",
            "cta_link": f"mailto:{CONFIG.get('reply_to') or CONFIG['smtp_user']}?subject=What's my offer? - {addr}"
        },
        30: {
            "subject": f"Last check-in on {addr.split(',')[0]}",
            "headline": "Closing the loop — just in case",
            "body": f"""
              <p>Hi {name}, this is our last check-in about <strong>{addr}</strong>.</p>
              <p>We don't want to crowd your inbox if the timing isn't right. But before we close the file, we wanted to make one final offer to connect.</p>
              <p>If you ever decide you want a fast, certain cash sale — even 6 months from now — just reply to this email and we'll pick up right where we left off. Your info is saved.</p>
              <div class="highlight">
                <strong>Our commitment to you:</strong><br>
                No pressure. No games. Just a straightforward offer when you're ready.
              </div>
              <p>Wishing you the best whatever direction you go.</p>
            """,
            "cta_text": "Let's Reconnect",
            "cta_link": f"mailto:{CONFIG.get('reply_to') or CONFIG['smtp_user']}?subject=Reconnecting - {addr}"
        }
    }

    t = templates.get(day, templates[30])
    style = _base_style()
    html = f"""<!DOCTYPE html><html><head>{style}</head><body>
    <div class="wrap">
      <div class="header"><div class="header-logo">⬡ Aegis Capital RE</div></div>
      <div class="body">
        <h2>{t['headline']}</h2>
        {t['body']}
        <a href="{t['cta_link']}" class="cta">{t['cta_text']}</a>
        <p style="color:#999;font-size:13px;margin-top:24px;">— {from_name}<br>Aegis Capital RE · Houston Metro</p>
      </div>
      <div class="footer">
        This email was sent because you requested a cash offer from Aegis Capital RE.<br>
        Reply STOP to unsubscribe. We'll honor that immediately.
      </div>
    </div>
    </body></html>"""

    plain = f"{t['headline']}\n\n{addr}\n\nReply to this email or contact us directly.\n\n— {from_name}"
    return t["subject"], html, plain


# ─────────────────────────────────────────────────────────────────────────────
# DRIP RUNNER
# ─────────────────────────────────────────────────────────────────────────────

DRIP_DAYS = [1, 3, 7, 14, 30]


def run_drip(dry_run: bool = False):
    """
    For each active lead with a seller email, check which drip emails are due
    and send them if not already sent.
    """
    ensure_drip_table()
    conn = get_db()
    today = date.today()

    props = conn.execute("""
        SELECT * FROM properties
        WHERE status IN ('lead', 'analyzing')
        AND seller_email IS NOT NULL AND seller_email != ''
        AND date_added IS NOT NULL
    """).fetchall()

    sent_count = 0
    for p in props:
        try:
            days_since = (today - date.fromisoformat(p["date_added"])).days
        except Exception:
            continue

        for d in DRIP_DAYS:
            if days_since < d:
                break  # not yet time

            # Check if already sent
            already = conn.execute(
                "SELECT id FROM drip_log WHERE property_id=? AND day_num=?",
                (p["id"], d)
            ).fetchone()
            if already:
                continue

            subject, html, plain = drip_template(d, p)
            to_email = p["seller_email"]

            if dry_run:
                print(f"[DRY RUN] Day {d} → {to_email}: {subject[:60]}")
                conn.execute(
                    "INSERT OR IGNORE INTO drip_log (property_id, day_num, status) VALUES (?,?,'dry_run')",
                    (p["id"], d)
                )
            else:
                print(f"[DRIP] Day {d} → {to_email} (ID:{p['id']}): {subject[:60]}")
                ok = _send_email(to_email, subject, html, plain)
                status = "sent" if ok else "failed"
                conn.execute(
                    "INSERT OR IGNORE INTO drip_log (property_id, day_num, status) VALUES (?,?,?)",
                    (p["id"], d, status)
                )
                # Also log to deal_logs
                conn.execute(
                    "INSERT INTO deal_logs (property_id, event, details) VALUES (?,?,?)",
                    (p["id"], "drip_email", f"Day {d} drip sent to {to_email}")
                )
                sent_count += 1

    conn.commit()
    conn.close()
    print(f"Drip run complete. {sent_count} emails {'would be ' if dry_run else ''}sent.")
    return sent_count


# ─────────────────────────────────────────────────────────────────────────────
# HOT LEAD ALERTS
# ─────────────────────────────────────────────────────────────────────────────

def run_hot_alerts(dry_run: bool = False):
    """Score all leads and alert on hot ones not yet alerted today."""
    ensure_drip_table()
    scored = run_scoring()
    hot = [p for p in scored if p["score"] >= CONFIG["hot_score_threshold"]]

    if not hot:
        print("No hot leads to alert.")
        return

    conn = get_db()
    today_str = date.today().isoformat()
    alerted = 0

    for p in hot:
        # Check deal_logs for alert today
        already = conn.execute("""
            SELECT id FROM deal_logs
            WHERE property_id=? AND event='hot_lead_alert'
            AND DATE(timestamp)=?
        """, (p["id"], today_str)).fetchone()
        if already:
            continue

        msg = (
            f"🔥 HOT LEAD (Score {p['score']})\n"
            f"{p['address']}\n"
            f"ARV ${(p['arv'] or 0):,} | {p.get('motivation','?')}\n"
            f"Asking ${(p['asking_price'] or 0):,} | {p.get('condition','?')}\n"
            f"Source: {p.get('source','?')}"
        )

        if dry_run:
            print(f"[DRY RUN] Hot alert:\n{msg}\n")
        else:
            print(f"[HOT ALERT] {p['address']} — Score {p['score']}")
            # SMS you
            if CONFIG["your_cell"]:
                _send_sms(CONFIG["your_cell"], msg)
            # Email you
            if CONFIG["smtp_user"]:
                html = f"<pre style='font-family:monospace;font-size:14px;'>{msg}</pre>"
                _send_email(
                    CONFIG.get("reply_to") or CONFIG["smtp_user"],
                    f"🔥 Hot Lead Alert — Score {p['score']} — {p['address'].split(',')[0]}",
                    html, msg
                )
            conn.execute(
                "INSERT INTO deal_logs (property_id, event, details) VALUES (?,?,?)",
                (p["id"], "hot_lead_alert", f"Score {p['score']} — alerted")
            )
            alerted += 1

    conn.commit()
    conn.close()
    print(f"Hot lead alerts: {alerted} sent. ({len(hot)} hot leads total)")
    return alerted


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def print_scores():
    scored = run_scoring()
    print(f"\n{'─'*70}")
    print(f"  LEAD SCORES — {date.today()} — {len(scored)} active leads")
    print(f"{'─'*70}")
    for i, p in enumerate(scored[:15], 1):
        bar = '█' * (p['score'] // 10) + '░' * (10 - p['score'] // 10)
        tier = "🔥 HOT" if p['score'] >= 70 else "🌡️ WARM" if p['score'] >= 50 else "❄️  COLD"
        print(f"  {i:2}. [{bar}] {p['score']:2} {tier}  ID:{p['id']}  {p['address'][:40]}")
        bd = p.get('breakdown', {})
        print(f"      Motivation:{bd.get('motivation',0)} Equity:{bd.get('equity',0)} ARV:{bd.get('arv_fit',0)} Cond:{bd.get('condition',0)}")
    print(f"{'─'*70}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Aegis Drip + Lead Scoring')
    parser.add_argument('--run-drip', action='store_true', help='Send scheduled drip emails')
    parser.add_argument('--score',    action='store_true', help='Score and display all leads')
    parser.add_argument('--alerts',   action='store_true', help='Send hot lead alerts')
    parser.add_argument('--all',      action='store_true', help='Run everything')
    parser.add_argument('--dry-run',  action='store_true', help='Preview without sending')
    args = parser.parse_args()

    if not any([args.run_drip, args.score, args.alerts, args.all]):
        parser.print_help()
        sys.exit(0)

    ensure_drip_table()

    if args.score or args.all:
        print_scores()

    if args.run_drip or args.all:
        print("\n── Running drip sequence ──")
        run_drip(dry_run=args.dry_run)

    if args.alerts or args.all:
        print("\n── Running hot lead alerts ──")
        run_hot_alerts(dry_run=args.dry_run)
