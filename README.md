# Aegis Capital RE Wholesale

## 🚀 Quick Start

### 1. Start the API server
```bash
cd ~/aegis-wholesale/backend
python3 api_server.py
```

Server runs on `http://localhost:5000`

### 2. Open the dashboard
```bash
open ~/aegis-wholesale/dashboard.html
```

Or visit `file:///Users/yuhfriendchris/aegis-wholesale/dashboard.html` in your browser.

## 📁 Structure

```
aegis-wholesale/
├── dashboard.html          # Live dashboard (replaces old localStorage version)
├── backend/
│   ├── api_server.py       # Python Flask API for SQLite
│   ├── aegis.db            # SQLite database (real persistence)
│   ├── schema.sql          # Database schema
│   └── seed_data.sql       # Initial Houston market data
├── buyers.html             # Existing buyer database
├── deal-analyzer.html      # Existing deal analyzer
├── matcher.html            # Existing auto-matcher
└── ... (other tools)
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/properties` | GET | List all properties (with `?arv_min=350000&arv_max=450000&status=active` filters) |
| `/api/properties/<id>` | GET | Single property detail |
| `/api/properties` | POST | Add new property |
| `/api/properties/<id>` | PUT | Update property |
| `/api/properties/<id>` | DELETE | Delete property |
| `/api/buyers` | GET | List all buyers |
| `/api/pipeline/summary` | GET | Dashboard stats cards |
| `/api/pipeline/filter` | GET | Filtered deals (e.g. ~$400K ARV) |
| `/api/match/<property_id>` | GET | Find matching buyers for a deal |

## 🧮 Dashboard Metrics

- **Active Deals**: 26 (6 under contract, 7 analyzing, 13 leads)
- **Pipeline Value**: $488K in assignment fees
- **Avg ARV**: ~$395K
- **~$400K ARV Filter**: 23 properties in range

## 📝 Adding Real Data

Replace the seed data with your actual leads:

1. Export from PropStream, BatchLeads, or REI Reply to CSV
2. Run: `python3 import_csv.py your_data.csv`
3. Or POST to `/api/properties` from the deal analyzer

## ⚠️ Data Accuracy

ARV values in seed data are based on 2026 Houston market comps:
- Houston proper: $350K-$450K for 3-4BR homes
- Katy/Spring/Cypress: Slightly higher ($400K-$440K)
- Sharpstown/Sunnyside: Lower ($325K-$375K)

Always verify ARV with fresh comps before making offers.
