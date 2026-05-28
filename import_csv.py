#!/usr/bin/env python3
"""
Aegis Capital - PropStream CSV Importer
Imports PropStream / BatchLeads CSV exports into the Aegis SQLite database.

Usage:
    python3 import_csv.py propstream_export.csv
    python3 import_csv.py batchleads_export.csv --source batchleads
    python3 import_csv.py my_file.csv --dry-run  # preview without saving

PropStream export columns (auto-detected):
    Address, City, State, Zip, Beds, Baths, SqFt, YearBuilt,
    EstimatedValue, WholesaleValue, EquityPercent, ListingStatus,
    OwnerName, OwnerPhone, OwnerEmail, MortgageBalance, TaxDelinquent,
    PreForeclosure, Absentee, Vacant, LastSaleDate, LastSalePrice
"""

import csv
import sqlite3
import sys
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'aegis.db')

# PropStream column name → our DB column (flexible mapping)
PROPSTREAM_MAP = {
    # Address
    'property address': 'address', 'address': 'address',
    # City/State/Zip
    'city': 'city', 'state': 'state', 'zip': 'zip', 'zipcode': 'zip',
    # Property details
    'beds': 'beds', 'bedrooms': 'beds',
    'baths': 'baths', 'bathrooms': 'baths',
    'sqft': 'sqft', 'square feet': 'sqft', 'living area': 'sqft',
    'year built': 'year_built', 'yearbuilt': 'year_built',
    # Valuation
    'estimated value': 'arv', 'estimatedvalue': 'arv',
    'wholesale value': 'arv',  # PropStream's 70% AVM — use as MAO proxy
    'arv': 'arv',
    # Seller/Contact
    'owner name': 'seller_name', 'ownername': 'seller_name', 'owner 1 first name': 'seller_name',
    'owner phone': 'seller_phone', 'phone': 'seller_phone',
    'mailing address': 'notes',
    # Motivation signals
    'tax delinquent': '_tax_delinquent',
    'preforeclosure': '_preforeclosure', 'pre-foreclosure': '_preforeclosure',
    'absentee': '_absentee',
    'vacant': '_vacant',
    'equity percent': '_equity_pct',
    'listing status': '_listing_status',
}

def clean_money(val):
    if not val:
        return 0
    return int(re.sub(r'[^\d]', '', str(val)) or 0)

def clean_int(val):
    if not val:
        return None
    try:
        return int(float(str(val).replace(',', '')))
    except:
        return None

def derive_motivation(row):
    """Build motivation string from PropStream flags"""
    flags = []
    if row.get('_tax_delinquent', '').strip().lower() in ('yes', 'true', '1', 'y'):
        flags.append('Tax delinquent')
    if row.get('_preforeclosure', '').strip().lower() in ('yes', 'true', '1', 'y'):
        flags.append('Pre-foreclosure')
    if row.get('_absentee', '').strip().lower() in ('yes', 'true', '1', 'y'):
        flags.append('Absentee owner')
    if row.get('_vacant', '').strip().lower() in ('yes', 'true', '1', 'y'):
        flags.append('Vacant')
    equity = clean_int(row.get('_equity_pct', ''))
    if equity and equity >= 40:
        flags.append(f'High equity ({equity}%)')
    return ', '.join(flags) if flags else 'Unknown'

def import_csv(filepath, source='PropStream', dry_run=False):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    imported = 0
    skipped = 0
    errors = 0

    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        # Normalize header names
        headers = {k.lower().strip(): k for k in reader.fieldnames or []}
        print(f"\n📂 File: {filepath}")
        print(f"   Columns detected: {len(headers)}")
        print(f"   Source: {source}")
        print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE IMPORT'}\n")

        for i, raw_row in enumerate(reader, 1):
            # Map columns
            row = {}
            for col_lower, original in headers.items():
                mapped = PROPSTREAM_MAP.get(col_lower)
                if mapped:
                    row[mapped] = raw_row.get(original, '').strip()

            # Skip if no address
            address = row.get('address', '').strip()
            if not address:
                skipped += 1
                continue

            # Skip duplicates
            cursor.execute("SELECT id FROM properties WHERE address = ?", (address,))
            if cursor.fetchone():
                skipped += 1
                continue

            # Determine ARV
            arv_raw = row.get('arv', '')
            arv = clean_money(arv_raw)
            
            # Filter: only import ~$400K ARV range (300K-500K)
            if arv and (arv < 250000 or arv > 600000):
                skipped += 1
                continue

            # MAO calculation (70% rule)
            mao = int(arv * 0.70) if arv else 0

            # Assign condition based on listing status
            listing = row.get('_listing_status', '').lower()
            condition = 'C3'  # default
            if 'vacant' in row.get('_vacant', '').lower() or 'vacant' in listing:
                condition = 'C4'

            motivation = derive_motivation(row)

            if dry_run:
                print(f"  [{i}] WOULD IMPORT: {address} | ARV: ${arv:,} | MAO: ${mao:,} | {motivation}")
                imported += 1
                continue

            try:
                cursor.execute("""
                    INSERT INTO properties 
                    (address, city, state, zip, beds, baths, sqft, condition, year_built,
                     arv, mao, status, source, seller_name, seller_phone, motivation, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    address,
                    row.get('city', 'Houston'),
                    row.get('state', 'TX'),
                    row.get('zip', ''),
                    clean_int(row.get('beds')),
                    clean_int(row.get('baths')),
                    clean_int(row.get('sqft')),
                    condition,
                    clean_int(row.get('year_built')),
                    arv, mao,
                    'lead',
                    source,
                    row.get('seller_name', ''),
                    row.get('seller_phone', ''),
                    motivation,
                    row.get('notes', '')
                ))
                imported += 1
                
                if imported % 10 == 0:
                    print(f"  ✓ {imported} records imported...")

            except Exception as e:
                print(f"  ⚠️  Row {i} error: {e}")
                errors += 1

    if not dry_run:
        conn.commit()
    conn.close()

    print(f"\n{'─'*40}")
    print(f"✅ Imported:  {imported}")
    print(f"⏭️  Skipped:   {skipped} (duplicates or out of ARV range)")
    print(f"❌ Errors:    {errors}")
    print(f"{'─'*40}")
    if not dry_run:
        print(f"\nAll data saved to: {DB_PATH}")
        print(f"View in dashboard: open ~/aegis-wholesale/dashboard.html")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 import_csv.py <file.csv> [--source sourcename] [--dry-run]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    source = 'PropStream'
    dry_run = False
    
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == '--source' and i < len(sys.argv):
            source = sys.argv[i]
        elif arg == '--dry-run':
            dry_run = True
    
    import_csv(filepath, source, dry_run)
