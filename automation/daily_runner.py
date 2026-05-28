#!/usr/bin/env python3
"""
Aegis Capital - Daily Automation Runner
Runs every morning to: import new leads, run matching, send digest.

Setup (runs at 9 AM daily):
    crontab -e
    0 9 * * * cd ~/aegis-wholesale && python3 automation/daily_runner.py >> automation/runner.log 2>&1

Or run manually: python3 automation/daily_runner.py
"""

import os
import sys
import sqlite3
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─── CONFIG (edit these) ───────────────────────────────────────────────────────
CONFIG = {
    # Your email settings (Gmail App Password recommended)
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your@gmail.com",       # ← YOUR EMAIL
    "smtp_pass": "your-app-password",     # ← Gmail App Password
    "digest_to": "your@gmail.com",        # ← Where to send daily digest

    # PropStream export folder (auto-import if new CSV found)
    "propstream_watch_dir": os.path.expanduser("~/Downloads"),
    "propstream_prefix": "propstream_",   # Files starting with this get imported

    # Target ARV range
    "arv_min": 350000,
    "arv_max": 450000,

    # Database path
    "db_path": os.path.join(os.path.dirname(__file__), '..', 'backend', 'aegis.db'),
}
# ──────────────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(CONFIG['db_path'])
    conn.row_factory = sqlite3.Row
    return conn

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")

def scan_for_new_csvs():
    """Auto-import any new PropStream CSVs from Downloads folder"""
    watch_dir = CONFIG['propstream_watch_dir']
    prefix = CONFIG['propstream_prefix']
    imported_log = os.path.join(os.path.dirname(__file__), 'imported_files.txt')
    
    already_imported = set()
    if os.path.exists(imported_log):
        with open(imported_log) as f:
            already_imported = set(f.read().splitlines())
    
    new_files = []
    if os.path.exists(watch_dir):
        for fname in os.listdir(watch_dir):
            if fname.lower().startswith(prefix.lower()) and fname.endswith('.csv'):
                full_path = os.path.join(watch_dir, fname)
                if full_path not in already_imported:
                    new_files.append(full_path)
    
    for fpath in new_files:
        log(f"📥 Found new PropStream file: {os.path.basename(fpath)}")
        # Import it
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from import_csv import import_csv
        import_csv(fpath, source='PropStream')
        
        # Mark as imported
        with open(imported_log, 'a') as f:
            f.write(fpath + '\n')
        log(f"✅ Imported: {os.path.basename(fpath)}")
    
    return len(new_files)

def get_todays_stats():
    """Pull today's pipeline stats from DB"""
    conn = get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    stats = {}
    
    # New leads today
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM properties WHERE date_added >= ?", (today,)
    ).fetchone()
    stats['new_leads_today'] = row['cnt']
    
    # Deals in $400K range
    row = conn.execute("""
        SELECT COUNT(*) as cnt, AVG(arv) as avg_arv, SUM(assignment_fee) as total_fees
        FROM properties 
        WHERE arv BETWEEN ? AND ? AND status NOT IN ('dead','closed')
    """, (CONFIG['arv_min'], CONFIG['arv_max'])).fetchone()
    stats['deals_400k'] = row['cnt']
    stats['avg_arv'] = int(row['avg_arv'] or 0)
    stats['pipeline_value'] = int(row['total_fees'] or 0)
    
    # Under contract
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM properties WHERE status='under_contract'"
    ).fetchone()
    stats['under_contract'] = row['cnt']
    
    # Hot deals (price well below MAO)
    hot = conn.execute("""
        SELECT address, arv, asking_price, mao,
               (mao - asking_price) as spread
        FROM properties
        WHERE status IN ('lead','analyzing')
          AND asking_price > 0
          AND mao > asking_price
          AND arv BETWEEN ? AND ?
        ORDER BY spread DESC
        LIMIT 5
    """, (CONFIG['arv_min'], CONFIG['arv_max'])).fetchall()
    stats['hot_deals'] = [dict(h) for h in hot]
    
    # New leads (last 24h)
    new = conn.execute("""
        SELECT address, arv, mao, motivation, source
        FROM properties
        WHERE date_added >= ?
        ORDER BY date_added DESC
        LIMIT 10
    """, (yesterday,)).fetchall()
    stats['new_leads'] = [dict(n) for n in new]
    
    conn.close()
    return stats

def run_auto_matching():
    """For each new lead, log top buyer matches to deal_logs"""
    conn = get_db()
    
    # Get properties added in last 24h with no match log
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    props = conn.execute("""
        SELECT p.* FROM properties p
        WHERE p.date_added >= ?
        AND p.id NOT IN (
            SELECT DISTINCT property_id FROM deal_logs WHERE event = 'auto_matched'
        )
    """, (yesterday,)).fetchall()
    
    matched = 0
    for prop in props:
        arv = prop['arv']
        buyers = conn.execute("""
            SELECT name, company, email, phone, buy_box_min, buy_box_max, closing_time_days
            FROM buyers
            WHERE buy_box_min <= ? AND buy_box_max >= ?
            ORDER BY closing_time_days ASC
        """, (arv, arv)).fetchall()
        
        if buyers:
            match_summary = f"{len(buyers)} buyers matched. Top: {buyers[0]['name']} ({buyers[0]['company']})"
            conn.execute("""
                INSERT INTO deal_logs (property_id, event, details)
                VALUES (?, 'auto_matched', ?)
            """, (prop['id'], match_summary))
            matched += 1
    
    conn.commit()
    conn.close()
    log(f"🔗 Auto-matched {matched} new properties to buyers")
    return matched

def send_daily_digest(stats):
    """Email yourself a daily digest of the pipeline"""
    if CONFIG['smtp_user'] == 'your@gmail.com':
        log("⚠️  Email not configured — skipping digest (edit CONFIG in daily_runner.py)")
        return

    hot_html = ""
    for d in stats.get('hot_deals', []):
        spread = d.get('spread', 0)
        hot_html += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee">{d['address']}</td>
            <td style="padding:8px;border-bottom:1px solid #eee">${d['arv']:,}</td>
            <td style="padding:8px;border-bottom:1px solid #eee">${d['asking_price']:,}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;color:green;font-weight:bold">+${spread:,}</td>
        </tr>"""

    new_html = ""
    for l in stats.get('new_leads', []):
        new_html += f"<li>{l['address']} — ARV ${l.get('arv',0):,} | {l.get('motivation','')}</li>"

    body = f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
<div style="background:#1A3A5C;color:white;padding:20px;border-radius:8px 8px 0 0">
  <h1 style="margin:0">🏛️ Aegis Capital Daily Digest</h1>
  <p style="margin:5px 0 0;opacity:0.7">{datetime.now().strftime('%A, %B %d, %Y')}</p>
</div>

<div style="background:#FFF8F0;padding:20px">

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px">
  <div style="background:white;padding:16px;border-radius:8px;text-align:center;border:1px solid #e5e7eb">
    <div style="font-size:32px;font-weight:bold;color:#1A3A5C">{stats['new_leads_today']}</div>
    <div style="color:#6b7280;font-size:12px">New Leads Today</div>
  </div>
  <div style="background:white;padding:16px;border-radius:8px;text-align:center;border:1px solid #e5e7eb">
    <div style="font-size:32px;font-weight:bold;color:#C9A227">{stats['deals_400k']}</div>
    <div style="color:#6b7280;font-size:12px">~$400K ARV Deals</div>
  </div>
  <div style="background:white;padding:16px;border-radius:8px;text-align:center;border:1px solid #e5e7eb">
    <div style="font-size:32px;font-weight:bold;color:#10B981">{stats['under_contract']}</div>
    <div style="color:#6b7280;font-size:12px">Under Contract</div>
  </div>
</div>

<h2 style="color:#1A3A5C">🔥 Hot Deals (Price Below MAO)</h2>
<table style="width:100%;border-collapse:collapse;background:white;border-radius:8px;overflow:hidden">
  <tr style="background:#1A3A5C;color:white">
    <th style="padding:10px;text-align:left">Address</th>
    <th style="padding:10px">ARV</th>
    <th style="padding:10px">Asking</th>
    <th style="padding:10px">Spread</th>
  </tr>
  {hot_html or '<tr><td colspan="4" style="padding:16px;text-align:center;color:#9ca3af">No hot deals today</td></tr>'}
</table>

<h2 style="color:#1A3A5C;margin-top:20px">📍 New Leads (Last 24h)</h2>
<ul style="background:white;padding:16px 16px 16px 32px;border-radius:8px;margin:0">
  {new_html or '<li style="color:#9ca3af">No new leads yet — time to run a scan!</li>'}
</ul>

<p style="margin-top:20px;text-align:center">
  <a href="http://localhost:5001/api/pipeline/filter?arv_min=350000&arv_max=450000" 
     style="background:#1A3A5C;color:white;padding:12px 24px;border-radius:8px;text-decoration:none">
    View Full Pipeline →
  </a>
</p>

</div>
</body></html>"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📊 Aegis Daily: {stats['new_leads_today']} new leads | {stats['under_contract']} under contract"
        msg['From'] = CONFIG['smtp_user']
        msg['To'] = CONFIG['digest_to']
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(CONFIG['smtp_host'], CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(CONFIG['smtp_user'], CONFIG['smtp_pass'])
            server.send_message(msg)
        log(f"📧 Daily digest sent to {CONFIG['digest_to']}")
    except Exception as e:
        log(f"⚠️  Email failed: {e} (check SMTP config in daily_runner.py)")

def main():
    log("=" * 50)
    log("🏛️  AEGIS CAPITAL — Daily Runner Starting")
    log("=" * 50)

    # 1. Import any new PropStream CSVs
    n = scan_for_new_csvs()
    if n == 0:
        log("📭 No new PropStream exports found in ~/Downloads")
        log("   → Export from PropStream and name file: propstream_YYYY-MM-DD.csv")

    # 2. Auto-match new properties
    run_auto_matching()

    # 3. Get pipeline stats
    stats = get_todays_stats()
    log(f"📊 Pipeline: {stats['deals_400k']} deals @ ~$400K ARV | {stats['under_contract']} under contract")
    
    if stats['hot_deals']:
        log(f"🔥 {len(stats['hot_deals'])} HOT deals (asking below MAO):")
        for d in stats['hot_deals']:
            log(f"   {d['address']} — spread: +${d['spread']:,}")

    # 4. Send digest
    send_daily_digest(stats)

    # 5. Drip sequences + lead scoring + hot alerts
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from drip_and_score import run_drip, run_hot_alerts, run_scoring
        log("── Scoring leads ──")
        scored = run_scoring()
        hot_count = sum(1 for p in scored if p['score'] >= 70)
        warm_count = sum(1 for p in scored if 50 <= p['score'] < 70)
        log(f"🎯 Lead scores: {hot_count} hot | {warm_count} warm | {len(scored)} total")
        if scored:
            top = scored[0]
            log(f"   Top: {top['address']} (Score {top['score']})")

        log("── Drip emails ──")
        drip_sent = run_drip()
        log(f"📬 Drip: {drip_sent} emails sent")

        log("── Hot lead alerts ──")
        run_hot_alerts()
    except Exception as e:
        log(f"⚠️  Drip/scoring error: {e}")

    log("✅ Daily runner complete")
    log("=" * 50)

if __name__ == '__main__':
    main()
