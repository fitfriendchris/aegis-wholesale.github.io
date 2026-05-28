#!/usr/bin/env python3
"""
Aegis Capital RE Wholesale - SQLite API Server
Replaces browser localStorage with real database persistence.
Run: python3 api_server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

DB_PATH = 'aegis.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route('/api/properties', methods=['GET'])
def get_properties():
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    query = "SELECT * FROM properties WHERE 1=1"
    params = []
    
    if request.args.get('status'):
        query += " AND status = ?"
        params.append(request.args.get('status'))
    if request.args.get('arv_min'):
        query += " AND arv >= ?"
        params.append(int(request.args.get('arv_min')))
    if request.args.get('arv_max'):
        query += " AND arv <= ?"
        params.append(int(request.args.get('arv_max')))
    if request.args.get('city'):
        query += " AND city LIKE ?"
        params.append(f"%{request.args.get('city')}%")
    if request.args.get('active'):
        query += " AND status IN ('lead', 'analyzing', 'under_contract')"
    
    query += " ORDER BY date_updated DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/api/properties/<int:prop_id>', methods=['GET'])
def get_property(prop_id):
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties WHERE id = ?", (prop_id,))
    row = cursor.fetchone()
    conn.close()
    return jsonify(row) if row else jsonify({"error": "Not found"}), 404

@app.route('/api/properties', methods=['POST'])
def add_property():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    # Calculate MAO if not provided
    arv = data.get('arv', 0)
    repairs = data.get('repair_estimate', 0)
    mao = data.get('mao', int(arv * 0.70 - repairs))
    
    cursor.execute("""
        INSERT INTO properties (address, city, state, zip, beds, baths, sqft, condition, 
                                year_built, arv, repair_estimate, mao, asking_price, 
                                assignment_fee, status, source, motivation, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('address'), data.get('city', 'Houston'), data.get('state', 'TX'),
        data.get('zip'), data.get('beds'), data.get('baths'), data.get('sqft'),
        data.get('condition'), data.get('year_built'), arv, repairs, mao,
        data.get('asking_price'), data.get('assignment_fee'),
        data.get('status', 'lead'), data.get('source'), data.get('motivation'), data.get('notes')
    ))
    
    prop_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": prop_id, "message": "Property added"}), 201

@app.route('/api/properties/<int:prop_id>', methods=['PUT'])
def update_property(prop_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    # Build dynamic update
    allowed = ['address','city','state','zip','beds','baths','sqft','condition',
               'year_built','arv','repair_estimate','mao','asking_price',
               'assignment_fee','status','source','motivation','notes']
    
    updates = []
    values = []
    for key in allowed:
        if key in data:
            updates.append(f"{key} = ?")
            values.append(data[key])
    
    if not updates:
        return jsonify({"error": "No valid fields"}), 400
    
    values.append(prop_id)
    cursor.execute(f"UPDATE properties SET {', '.join(updates)}, date_updated = CURRENT_DATE WHERE id = ?", values)
    conn.commit()
    conn.close()
    return jsonify({"message": "Updated"})

@app.route('/api/properties/<int:prop_id>', methods=['DELETE'])
def delete_property(prop_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Deleted"})

@app.route('/api/buyers', methods=['GET'])
def get_buyers():
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    # Optional filters
    arv = request.args.get('arv')
    state = request.args.get('state')

    query = "SELECT * FROM buyers WHERE 1=1"
    params = []
    if arv:
        query += " AND buy_box_min <= ? AND buy_box_max >= ?"
        params.extend([int(arv), int(arv)])
    if state:
        query += " AND preferred_states LIKE ?"
        params.append(f"%{state}%")
    query += " ORDER BY closing_time_days ASC, date_added DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/api/buyers', methods=['POST'])
def add_buyer():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO buyers (name, company, phone, email, buy_box_min, buy_box_max,
                            preferred_states, preferred_cities, property_types,
                            min_beds, max_rehab, cash_buyer, closing_time_days, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('name'), data.get('company'), data.get('phone'), data.get('email'),
        data.get('buy_box_min', 300000), data.get('buy_box_max', 500000),
        data.get('preferred_states', 'TX'), data.get('preferred_cities', 'Houston'),
        data.get('property_types', 'Single Family'),
        data.get('min_beds', 3), data.get('max_rehab', 75000),
        data.get('cash_buyer', True), data.get('closing_time_days', 14),
        data.get('notes', '')
    ))
    buyer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": buyer_id, "message": "Buyer added to list"}), 201

@app.route('/api/buyers/<int:buyer_id>', methods=['PUT'])
def update_buyer(buyer_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    allowed = ['name','company','phone','email','buy_box_min','buy_box_max',
               'preferred_states','preferred_cities','property_types',
               'min_beds','max_rehab','closing_time_days','notes']
    updates = [(k, data[k]) for k in allowed if k in data]
    if not updates:
        return jsonify({"error": "No valid fields"}), 400
    set_clause = ', '.join(f"{k} = ?" for k, _ in updates)
    values = [v for _, v in updates] + [buyer_id]
    cursor.execute(f"UPDATE buyers SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return jsonify({"message": "Buyer updated"})

@app.route('/api/buyers/<int:buyer_id>', methods=['DELETE'])
def delete_buyer(buyer_id):
    conn = get_db()
    conn.execute("DELETE FROM buyers WHERE id = ?", (buyer_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Buyer removed"})

@app.route('/api/buyers/match', methods=['GET'])
def match_for_arv():
    """Find all buyers who want a specific ARV — used by buyer-intake confirmation"""
    arv = request.args.get('arv', 400000)
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, company, closing_time_days, preferred_cities
        FROM buyers
        WHERE buy_box_min <= ? AND buy_box_max >= ?
        ORDER BY closing_time_days ASC
    """, (int(arv), int(arv)))
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"arv": arv, "matched_buyers": len(rows), "buyers": rows})

@app.route('/api/pipeline/summary', methods=['GET'])
def get_summary():
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_active,
            SUM(CASE WHEN status = 'under_contract' THEN 1 ELSE 0 END) as under_contract,
            SUM(CASE WHEN status = 'analyzing' THEN 1 ELSE 0 END) as analyzing,
            SUM(CASE WHEN status = 'lead' THEN 1 ELSE 0 END) as leads,
            SUM(assignment_fee) as total_pipeline_value,
            AVG(arv) as avg_arv
        FROM properties 
        WHERE status IN ('lead', 'analyzing', 'under_contract')
    """)
    summary = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as buyer_count FROM buyers")
    buyers = cursor.fetchone()
    summary['buyer_count'] = buyers['buyer_count']
    
    conn.close()
    return jsonify(summary)

@app.route('/api/pipeline/filter', methods=['GET'])
def filter_pipeline():
    """Filter properties by ARV range and other criteria"""
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    arv_min = request.args.get('arv_min', 350000)
    arv_max = request.args.get('arv_max', 450000)
    status = request.args.get('status', '')
    
    query = """
        SELECT *, 
            (arv * 0.70 - repair_estimate) as calculated_mao,
            (asking_price - (arv * 0.70 - repair_estimate)) as potential_profit
        FROM properties
        WHERE arv BETWEEN ? AND ? AND status != 'dead'
    """
    params = [arv_min, arv_max]
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY arv DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/api/match/<int:prop_id>', methods=['GET'])
def match_buyers(prop_id):
    """Find buyers whose buy box matches this property"""
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM properties WHERE id = ?", (prop_id,))
    prop = cursor.fetchone()
    
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    
    cursor.execute("""
        SELECT *, 
            CASE 
                WHEN ? BETWEEN buy_box_min AND buy_box_max THEN 100
                WHEN ? BETWEEN buy_box_min AND buy_box_max THEN 80
                ELSE 50
            END as match_score
        FROM buyers
        WHERE buy_box_min <= ? AND buy_box_max >= ?
        ORDER BY match_score DESC
    """, (prop['arv'], prop['asking_price'], prop['arv'], prop['arv']))
    
    buyers = cursor.fetchall()
    conn.close()
    return jsonify({"property": prop, "matches": buyers})

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Remove stale leads older than 90 days"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM properties 
        WHERE date_added < date('now', '-90 days') 
        AND status = 'lead'
    """)
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return jsonify({"deleted": deleted, "message": f"Removed {deleted} stale leads"})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# ─────────────────────────────────────────────────────────────────────────────
# CLAUDE DISPATCH  –  natural language command center for phone use
# ─────────────────────────────────────────────────────────────────────────────

def _score_property(p):
    """Simple lead score 0-99 for sorting hot leads."""
    score = 0
    hot_keywords = ['foreclosure', 'divorce', 'financial', 'probate', 'estate', 'tax', 'behind']
    if any(k in (p.get('motivation') or '').lower() for k in hot_keywords):
        score += 40
    else:
        score += 15
    if p.get('arv') and p.get('asking_price'):
        equity = (p['arv'] - p['asking_price']) / p['arv']
        score += min(30, int(equity * 100))
    if 350000 <= (p.get('arv') or 0) <= 450000:
        score += 20
    elif 300000 <= (p.get('arv') or 0) <= 500000:
        score += 10
    cond = p.get('condition', '')
    if cond in ('C4', 'C5'):
        score += 10
    return min(99, score)


@app.route('/api/ask', methods=['POST'])
def ask():
    """
    Natural language dispatch endpoint.
    POST {"q": "show me hot leads"} → structured JSON response with reply + data.
    Handles: pipeline summary, hot leads, buyer matching, status updates,
             adding leads, filtering by ARV, fastest closers, property lookup.
    """
    body = request.json or {}
    q = (body.get('q') or '').lower().strip()
    if not q:
        return jsonify({"reply": "Ask me anything about your pipeline!", "type": "info"})

    conn = get_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()

    # ── PIPELINE SUMMARY ──────────────────────────────────────────────────────
    if any(k in q for k in ['summary', 'pipeline', 'overview', 'stats', 'how many', 'status']):
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status='lead') as leads,
                COUNT(*) FILTER (WHERE status='analyzing') as analyzing,
                COUNT(*) FILTER (WHERE status='under_contract') as under_contract,
                COUNT(*) FILTER (WHERE status='closed') as closed,
                SUM(assignment_fee) FILTER (WHERE status NOT IN ('dead','closed')) as pipeline_value,
                SUM(assignment_fee) FILTER (WHERE status='closed') as earned,
                AVG(arv) FILTER (WHERE status NOT IN ('dead','closed')) as avg_arv
            FROM properties WHERE status != 'dead'
        """)
        s = cur.fetchone()
        cur.execute("SELECT COUNT(*) as n FROM buyers")
        bc = cur.fetchone()['n']
        conn.close()
        reply = (
            f"📊 Pipeline snapshot:\n"
            f"• {s['leads']} leads  |  {s['analyzing']} analyzing  |  {s['under_contract']} under contract  |  {s['closed']} closed\n"
            f"• Pipeline value: ${(s['pipeline_value'] or 0):,.0f}\n"
            f"• Avg ARV: ${(s['avg_arv'] or 0):,.0f}\n"
            f"• Buyer list: {bc} active buyers"
        )
        return jsonify({"reply": reply, "type": "summary", "data": dict(s), "buyer_count": bc})

    # ── HOT LEADS ─────────────────────────────────────────────────────────────
    if any(k in q for k in ['hot', 'best', 'top lead', 'priority', 'urgent', 'fire']):
        cur.execute("SELECT * FROM properties WHERE status IN ('lead','analyzing') ORDER BY date_added DESC")
        rows = cur.fetchall()
        conn.close()
        scored = sorted(rows, key=_score_property, reverse=True)[:5]
        lines = [f"🔥 Top {len(scored)} hot leads:"]
        for i, p in enumerate(scored, 1):
            lines.append(f"{i}. {p['address']} (ID:{p['id']})\n   ARV ${(p['arv'] or 0):,} · {p['motivation'] or '?'} · Score {_score_property(p)}")
        reply = '\n'.join(lines)
        return jsonify({"reply": reply, "type": "leads", "data": scored})

    # ── ALL ACTIVE LEADS ──────────────────────────────────────────────────────
    if any(k in q for k in ['all lead', 'show lead', 'list lead', 'my lead']):
        cur.execute("SELECT * FROM properties WHERE status='lead' ORDER BY date_added DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        lines = [f"📋 {len(rows)} leads:"]
        for p in rows:
            lines.append(f"• {p['address']} — ARV ${(p['arv'] or 0):,} [{p.get('condition','?')}]")
        return jsonify({"reply": '\n'.join(lines), "type": "leads", "data": rows})

    # ── UNDER CONTRACT ────────────────────────────────────────────────────────
    if any(k in q for k in ['contract', 'under contract', 'contracted']):
        cur.execute("SELECT * FROM properties WHERE status='under_contract'")
        rows = cur.fetchall()
        conn.close()
        total = sum(p.get('assignment_fee') or 0 for p in rows)
        lines = [f"📝 {len(rows)} under contract — ${total:,} in fees:"]
        for p in rows:
            lines.append(f"• {p['address']} — Fee ${(p.get('assignment_fee') or 0):,}")
        return jsonify({"reply": '\n'.join(lines), "type": "contracts", "data": rows})

    # ── MATCH BUYERS for a property ID ───────────────────────────────────────
    import re
    match_id = re.search(r'(?:match|buyer).*?(?:for|id|#)?\s*(\d+)', q)
    if match_id or any(k in q for k in ['match buyer', 'find buyer', 'who buys']):
        pid = int(match_id.group(1)) if match_id else None
        if not pid:
            # Try to find a property from address keywords
            words = [w for w in q.split() if len(w) > 4]
            cur.execute("SELECT id, address, arv FROM properties WHERE status IN ('lead','analyzing','under_contract') LIMIT 1")
            p = cur.fetchone()
            pid = p['id'] if p else None
        if pid:
            cur.execute("SELECT * FROM properties WHERE id=?", (pid,))
            prop = cur.fetchone()
            if prop:
                cur.execute("""
                    SELECT name, company, closing_time_days, preferred_cities
                    FROM buyers WHERE buy_box_min <= ? AND buy_box_max >= ?
                    ORDER BY closing_time_days ASC LIMIT 5
                """, (prop['arv'], prop['arv']))
                buyers = cur.fetchall()
                conn.close()
                lines = [f"🎯 Buyers for {prop['address']} (ARV ${prop['arv']:,}):"]
                for b in buyers:
                    lines.append(f"• {b['name']} @ {b['company']} — closes in {b['closing_time_days']} days")
                if not buyers:
                    lines.append("No buyers in range. Consider expanding buy box.")
                return jsonify({"reply": '\n'.join(lines), "type": "match", "property": prop, "buyers": buyers})
        conn.close()
        return jsonify({"reply": "Specify a property ID, e.g. 'match buyers for ID 3'", "type": "error"})

    # ── FASTEST CLOSERS ───────────────────────────────────────────────────────
    if any(k in q for k in ['fastest', 'quick close', 'close fast', 'cash buyer', 'quick buyer']):
        cur.execute("SELECT name, company, closing_time_days, buy_box_min, buy_box_max FROM buyers ORDER BY closing_time_days ASC LIMIT 5")
        rows = cur.fetchall()
        conn.close()
        lines = ["⚡ Fastest closers:"]
        for b in rows:
            lines.append(f"• {b['name']} ({b['company']}) — {b['closing_time_days']} days | ${b['buy_box_min']:,}–${b['buy_box_max']:,}")
        return jsonify({"reply": '\n'.join(lines), "type": "buyers", "data": rows})

    # ── ARV FILTER ────────────────────────────────────────────────────────────
    arv_match = re.search(r'(\d{2,3})k?\s*(?:arv|to|–|-)\s*(\d{2,3})k?', q)
    if arv_match or '400k' in q or '$400' in q or 'four hundred' in q:
        if arv_match:
            lo = int(arv_match.group(1)) * 1000
            hi = int(arv_match.group(2)) * 1000
        else:
            lo, hi = 350000, 450000
        cur.execute("SELECT * FROM properties WHERE arv BETWEEN ? AND ? AND status != 'dead' ORDER BY arv DESC", (lo, hi))
        rows = cur.fetchall()
        conn.close()
        lines = [f"🏠 {len(rows)} deals in ${lo//1000}K–${hi//1000}K ARV range:"]
        for p in rows[:7]:
            lines.append(f"• {p['address']} — ARV ${(p['arv'] or 0):,} | {p['status']}")
        if len(rows) > 7:
            lines.append(f"... and {len(rows)-7} more")
        return jsonify({"reply": '\n'.join(lines), "type": "filter", "data": rows})

    # ── UPDATE STATUS ─────────────────────────────────────────────────────────
    update_match = re.search(r'(?:update|move|set|change)\s+(?:id\s*#?)?(\d+)\s+to\s+(lead|analyzing|under.?contract|closed|dead)', q)
    if update_match:
        pid = int(update_match.group(1))
        new_status = update_match.group(2).replace(' ', '_').replace('under_contract', 'under_contract')
        cur.execute("SELECT address FROM properties WHERE id=?", (pid,))
        prop = cur.fetchone()
        if prop:
            cur.execute("UPDATE properties SET status=?, date_updated=CURRENT_DATE WHERE id=?", (new_status, pid))
            cur.execute("INSERT INTO deal_logs (property_id, event, details) VALUES (?,?,?)",
                       (pid, 'status_change', f'Mobile dispatch: → {new_status}'))
            conn.commit()
            conn.close()
            return jsonify({"reply": f"✅ Updated {prop['address']} → {new_status}", "type": "update"})
        conn.close()
        return jsonify({"reply": f"Property ID {pid} not found.", "type": "error"})

    # ── ADD QUICK LEAD ────────────────────────────────────────────────────────
    if 'add lead' in q or 'new lead' in q or 'add property' in q:
        conn.close()
        return jsonify({
            "reply": "To add a lead, provide: Address, City, Beds/Baths, ARV estimate, and Condition (C1-C6). Use the seller intake form or POST to /api/properties.",
            "type": "info",
            "action": "open_intake"
        })

    # ── PROPERTY LOOKUP ───────────────────────────────────────────────────────
    id_lookup = re.search(r'(?:property|deal|id)\s*#?\s*(\d+)', q)
    if id_lookup:
        pid = int(id_lookup.group(1))
        cur.execute("SELECT * FROM properties WHERE id=?", (pid,))
        p = cur.fetchone()
        conn.close()
        if p:
            mao = int((p['arv'] or 0) * 0.70 - (p['repair_estimate'] or 0))
            reply = (
                f"🏠 Property #{pid}:\n"
                f"📍 {p['address']}\n"
                f"🔢 {p.get('beds','?')}bd/{p.get('baths','?')}ba · {p.get('sqft','?')} sqft · {p.get('condition','?')}\n"
                f"💰 ARV ${(p['arv'] or 0):,} | Repairs ${(p['repair_estimate'] or 0):,} | MAO ${mao:,}\n"
                f"📋 Status: {p['status']} | Source: {p.get('source','?')}\n"
                f"💡 {p.get('motivation','?')}"
            )
            return jsonify({"reply": reply, "type": "property", "data": p})
        return jsonify({"reply": f"No property found with ID {pid}.", "type": "error"})

    # ── FALLBACK ──────────────────────────────────────────────────────────────
    conn.close()
    return jsonify({
        "reply": (
            "I can help with:\n"
            "• 'pipeline summary' — stats overview\n"
            "• 'hot leads' — top scored leads\n"
            "• 'under contract' — current deals\n"
            "• 'match buyers for ID 5' — find buyers\n"
            "• 'fastest closers' — quick-close buyers\n"
            "• '400k deals' — filter by ARV\n"
            "• 'update ID 3 to analyzing' — change status\n"
            "• 'property 7' — property details"
        ),
        "type": "help"
    })


if __name__ == '__main__':
    print("🏛️ Aegis Capital API Server")
    print("=" * 40)
    print("Endpoints:")
    print("  GET  /api/properties")
    print("  GET  /api/properties?arv_min=350000&arv_max=450000&active=1")
    print("  GET  /api/pipeline/summary")
    print("  GET  /api/pipeline/filter?arv_min=350000&arv_max=450000")
    print("  GET  /api/match/<property_id>")
    print("=" * 40)
    app.run(host='0.0.0.0', port=5001, debug=True)
