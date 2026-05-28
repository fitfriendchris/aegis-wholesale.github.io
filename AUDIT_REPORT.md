# 🏛️ AEGIS CAPITAL — DEEP PLAN AUDIT
**Date:** May 28, 2026 | **Market Focus:** Houston Metro, ~$400K ARV

---

## ✅ WHAT'S BUILT (Confirmed Working)

| Module | Status | Notes |
|---|---|---|
| Flask/SQLite Backend | ✅ Solid | Real persistence, 9 API endpoints |
| Dashboard (dashboard.html) | ✅ | Stats, filters, deal table |
| Deal Analyzer (deal-analyzer.html) | ✅ | MAO calc, 70% rule |
| Buyer Matching Engine (matcher.html) | ✅ | Buy-box matching logic |
| Buyer Database (buyers.html) | ✅ UI | 8 seed buyers (ALL FAKE) |
| Lead Finder (lead-finder.html) | ✅ Guide | Manual guide only — no automation |
| Daily Scanner (scanner.html) | ⚠️ Shell | Buttons exist, no real API calls |
| Contract Generator | ⚠️ Partial | HTML print only, no PDF/e-sign |
| Email Templates | ⚠️ Static | No sending mechanism |
| $400K ARV DB View | ✅ | `deals_400k` view in schema |
| Pipeline Summary API | ✅ | `/api/pipeline/summary` working |
| Auto-Matcher API | ✅ | `/api/match/<id>` working |

---

## 🔴 CRITICAL GAPS (P0 — Blocking Real Business)

### GAP 1: ALL DATA IS FAKE
- 26 properties = seed data, not real deals
- 8 buyers = fictional, no real contacts
- `import_csv.py` referenced in README — **does not exist**
- **Fix:** `import_csv.py` created (see below) + PropStream export workflow

### GAP 2: NO LIVE DATA PIPELINE
- Scanner buttons call `runScan()` JS — makes no real API calls
- No PropStream/BatchLeads CSV auto-import scheduler
- No county records pull (lis pendens, probate, tax delinquent)
- **Fix:** `automation/daily_runner.py` scheduler created (see below)

### GAP 3: BUYER LIST IS TOO THIN
- Need 50-200 active buyers at $400K ARV range
- Missing granular criteria: zip codes, condition grades, hold strategy
- No proof of funds tracking, no deal velocity tracking
- **Fix:** `buyer-intake.html` built with full $400K criteria form

### GAP 4: NO OUTREACH AUTOMATION
- Email templates exist but zero sending capability
- No SMS blast when deal goes under contract
- No seller follow-up drip sequence
- **Fix:** Add `automation/buyer_blast.py` + SMTP config instructions

---

## 🟡 IMPORTANT GAPS (P1 — Limits Scale)

### GAP 5: NO REAL ARV VALIDATION
- ARV is manually typed — no comp verification
- Should cross-reference Zillow/Redfin before locking MAO
- Workaround: PropStream's Wholesale Value AVM (70% of estimated value)

### GAP 6: CONTRACT NOT PRODUCTION-READY
- HTML print only — not a real signed document
- Texas requires specific disclosures for equitable interest marketing
- Missing: Assignment of Contract form, Disclosure Notice
- Fix needed: PandaDoc/DocuSign integration OR attorney-reviewed PDF template

### GAP 7: NO SELLER INTAKE FORM (Public-Facing)
- No way for motivated sellers to submit their own info
- Missing landing page / seller lead capture
- Fix: `seller-intake.html` page for Facebook/Google ad traffic

### GAP 8: NO KPI TRACKING
- No conversion rate by source (PropStream vs cold call vs DFD)
- No revenue tracking by month
- No source ROI — can't tell which lead source makes money
- Fix: Add `source_tracking` column, build analytics view

---

## 🟢 $400K ARV — BUYER CRITERIA INTELLIGENCE

Based on 2026 Houston market research, here's what buyers actually want:

### Fix-and-Flip Buyers (70% of your buyer pool)
| Criteria | Requirement |
|---|---|
| ARV Range | $350K–$450K |
| Max Purchase | ARV × 0.70 − repairs |
| Repair Tolerance | Up to $50K cosmetic; $75K+ for experienced operators |
| Beds/Baths | 3+ BR / 2+ BA minimum |
| Sqft | 1,400–2,500 sq ft sweet spot |
| Condition | C2–C4 preferred; C5 only if price is right |
| Year Built | 1980+ preferred; 1960s+ needs significant discount |
| School District | Katy ISD, Klein, Cy-Fair, Clear Creek = premium pricing |
| Flood Zone | Must be Zone X (AE = deal killer for most) |
| Foundation | Slab only (pier-and-beam needs specialist buyer) |
| Close Time | 7–21 days cash close |
| Assignment Fee | $10K–$25K (typical), up to $30K on premium deals |

### BRRRR/Buy-Hold Buyers (20% of buyer pool)
| Criteria | Requirement |
|---|---|
| Purchase Price | Max 75% ARV |
| Target Rent | $2,200–$2,800/mo for $400K ARV homes |
| Cap Rate | 7%+ preferred |
| Hold Strategy | Long-term, wants C1–C3 condition |
| Close Time | 10–21 days |

### Institutional Buyers / Hedge Funds (10% — high volume)
| Criteria | Requirement |
|---|---|
| Volume | 5–20 deals/month |
| ARV | $300K–$500K |
| Condition | C1–C3 only, move-in ready preferred |
| Garage | Attached 2-car required for most |
| HOA | Will accept but needs full disclosure |
| Close Time | 10–14 days |
| POF | Wire transfer, same-day confirmation |

### TOP ZIP CODES at $400K ARV (Houston Metro 2026)
- **77449** (Katy) — hot, Katy ISD, 3-4BR SFR
- **77379** (Spring/Champions) — Klein ISD, family-friendly
- **77429** (Cypress) — Cy-Fair ISD, newer builds
- **77025** / **77030** (Medical Center) — high appreciation
- **77019** (Montrose/River Oaks) — gentrification premium
- **77005** (Rice Village) — land value play
- **77401** (Bellaire) — schools + teardown premium
- **77079** (Energy Corridor) — corporate relocation demand

---

## 🤖 AUTOMATION ROADMAP (To "Fully Automated")

### Phase 1 — Data In (Week 1)
1. PropStream → Export CSV daily (filtered: TX, ARV $300K-500K, motivated seller flags)
2. Run `python3 import_csv.py propstream_export.csv` → auto-imports to DB
3. Auto-calculate MAO, flag deals in $400K ARV range

### Phase 2 — Analysis (Week 1)  
1. Auto-run matcher when new property added
2. Flag "hot deals" (MAO > asking price by $15K+)
3. Daily digest email of new leads

### Phase 3 — Outreach (Week 2)
1. Buyer blast via SMTP when deal added to DB
2. SMS alerts via Twilio for top-matched buyers
3. Seller follow-up drip (Day 1, 3, 7, 14, 30)

### Phase 4 — Disposition (Week 3)
1. Auto-generate assignment contract when buyer selected
2. Send via email for review (PandaDoc integration)
3. Track EMD received, close date, assignment fee collected

### Phase 5 — Analytics (Week 4)
1. Source tracking (which channel → best ROI)
2. Conversion funnel by stage
3. Monthly revenue dashboard

---

## 📋 IMMEDIATE ACTION LIST

| Priority | Task | Time |
|---|---|---|
| P0 | Run `import_csv.py` with real PropStream data | 30 min |
| P0 | Add 20+ real buyers to DB via `buyer-intake.html` | 2 hrs |
| P0 | Configure SMTP in `automation/buyer_blast.py` | 30 min |
| P1 | Set up daily cron: `python3 automation/daily_runner.py` | 15 min |
| P1 | Build real buyer list (BiggerPockets, REI meetups, Connected Investors) | Ongoing |
| P1 | Get PropStream subscription ($99/mo) for daily exports | Today |
| P2 | Replace seed data with real Houston comps | 1 hr |
| P2 | Add TX disclosure language to contract generator | 1 hr |
| P3 | Connect Twilio for SMS buyer blasts | 1 hr |

---

*Files created: `import_csv.py`, `automation/daily_runner.py`, `automation/buyer_blast.py`, `buyer-intake.html`*
