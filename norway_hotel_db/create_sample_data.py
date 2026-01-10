"""
Create sample input data for Norway Hotel Database
"""
import pandas as pd

# Sample data - North Norway hotels (legal names from Brønnøysund register style)
sample_hotels = [
    {"org_number": "912345678", "legal_name": "THON HOTEL TROMSØ AS", "address": "Sjøgata 19-21, 9008 Tromsø", "municipality": "Tromsø", "property_type": "Hotel"},
    {"org_number": "923456789", "legal_name": "SCANDIC ISHAVSHOTEL AS", "address": "Fredrik Langes gate 2, 9008 Tromsø", "municipality": "Tromsø", "property_type": "Hotel"},
    {"org_number": "934567890", "legal_name": "CLARION HOTEL THE EDGE AS", "address": "Kaigata 6, 9008 Tromsø", "municipality": "Tromsø", "property_type": "Hotel"},
    {"org_number": "945678901", "legal_name": "SMARTHOTEL TROMSØ AS", "address": "Vestregata 34, 9008 Tromsø", "municipality": "Tromsø", "property_type": "Hotel"},
    {"org_number": "956789012", "legal_name": "VIKING HOTELL TROMSØ AS", "address": "Grønnegata 18, 9008 Tromsø", "municipality": "Tromsø", "property_type": "Hotel"},
    {"org_number": "967890123", "legal_name": "QUALITY HOTEL SAGA AS", "address": "Richard Withs plass 2, 9008 Tromsø", "municipality": "Tromsø", "property_type": "Hotel"},
    {"org_number": "978901234", "legal_name": "SYDSPISSEN HOTELL AS", "address": "Strandvegen 166, 9006 Tromsø", "municipality": "Tromsø", "property_type": "Hotel"},
    {"org_number": "989012345", "legal_name": "SOMMARØY ARCTIC HOTEL AS", "address": "Sommarøy, 9110 Sommarøy", "municipality": "Tromsø", "property_type": "Hotel"},
    {"org_number": "990123456", "legal_name": "MALANGEN RESORT AS", "address": "Malangen, 9055 Meistervik", "municipality": "Balsfjord", "property_type": "Resort"},
    {"org_number": "901234567", "legal_name": "SCANDIC GRAND TROMSØ AS", "address": "Storgata 44, 9008 Tromsø", "municipality": "Tromsø", "property_type": "Hotel"},
]

df = pd.DataFrame(sample_hotels)
df.to_excel("sample_input.xlsx", index=False, sheet_name="Hotels")
print(f"Created sample_input.xlsx with {len(df)} hotels")
print("\nColumns:")
for col in df.columns:
    print(f"  - {col}")
