# Norway Hotel Database - Design Document

## Objective

> "I want to populate data, currently in excel, where I need about 1000 data points from three sources, mostly Tripadvisor and/or google places, proff.no and the web."

## Scope

| Phase | Location | Hotels | Status |
|-------|----------|--------|--------|
| Pilot | Nord-Norge (North Norway) | ~450 | In Progress |
| Full | Hele Norge (All Norway) | ~10,000 | Planned |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                     (EXE with GUI - tkinter)                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      1. DISCOVERY MODULE                        │
│                   Find all hotels in region                     │
├─────────────────────────────────────────────────────────────────┤
│  Source: Brreg API (free, official Norwegian business registry) │
│  Method: Search by NACE codes (55.xxx = accommodation)          │
│  Output: org_number, legal_name, address, municipality          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      2. ENRICHMENT MODULE                       │
│                   Add details from multiple sources             │
├─────────────────────────────────────────────────────────────────┤
│  Source A: Google Places API                                    │
│  Source B: Proff.no (scraping or API)                          │
│  Source C: TripAdvisor (scraping - often blocked)              │
│  Source D: Auto-detection (brand from name)                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       3. EXPORT MODULE                          │
│                      Save to Excel file                         │
└─────────────────────────────────────────────────────────────────┘

```

## Data Sources

### 1. Brreg API (Discovery)
- **URL:** https://data.brreg.no/enhetsregisteret/api/enheter
- **Cost:** Free
- **Rate Limit:** None (reasonable use)
- **Status:** Planned

| Provides | Example |
|----------|---------|
| org_number | 912345678 |
| legal_name | THON HOTEL TROMSØ AS |
| address | Sjøgata 1, 9008 Tromsø |
| municipality | Tromsø |
| nace_code | 55.101 |

### 2. Google Places API (Enrichment)
- **URL:** https://maps.googleapis.com/maps/api/place/findplacefromtext/json
- **Cost:** Free 300 requests/day
- **Rate Limit:** 300/day (free tier)
- **Status:** Working

| Provides | Example |
|----------|---------|
| commercial_name | Thon Hotel Tromsø |
| address | Sjøgata 1, 9008 Tromsø, Norway |
| google_rating | 4.2 |
| phone | +47 77 60 00 00 |
| website | https://thonhotels.com/tromso |

### 3. Proff.no (Enrichment)
- **URL:** https://www.proff.no/selskap/-/-/{org_number}
- **Cost:** Free (scraping) or 25,000 NOK (API for 10k lookups)
- **Rate Limit:** Blocks after ~30 requests
- **Status:** Blocked (scraping), Too expensive (API)

| Provides | Example |
|----------|---------|
| owner | Olav Thon |
| board_members | ["Person A", "Person B"] |
| revenue | 45,000,000 NOK |

### 4. TripAdvisor (Enrichment)
- **URL:** https://www.tripadvisor.com/Search?q={hotel_name}
- **Cost:** Free (scraping) or $$$$$ (enterprise API)
- **Rate Limit:** Blocks after ~29 requests
- **Status:** Blocked

| Provides | Example |
|----------|---------|
| rooms | 125 |
| tripadvisor_rating | 4.5 |

### 5. Auto-Detection (Enrichment)
- **Method:** Pattern matching on hotel name
- **Cost:** Free
- **Status:** Working

| Provides | Example |
|----------|---------|
| brand | Thon, Scandic, Choice, Nordic Choice |
| property_type | Hotel, B&B, Hostel, Camping |

## Output Columns

| # | Column | Source | Status |
|---|--------|--------|--------|
| 1 | org_number | Brreg | Planned |
| 2 | legal_name | Brreg | Planned |
| 3 | commercial_name | Google Places | Working |
| 4 | address | Google Places | Working |
| 5 | municipality | Brreg | Planned |
| 6 | property_type | Auto-detect | Working |
| 7 | stars | Google (derived) | Working |
| 8 | rooms | TripAdvisor | Blocked |
| 9 | brand | Auto-detect | Working |
| 10 | operator | Proff.no | Blocked |
| 11 | owner | Proff.no | Blocked |
| 12 | board_members | Proff.no | Blocked |
| 13 | revenue | Proff.no | Blocked |
| 14 | google_rating | Google Places | Working |
| 15 | phone | Google Places | Working |
| 16 | website | Google Places | Working |

## Status Summary

```
WORKING (Free):              BLOCKED:                 TOO EXPENSIVE:
├─ commercial_name           ├─ rooms                 ├─ owner
├─ address                   │  (TripAdvisor)         ├─ board_members
├─ google_rating             │                        ├─ revenue
├─ stars                     │                        │  (Proff.no API 25k NOK)
├─ phone                     │                        │
├─ website                   │                        │
├─ brand                     │                        │
└─ property_type             │                        │
```

## Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13 |
| GUI | tkinter |
| HTTP | requests |
| Scraping | BeautifulSoup |
| Excel | pandas + openpyxl |
| Packaging | PyInstaller |

## Files

```
norway_hotel_db/
├── hotel_scraper_full.py    # Main application
├── config.env               # API keys (template)
├── .env                     # API keys (actual, gitignored)
├── DESIGN.md                # This file
├── dist/
│   └── Norway_Hotel_Scraper.exe
└── .beads/                  # Issue tracking
```

## Issues (Beads)

| ID | Priority | Task | Status |
|----|----------|------|--------|
| realestate1-8kp | P0 | Norway Hotel Database - Main Project | Open |
| realestate1-cnk | P0 | Rebuild EXE with latest fixes | Open |
| realestate1-e8t | P1 | Switch discovery from Proff.no to Brreg API | Open |
| realestate1-3vl | P1 | Move API key to config file | Open |

## Next Steps

1. [ ] Move API key to .env file
2. [ ] Switch discovery to Brreg API (free, no blocking)
3. [ ] Rebuild EXE
4. [ ] Test with Nord-Norge (~450 hotels)
5. [ ] Scale to all Norway (~10,000 hotels)
