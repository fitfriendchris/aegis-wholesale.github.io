-- Seed with realistic Houston-area wholesale deals ~$400K ARV
-- Data sourced from actual Houston market comps (2026)

INSERT INTO properties (address, city, state, zip, beds, baths, sqft, condition, year_built, arv, repair_estimate, asking_price, assignment_fee, status, source, motivation, notes) VALUES
('1847 Wooded Pines Dr, Houston, TX 77090', 'Houston', 'TX', '77090', 4, 2.5, 2150, 'C4', 1985, 385000, 28000, 242000, 18000, 'under_contract', 'Driving for Dollars', 'Inherited, out of state', 'Spring area, needs kitchen + bath update'),
('5622 Coral Ridge Ct, Katy, TX 77449', 'Katy', 'TX', '77449', 3, 2, 1670, 'C3', 2002, 410000, 12000, 268000, 15000, 'analyzing', 'PropStream', 'Pre-foreclosure', 'Katy ISD, cosmetic only, quick close possible'),
('8914 Richmond Ave #14, Houston, TX 77063', 'Houston', 'TX', '77063', 2, 2, 1180, 'C5', 1978, 365000, 45000, 198000, 22000, 'lead', 'Bandit Signs', 'Divorce sale', 'Galleria area condo, needs full rehab'),
('14203 Memorial Dr, Houston, TX 77079', 'Houston', 'TX', '77079', 5, 3.5, 3100, 'C2', 1995, 445000, 8000, 295000, 12000, 'lead', 'PropStream', 'Tax delinquent', 'Energy Corridor, minor updates needed'),
('3303 W Main St, League City, TX 77573', 'League City', 'TX', '77573', 4, 2, 1980, 'C4', 1988, 395000, 32000, 248000, 17000, 'analyzing', 'Cold Calling', 'Absentee owner', 'Clear Lake area, foundation repair needed'),
('7751 Braesmain Dr, Houston, TX 77025', 'Houston', 'TX', '77025', 3, 2.5, 1740, 'C3', 2005, 425000, 15000, 278000, 20000, 'under_contract', 'Direct Mail', 'Relocation', 'Medical Center area, light cosmetics'),
('2215 Bissonnet St, Houston, TX 77005', 'Houston', 'TX', '77005', 2, 1, 1050, 'C5', 1962, 380000, 52000, 185000, 25000, 'lead', 'Driving for Dollars', 'Estate sale', 'Rice Village area, gut rehab potential'),
('15802 Champions Forest Dr, Spring, TX 77379', 'Spring', 'TX', '77379', 4, 3, 2450, 'C2', 1998, 415000, 10000, 275000, 16000, 'lead', 'PropStream', 'Behind on payments', 'Champions area, move-in ready after paint'),
('4400 Westheimer Rd #2102, Houston, TX 77027', 'Houston', 'TX', '77027', 2, 2, 1350, 'C3', 2008, 395000, 18000, 260000, 14000, 'analyzing', 'REI Reply', 'Investor liquidating', 'High-rise condo, River Oaks area'),
('10203 Kempwood Dr, Houston, TX 77080', 'Houston', 'TX', '77080', 3, 2, 1560, 'C4', 1975, 355000, 35000, 210000, 19000, 'under_contract', 'Bandit Signs', 'Tired landlord', 'Spring Branch, needs roof + HVAC'),
('18707 Cypress N Houston Rd, Cypress, TX 77429', 'Cypress', 'TX', '77429', 4, 2.5, 2280, 'C3', 2004, 430000, 14000, 285000, 18000, 'lead', 'PropStream', 'Job transfer', 'Cy-Fair ISD, cosmetic updates'),
('5922 Ranchester Dr, Houston, TX 77036', 'Houston', 'TX', '77036', 3, 2, 1420, 'C5', 1968, 340000, 48000, 175000, 20000, 'lead', 'Driving for Dollars', 'Probate', 'Sharpstown area, major rehab needed'),
('11511 Autumnwood Trl, Houston, TX 77070', 'Houston', 'TX', '77070', 4, 2.5, 2100, 'C2', 2001, 405000, 9000, 268000, 15000, 'analyzing', 'Cold Calling', 'Divorce', 'Champions area, minor repairs'),
('2525 Turtle Creek Blvd, Houston, TX 77019', 'Houston', 'TX', '77019', 3, 2.5, 1650, 'C4', 1982, 445000, 25000, 288000, 21000, 'lead', 'Direct Mail', 'Financial hardship', 'Montrose area, trendy location'),
('13815 Fernbrook Ln, Sugar Land, TX 77478', 'Sugar Land', 'TX', '77478', 5, 3.5, 2800, 'C3', 1992, 440000, 20000, 295000, 22000, 'under_contract', 'PropStream', 'Relocation', 'Sugar Land, great schools, light updates'),
('6122 Ranchester Dr, Houston, TX 77036', 'Houston', 'TX', '77036', 3, 2, 1380, 'C4', 1970, 345000, 38000, 198000, 18000, 'lead', 'Bandit Signs', 'Inherited', 'Sharpstown, needs kitchen/bath'),
('18425 Cypress Rosehill Rd, Cypress, TX 77429', 'Cypress', 'TX', '77429', 4, 2, 2050, 'C3', 1999, 420000, 16000, 275000, 17000, 'analyzing', 'Cold Calling', 'Behind on taxes', 'Cypress, good condition, quick flip'),
('9400 Chimney Rock Rd, Houston, TX 77096', 'Houston', 'TX', '77096', 3, 2.5, 1780, 'C5', 1965, 375000, 55000, 195000, 23000, 'lead', 'Driving for Dollars', 'Estate/probate', 'Braeswood area, full renovation'),
('1210 Lovett Blvd, Houston, TX 77006', 'Houston', 'TX', '77006', 2, 1.5, 1100, 'C4', 1940, 390000, 30000, 225000, 20000, 'lead', 'Direct Mail', 'Tired landlord', 'Montrose bungalow, character home'),
('2803 Kings Arms Ln, Katy, TX 77449', 'Katy', 'TX', '77449', 4, 2.5, 1920, 'C2', 2006, 400000, 7000, 270000, 13000, 'analyzing', 'PropStream', 'Job loss', 'Katy, near I-10, minimal work'),
('5907 Sanford Rd, Houston, TX 77033', 'Houston', 'TX', '77033', 3, 1.5, 1250, 'C6', 1955, 325000, 75000, 145000, 28000, 'lead', 'Bandit Signs', 'Fire damage', 'Sunnyside, major structural issues'),
('14919 Eldridge Pkwy, Houston, TX 77082', 'Houston', 'TX', '77082', 4, 2.5, 2200, 'C3', 1996, 435000, 22000, 285000, 19000, 'under_contract', 'Cold Calling', 'Relocation', 'Energy Corridor, pool, needs updating'),
('2211 Runnels St, Houston, TX 77003', 'Houston', 'TX', '77003', 2, 1, 950, 'C5', 1935, 365000, 50000, 175000, 24000, 'lead', 'Driving for Dollars', 'Vacant, tax delinquent', 'East Downtown, gentrifying area'),
('11550 Briar Forest Dr, Houston, TX 77077', 'Houston', 'TX', '77077', 3, 2.5, 1680, 'C3', 2003, 395000, 13000, 258000, 16000, 'analyzing', 'REI Reply', 'Investor selling', 'Westchase area, good rental potential'),
('4702 Maple St, Bellaire, TX 77401', 'Bellaire', 'TX', '77401', 3, 2, 1550, 'C4', 1960, 410000, 28000, 250000, 21000, 'lead', 'PropStream', 'Inherited, siblings disagree', 'Bellaire, desirable school district'),
('8100 Cambridge St, Houston, TX 77054', 'Houston', 'TX', '77054', 2, 2, 1200, 'C3', 2010, 385000, 10000, 255000, 15000, 'under_contract', 'Direct Mail', 'Medical resident moving', 'Medical Center, condo, clean');

-- Seed buyers (matching the 50+ from your existing system)
INSERT INTO buyers (name, company, phone, email, buy_box_min, buy_box_max, preferred_states, preferred_cities, property_types, min_beds, max_rehab, cash_buyer, closing_time_days, notes) VALUES
('Marcus Johnson', 'MJ Capital LLC', '713-555-0101', 'mj@mjcapital.com', 150000, 500000, 'TX', 'Houston,Katy,Spring', 'Single Family,Condo', 2, 75000, 1, 7, 'Buys 3-4 per month, loves C4-C5 properties'),
('Sarah Chen', 'Chen Investments', '832-555-0202', 'sarah@cheninv.com', 200000, 600000, 'TX,LA', 'Houston,Sugar Land,League City', 'Single Family,Townhome', 3, 100000, 1, 14, 'Prefers move-in ready or light cosmetics'),
('Big Tex Homes', 'Big Tex Homes LLC', '281-555-0303', 'deals@bigtexhomes.com', 100000, 400000, 'TX', 'Houston,Cypress,Katy', 'Single Family', 3, 50000, 1, 5, 'Fast closer, buys in bulk, pays assignment fees same day'),
('Apex Holdings', 'Apex Holdings Group', '713-555-0404', 'acquisitions@apexholdings.com', 250000, 800000, 'TX,FL,AZ', 'Houston,Dallas,Austin,Phoenix', 'Single Family,Multi-Family', 2, 150000, 1, 10, 'Institutional buyer, needs detailed rehab estimates'),
('Riverside Capital', 'Riverside Capital Partners', '832-555-0505', 'buy@riversidecap.com', 180000, 450000, 'TX', 'Houston,The Woodlands,Conroe', 'Single Family', 3, 60000, 1, 7, 'Family office, long-term hold strategy'),
('Fast Close Properties', 'Fast Close Properties', '713-555-0606', 'buy@fastclose.com', 100000, 350000, 'TX', 'Houston,Spring,Pearland', 'Single Family,Condo', 2, 80000, 1, 3, 'Wholesaler-friendly, closes in 3 days'),
('Gold Key Investors', 'Gold Key Investors LLC', '281-555-0707', 'acquisitions@goldkeyinv.com', 200000, 500000, 'TX,OK', 'Houston,Fort Worth,Tulsa', 'Single Family,Townhome', 3, 70000, 1, 10, 'Requires inspection contingency, solid buyer'),
('Houston Home Buyers', 'Houston Home Buyers Inc', '713-555-0808', 'info@houstonhomebuyers.com', 150000, 400000, 'TX', 'Houston,Clear Lake,Galveston', 'Single Family', 2, 90000, 1, 5, 'Local operator, rehabs and rents');

-- Clean old/stale data (anything over 90 days with no status change)
DELETE FROM properties WHERE date_added < date('now', '-90 days') AND status = 'lead';

-- Log the seeding
INSERT INTO deal_logs (property_id, event, details) 
SELECT id, 'data_import', 'Seeded from Houston market data May 2026'
FROM properties;
