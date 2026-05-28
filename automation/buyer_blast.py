#!/usr/bin/env python3
"""
Aegis Capital - Buyer Blast System
When you add a deal to the DB, blast matched buyers immediately.

Usage:
    python3 automation/buyer_blast.py <property_id>
    python3 automation/buyer_blast.py 12 --preview   # preview email without sending
    python3 automation/buyer_blast.py 12 --sms       # also send SMS via Twilio

Trigger automatically from api_server.py by calling this after POST /api/properties
"""

import os
import sys
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────────────────────────────
CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your@gmail.com",        # ← YOUR EMAIL (from address)
    "smtp_pass": "your-app-password",      # ← Gmail App Password
    "your_name": "Chris | Aegis Capital",
    "your_phone": "(713) 555-0000",        # ← YOUR PHONE
    "your_email": "deals@aegiscapital.com",# ← Your deals email
    
    # Twilio (optional, for SMS)
    "twilio_sid": "",                       # ← Twilio Account SID
    "twilio_token": "",                     # ← Twilio Auth Token
    "twilio_from": "+1XXXXXXXXXX",         # ← Your Twilio number

    "db_path": os.path.join(os.path.dirname(__file__), '..', 'backend', 'aegis.db'),
}
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(CONFIG['db_path'])
    conn.row_factory = sqlite3.Row
    return conn

def get_property(prop_id):
    conn = get_db()
    prop = conn.execute("SELECT * FROM properties WHERE id = ?", (prop_id,)).fetchone()
    conn.close()
    return dict(prop) if prop else None

def get_matched_buyers(prop):
    """Find buyers whose buy box matches this property"""
    conn = get_db()
    arv = prop['arv']
    buyers = conn.execute("""
        SELECT * FROM buyers
        WHERE buy_box_min <= ? AND buy_box_max >= ?
        AND (preferred_states IS NULL OR preferred_states LIKE ?)
        ORDER BY closing_time_days ASC
    """, (arv, arv, f"%{prop.get('state','TX')}%")).fetchall()
    conn.close()
    return [dict(b) for b in buyers]

def build_buyer_email(prop, buyer):
    """Build personalized deal email for a specific buyer"""
    arv = prop.get('arv', 0)
    mao = prop.get('mao', 0) or int(arv * 0.70)
    asking = prop.get('asking_price', 0)
    repairs = prop.get('repair_estimate', 0)
    assignment = prop.get('assignment_fee', 0)
    spread = mao - (asking or mao)

    buyer_name = buyer.get('name', 'Investor')
    first_name = buyer_name.split()[0]

    subject = f"🏠 Off-Market Deal | ${arv:,} ARV | {prop.get('city','Houston')}, TX | Aegis Capital"

    body = f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">

<div style="background:#1A3A5C;color:white;padding:20px 24px;border-radius:8px 8px 0 0">
  <h1 style="margin:0;font-size:22px">🏛️ Aegis Capital | New Deal Alert</h1>
  <p style="margin:4px 0 0;opacity:0.75;font-size:13px">Off-Market | Wholesale | Immediate Availability</p>
</div>

<div style="background:#FFF8F0;padding:24px">

<p style="font-size:16px">Hey {first_name},</p>

<p>Just locked up a new off-market deal that hits your buy box. Details below:</p>

<div style="background:white;border-radius:8px;padding:20px;border:1px solid #e5e7eb;margin:16px 0">
  <h2 style="color:#1A3A5C;margin:0 0 12px">{prop.get('address')}</h2>
  
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
    <div>
      <div style="font-size:12px;color:#6b7280;text-transform:uppercase;font-weight:bold">ARV</div>
      <div style="font-size:24px;font-weight:bold;color:#C9A227">${arv:,}</div>
    </div>
    <div>
      <div style="font-size:12px;color:#6b7280;text-transform:uppercase;font-weight:bold">Asking Price</div>
      <div style="font-size:24px;font-weight:bold;color:#1A3A5C">${asking:,}</div>
    </div>
    <div>
      <div style="font-size:12px;color:#6b7280;text-transform:uppercase;font-weight:bold">Est. Repairs</div>
      <div style="font-size:20px;font-weight:bold">${repairs:,}</div>
    </div>
    <div>
      <div style="font-size:12px;color:#6b7280;text-transform:uppercase;font-weight:bold">Your Profit Potential</div>
      <div style="font-size:20px;font-weight:bold;color:#10B981">${(arv - asking - repairs):,}+</div>
    </div>
  </div>
  
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0">
  
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:14px">
    <div><b>{prop.get('beds','?')}</b> Beds</div>
    <div><b>{prop.get('baths','?')}</b> Baths</div>
    <div><b>{prop.get('sqft','?'):,}</b> SqFt</div>
    <div>Built <b>{prop.get('year_built','?')}</b></div>
    <div>Condition <b>{prop.get('condition','?')}</b></div>
    <div>Zip <b>{prop.get('zip','?')}</b></div>
  </div>
  
  {'<div style="background:#FEF3C7;border-radius:6px;padding:10px;margin-top:12px;font-size:13px"><b>Seller motivation:</b> ' + prop.get("motivation","") + '</div>' if prop.get('motivation') else ''}
  {'<div style="background:#F0FDF4;border-radius:6px;padding:10px;margin-top:8px;font-size:13px"><b>Notes:</b> ' + prop.get("notes","") + '</div>' if prop.get('notes') else ''}
</div>

<div style="background:#1A3A5C;color:white;border-radius:8px;padding:16px;text-align:center;margin:16px 0">
  <div style="font-size:13px;opacity:0.75;margin-bottom:4px">ASSIGNMENT FEE</div>
  <div style="font-size:28px;font-weight:bold;color:#C9A227">${assignment:,}</div>
</div>

<p><b>⚡ This deal moves fast.</b> Reply "INTERESTED" and I'll send the full comp package + contract within the hour.</p>

<p>
  <b>{CONFIG['your_name']}</b><br>
  📞 {CONFIG['your_phone']}<br>
  📧 {CONFIG['your_email']}<br>
  <i>Aegis Capital RE Wholesale</i>
</p>

<p style="font-size:11px;color:#9ca3af;border-top:1px solid #e5e7eb;padding-top:12px;margin-top:20px">
  You're receiving this because you're on our active buyer list for {prop.get('city','Houston')}, TX properties. 
  Reply STOP to be removed.
</p>

</div>
</body></html>"""

    return subject, body

def send_blast(prop_id, preview=False, send_sms=False):
    prop = get_property(prop_id)
    if not prop:
        print(f"❌ Property {prop_id} not found")
        return

    buyers = get_matched_buyers(prop)
    if not buyers:
        print(f"⚠️  No buyers matched for property {prop_id}")
        print(f"   ARV: ${prop.get('arv',0):,} | State: {prop.get('state','TX')}")
        return

    print(f"\n🏠 Deal: {prop['address']}")
    print(f"   ARV: ${prop.get('arv',0):,} | Asking: ${prop.get('asking_price',0):,}")
    print(f"   Matched buyers: {len(buyers)}\n")

    email_configured = CONFIG['smtp_user'] != 'your@gmail.com'
    sent = 0

    for buyer in buyers:
        subject, body = build_buyer_email(prop, buyer)
        
        if preview:
            print(f"  📧 PREVIEW — To: {buyer.get('name')} <{buyer.get('email')}>")
            print(f"     Subject: {subject}")
            print(f"     [Full HTML email would be sent]")
            continue

        if not email_configured:
            print(f"  ⚠️  Email not configured — would send to: {buyer.get('name')} ({buyer.get('email')})")
            continue

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{CONFIG['your_name']} <{CONFIG['smtp_user']}>"
            msg['To'] = f"{buyer.get('name')} <{buyer.get('email')}>"
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(CONFIG['smtp_host'], CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(CONFIG['smtp_user'], CONFIG['smtp_pass'])
                server.send_message(msg)
            
            print(f"  ✅ Sent to {buyer['name']} ({buyer['email']})")
            sent += 1

        except Exception as e:
            print(f"  ❌ Failed to send to {buyer['name']}: {e}")

        # Optional SMS via Twilio
        if send_sms and CONFIG['twilio_sid'] and buyer.get('phone'):
            try:
                from twilio.rest import Client
                client = Client(CONFIG['twilio_sid'], CONFIG['twilio_token'])
                sms_body = (
                    f"🏠 NEW DEAL — Aegis Capital\n"
                    f"{prop['address']}\n"
                    f"ARV: ${prop.get('arv',0):,} | Asking: ${prop.get('asking_price',0):,}\n"
                    f"Reply YES for full package | {CONFIG['your_phone']}"
                )
                client.messages.create(
                    body=sms_body,
                    from_=CONFIG['twilio_from'],
                    to=buyer['phone']
                )
                print(f"  📱 SMS sent to {buyer['name']} ({buyer['phone']})")
            except Exception as e:
                print(f"  ⚠️  SMS failed: {e}")

    if not preview and email_configured:
        print(f"\n✅ Blast complete: {sent}/{len(buyers)} emails sent")
        # Log the blast
        conn = get_db()
        conn.execute("""
            INSERT INTO deal_logs (property_id, event, details)
            VALUES (?, 'buyer_blast', ?)
        """, (prop_id, f"Blasted {sent} buyers"))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 automation/buyer_blast.py <property_id> [--preview] [--sms]")
        sys.exit(1)
    
    prop_id = int(sys.argv[1])
    preview = '--preview' in sys.argv
    sms = '--sms' in sys.argv
    
    send_blast(prop_id, preview=preview, send_sms=sms)
