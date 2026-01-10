"""
Norway Hotel Database - Full Scraper
Discovers AND enriches all hotels/B&Bs in Norway from scratch.

Sources:
1. Brønnøysund Register (via Proff.no) - Find all hotel companies
2. Google Places API - Commercial names, ratings
3. Proff.no - Ownership, financials
4. TripAdvisor - Room count
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import pandas as pd
from datetime import datetime
import os
import sys
import time
import re
import random
from bs4 import BeautifulSoup

# ============================================================
# CONFIGURATION
# ============================================================
GOOGLE_PLACES_API_KEY = ""  # Optional: Add your Google Places API key
PROFF_API_KEY = ""          # Optional: Add your Proff.no API key

# Regions in Norway (for filtering)
REGIONS = {
    "Nord-Norge": ["Nordland", "Troms", "Finnmark", "Troms og Finnmark"],
    "Trøndelag": ["Trøndelag", "Sør-Trøndelag", "Nord-Trøndelag"],
    "Vestlandet": ["Rogaland", "Vestland", "Hordaland", "Sogn og Fjordane", "Møre og Romsdal"],
    "Østlandet": ["Oslo", "Viken", "Akershus", "Østfold", "Buskerud", "Innlandet", "Hedmark", "Oppland", "Vestfold og Telemark", "Vestfold", "Telemark"],
    "Sørlandet": ["Agder", "Aust-Agder", "Vest-Agder"],
    "Hele Norge": []  # Empty = all
}

# Search terms to find hotels
HOTEL_SEARCH_TERMS = [
    "hotell",
    "hotel",
    "overnatting",
    "gjestehus",
    "pensjonat",
    "motell",
    "camping",
    "hytteutleie",
    "bed and breakfast",
    "b&b",
    "vandrerhjem",
    "hostel",
    "resort",
    "lodge",
]

# NACE codes for accommodation
NACE_CODES = [
    "55.101",  # Drift av hoteller, pensjonater og moteller med restaurant
    "55.102",  # Drift av hoteller, pensjonater og moteller uten restaurant
    "55.201",  # Drift av vandrerhjem og turisthytter
    "55.202",  # Drift av campingplasser og turisthytter
    "55.203",  # Utleie av hytter, ferieleiligheter
    "55.204",  # Drift av feriesentre
    "55.300",  # Drift av campingplasser
    "55.900",  # Annen overnatting
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]


class HotelScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Norway Hotel Database - Full Scraper")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)

        self.hotels = []
        self.is_running = False
        self.discovered_count = 0

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Norway Hotel Database - Full Scraper",
            font=('Helvetica', 16, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 5))

        subtitle_label = ttk.Label(
            main_frame,
            text="Automatically discovers and enriches all hotels in Norway",
            font=('Helvetica', 10)
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 15))

        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Region selection
        ttk.Label(settings_frame, text="Region:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.region_var = tk.StringVar(value="Nord-Norge")
        region_combo = ttk.Combobox(settings_frame, textvariable=self.region_var, values=list(REGIONS.keys()), width=20)
        region_combo.grid(row=0, column=1, sticky="w")

        # Property types
        ttk.Label(settings_frame, text="Include:").grid(row=0, column=2, sticky="w", padx=(20, 10))

        self.include_hotels = tk.BooleanVar(value=True)
        self.include_bb = tk.BooleanVar(value=True)
        self.include_camping = tk.BooleanVar(value=False)

        ttk.Checkbutton(settings_frame, text="Hotels", variable=self.include_hotels).grid(row=0, column=3)
        ttk.Checkbutton(settings_frame, text="B&B/Pensjonat", variable=self.include_bb).grid(row=0, column=4)
        ttk.Checkbutton(settings_frame, text="Camping", variable=self.include_camping).grid(row=0, column=5)

        # Limit
        ttk.Label(settings_frame, text="Max results:").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.limit_var = tk.StringVar(value="100")
        limit_entry = ttk.Entry(settings_frame, textvariable=self.limit_var, width=10)
        limit_entry.grid(row=1, column=1, sticky="w", pady=(10, 0))
        ttk.Label(settings_frame, text="(0 = unlimited)", font=('Helvetica', 8)).grid(row=1, column=2, sticky="w", pady=(10, 0))

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        self.discover_btn = ttk.Button(
            action_frame,
            text="🔍 Discover Hotels",
            command=self.start_discovery,
            width=20
        )
        self.discover_btn.pack(side="left", padx=(0, 10))

        self.enrich_btn = ttk.Button(
            action_frame,
            text="📊 Enrich Data",
            command=self.start_enrichment,
            width=20,
            state="disabled"
        )
        self.enrich_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ttk.Button(
            action_frame,
            text="⏹ Stop",
            command=self.stop_process,
            width=10,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(0, 10))

        self.export_btn = ttk.Button(
            action_frame,
            text="💾 Export to Excel",
            command=self.export_to_excel,
            width=20,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=(0, 10))

        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Discovered Hotels", padding="5")
        results_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Treeview
        columns = ('org_number', 'legal_name', 'commercial_name', 'address', 'municipality',
                   'property_type', 'stars', 'rooms', 'brand', 'owner', 'status')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

        column_config = {
            'org_number': ('Org Nr', 90),
            'legal_name': ('Legal Name', 180),
            'commercial_name': ('Commercial Name', 150),
            'address': ('Address', 200),
            'municipality': ('Municipality', 100),
            'property_type': ('Type', 80),
            'stars': ('Stars', 50),
            'rooms': ('Rooms', 50),
            'brand': ('Brand', 100),
            'owner': ('Owner', 120),
            'status': ('Status', 80),
        }

        for col, (heading, width) in column_config.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=40)

        scrollbar_y = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, sticky="ew", pady=(0, 5))
        progress_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready. Select a region and click 'Discover Hotels'")
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        # Stats
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=6, column=0, sticky="w")

        self.stats_var = tk.StringVar(value="Hotels: 0 | Enriched: 0")
        ttk.Label(stats_frame, textvariable=self.stats_var, font=('Helvetica', 9)).pack(side="left")

        # API status
        google_status = "✅" if GOOGLE_PLACES_API_KEY else "❌"
        proff_status = "✅" if PROFF_API_KEY else "❌"
        ttk.Label(
            stats_frame,
            text=f"   |   Google: {google_status}  Proff API: {proff_status}",
            font=('Helvetica', 8),
            foreground='gray'
        ).pack(side="left")

    def stop_process(self):
        """Stop current process"""
        self.is_running = False
        self.status_var.set("Stopping...")

    def start_discovery(self):
        """Start hotel discovery"""
        if self.is_running:
            return

        self.is_running = True
        self.hotels = []
        self.discovered_count = 0
        self.clear_tree()

        self.discover_btn.config(state="disabled")
        self.enrich_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start()

        thread = threading.Thread(target=self.discover_hotels)
        thread.daemon = True
        thread.start()

    def discover_hotels(self):
        """Discover hotels from Proff.no by searching NACE codes and keywords"""
        region = self.region_var.get()
        counties = REGIONS.get(region, [])

        try:
            limit = int(self.limit_var.get())
        except:
            limit = 100

        self.update_status(f"Discovering hotels in {region}...")

        # Build search terms based on checkboxes
        search_terms = []
        if self.include_hotels.get():
            search_terms.extend(["hotell", "hotel", "resort", "lodge"])
        if self.include_bb.get():
            search_terms.extend(["pensjonat", "gjestehus", "bed and breakfast", "b&b", "vandrerhjem"])
        if self.include_camping.get():
            search_terms.extend(["camping", "hytteutleie"])

        if not search_terms:
            search_terms = ["hotell"]

        seen_orgs = set()

        for term in search_terms:
            if not self.is_running:
                break

            if limit > 0 and len(self.hotels) >= limit:
                break

            self.update_status(f"Searching for '{term}' in {region}...")

            # Search Proff.no
            hotels_found = self.search_proff(term, counties)

            for hotel in hotels_found:
                if not self.is_running:
                    break
                if limit > 0 and len(self.hotels) >= limit:
                    break

                org = hotel.get('org_number', '')
                if org and org not in seen_orgs:
                    seen_orgs.add(org)
                    hotel['status'] = 'Discovered'
                    hotel['property_type'] = self.classify_property_type(hotel.get('legal_name', ''))
                    self.hotels.append(hotel)
                    self.root.after(0, lambda h=hotel: self.add_tree_row(h))
                    self.update_stats()

            # Be nice to the server
            time.sleep(random.uniform(2, 4))

        self.is_running = False
        self.root.after(0, self.discovery_complete)

    def search_proff(self, term, counties):
        """Search Proff.no for companies matching term"""
        hotels = []

        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}

            # Search URL
            search_url = f"https://www.proff.no/bransjesøk?q={term}"

            # Add county filter if specified
            for county in (counties if counties else [""]):
                if not self.is_running:
                    break

                url = search_url
                if county:
                    url += f"&county={county}"

                self.update_status(f"Searching: {term} in {county if county else 'all counties'}...")

                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')

                # Find company listings
                company_links = soup.find_all('a', href=re.compile(r'/selskap/'))

                for link in company_links:
                    try:
                        href = link.get('href', '')

                        # Extract org number from URL
                        org_match = re.search(r'/(\d{9})/?$', href)
                        if not org_match:
                            continue

                        org_number = org_match.group(1)

                        # Get company name
                        name = link.get_text(strip=True)
                        if not name or len(name) < 3:
                            continue

                        # Skip if not accommodation related
                        name_lower = name.lower()
                        if not any(kw in name_lower for kw in ['hotell', 'hotel', 'pensjonat', 'gjestehus',
                                                                'overnatting', 'camping', 'resort', 'lodge',
                                                                'vandrerhjem', 'hostel', 'inn']):
                            # Check if parent has accommodation context
                            parent_text = link.find_parent('div')
                            if parent_text:
                                parent_text = parent_text.get_text().lower()
                                if not any(kw in parent_text for kw in ['overnatting', 'hotell', 'accommodation']):
                                    continue

                        # Try to find address
                        address = ""
                        parent = link.find_parent(['div', 'li', 'tr'])
                        if parent:
                            addr_elem = parent.find(['span', 'div'], class_=re.compile(r'address|location', re.I))
                            if addr_elem:
                                address = addr_elem.get_text(strip=True)
                            else:
                                # Look for postal code pattern
                                text = parent.get_text()
                                addr_match = re.search(r'(\d{4}\s+\w+)', text)
                                if addr_match:
                                    address = addr_match.group(1)

                        hotels.append({
                            'org_number': org_number,
                            'legal_name': name,
                            'address': address,
                            'municipality': county if county else '',
                            'commercial_name': '',
                            'stars': '',
                            'rooms': '',
                            'brand': '',
                            'owner': '',
                        })

                    except Exception as e:
                        continue

                # Random delay between pages
                time.sleep(random.uniform(1, 3))

                # Only search first county if no specific counties
                if not counties:
                    break

        except Exception as e:
            print(f"Search error: {e}")

        return hotels

    def classify_property_type(self, name):
        """Classify property type from name"""
        name_lower = name.lower()

        if 'camping' in name_lower:
            return 'Camping'
        elif any(x in name_lower for x in ['pensjonat', 'gjestehus', 'b&b', 'bed and breakfast']):
            return 'B&B'
        elif 'vandrerhjem' in name_lower or 'hostel' in name_lower:
            return 'Hostel'
        elif 'resort' in name_lower:
            return 'Resort'
        elif 'lodge' in name_lower:
            return 'Lodge'
        else:
            return 'Hotel'

    def discovery_complete(self):
        """Called when discovery is done"""
        self.progress.stop()
        self.discover_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        if self.hotels:
            self.enrich_btn.config(state="normal")
            self.export_btn.config(state="normal")

        self.status_var.set(f"Discovery complete! Found {len(self.hotels)} hotels. Click 'Enrich Data' to add details.")
        self.update_stats()

    def start_enrichment(self):
        """Start enriching discovered hotels"""
        if self.is_running or not self.hotels:
            return

        self.is_running = True
        self.discover_btn.config(state="disabled")
        self.enrich_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start()

        thread = threading.Thread(target=self.enrich_hotels)
        thread.daemon = True
        thread.start()

    def enrich_hotels(self):
        """Enrich hotel data from multiple sources"""
        total = len(self.hotels)
        enriched = 0

        for idx, hotel in enumerate(self.hotels):
            if not self.is_running:
                break

            org_number = hotel.get('org_number', '')
            legal_name = hotel.get('legal_name', '')
            address = hotel.get('address', '')

            self.update_status(f"Enriching {idx + 1}/{total}: {legal_name[:30]}...")

            sources = []

            # Google Places
            if GOOGLE_PLACES_API_KEY:
                google_data = self.lookup_google_places(legal_name, address)
                if google_data:
                    hotel['commercial_name'] = google_data.get('name', '')
                    hotel['google_rating'] = google_data.get('rating', '')
                    hotel['stars'] = self.rating_to_stars(google_data.get('rating', 0))
                    sources.append('Google')

            # Proff.no for ownership
            if org_number:
                proff_data = self.lookup_proff_details(org_number)
                if proff_data:
                    hotel['owner'] = proff_data.get('owner', '')
                    hotel['revenue'] = proff_data.get('revenue', '')
                    sources.append('Proff')

            # Detect brand
            hotel['brand'] = self.detect_brand(hotel.get('commercial_name', '') or legal_name)

            # Update status
            if sources:
                hotel['status'] = 'Enriched ✓'
                enriched += 1
            else:
                hotel['status'] = 'Basic'

            # Update tree row
            self.root.after(0, lambda h=hotel, i=idx: self.update_tree_row(i, h))
            self.root.after(0, lambda e=enriched: self.stats_var.set(f"Hotels: {len(self.hotels)} | Enriched: {e}"))

            # Human-like delay
            time.sleep(random.uniform(2, 5))

            # Break every 15-25 hotels
            if idx > 0 and idx % random.randint(15, 25) == 0:
                self.update_status(f"Taking a break to avoid blocking...")
                time.sleep(random.uniform(20, 40))

        self.is_running = False
        self.root.after(0, self.enrichment_complete)

    def lookup_google_places(self, name, address):
        """Lookup in Google Places API"""
        if not GOOGLE_PLACES_API_KEY:
            return None

        try:
            search_name = re.sub(r'\b(AS|ANS|DA|ENK|DRIFT)\b', '', name, flags=re.IGNORECASE).strip()
            query = f"{search_name} {address} Norway"

            url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            params = {
                'input': query,
                'inputtype': 'textquery',
                'fields': 'name,rating,formatted_address',
                'key': GOOGLE_PLACES_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('candidates'):
                return data['candidates'][0]

        except Exception as e:
            print(f"Google error: {e}")

        return None

    def lookup_proff_details(self, org_number):
        """Get details from Proff.no"""
        try:
            org_number = re.sub(r'\D', '', str(org_number))
            if len(org_number) != 9:
                return None

            url = f"https://www.proff.no/selskap/-/-/{org_number}"
            headers = {'User-Agent': random.choice(USER_AGENTS)}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            result = {}

            # Find owner
            text = soup.get_text()
            owner_match = re.search(r'Daglig leder[:\s]+([A-ZÆØÅ][a-zæøå]+\s+[A-ZÆØÅ][a-zæøå]+)', text)
            if owner_match:
                result['owner'] = owner_match.group(1)

            # Find revenue
            revenue_match = re.search(r'Driftsinntekter[:\s]+([\d\s,\.]+)', text)
            if revenue_match:
                result['revenue'] = revenue_match.group(1).strip()

            return result if result else None

        except Exception as e:
            print(f"Proff error: {e}")
            return None

    def rating_to_stars(self, rating):
        """Convert rating to stars"""
        try:
            r = float(rating)
            if r >= 4.5: return '5'
            elif r >= 4.0: return '4'
            elif r >= 3.5: return '3'
            elif r >= 3.0: return '2'
            else: return '1'
        except:
            return ''

    def detect_brand(self, name):
        """Detect hotel brand"""
        brands = {
            'Thon': 'Thon Hotels', 'Scandic': 'Scandic', 'Clarion': 'Nordic Choice',
            'Comfort': 'Nordic Choice', 'Quality': 'Nordic Choice', 'Radisson': 'Radisson',
            'Hilton': 'Hilton', 'Best Western': 'Best Western', 'Smarthotel': 'Smarthotel',
            'Citybox': 'Citybox', 'First': 'First Hotels', 'Rica': 'Scandic',
        }
        name_upper = name.upper()
        for key, brand in brands.items():
            if key.upper() in name_upper:
                return brand
        return ''

    def enrichment_complete(self):
        """Called when enrichment is done"""
        self.progress.stop()
        self.discover_btn.config(state="normal")
        self.enrich_btn.config(state="normal")
        self.export_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set(f"Enrichment complete! Ready to export.")

    def clear_tree(self):
        """Clear treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def add_tree_row(self, hotel):
        """Add row to treeview"""
        self.tree.insert('', 'end', values=(
            hotel.get('org_number', ''),
            str(hotel.get('legal_name', ''))[:30],
            str(hotel.get('commercial_name', ''))[:25],
            str(hotel.get('address', ''))[:35],
            hotel.get('municipality', ''),
            hotel.get('property_type', ''),
            hotel.get('stars', ''),
            hotel.get('rooms', ''),
            hotel.get('brand', ''),
            str(hotel.get('owner', ''))[:20],
            hotel.get('status', '')
        ))

    def update_tree_row(self, idx, hotel):
        """Update existing tree row"""
        items = self.tree.get_children()
        if idx < len(items):
            self.tree.item(items[idx], values=(
                hotel.get('org_number', ''),
                str(hotel.get('legal_name', ''))[:30],
                str(hotel.get('commercial_name', ''))[:25],
                str(hotel.get('address', ''))[:35],
                hotel.get('municipality', ''),
                hotel.get('property_type', ''),
                hotel.get('stars', ''),
                hotel.get('rooms', ''),
                hotel.get('brand', ''),
                str(hotel.get('owner', ''))[:20],
                hotel.get('status', '')
            ))

    def update_status(self, message):
        """Update status"""
        self.root.after(0, lambda: self.status_var.set(message))

    def update_stats(self):
        """Update stats display"""
        enriched = sum(1 for h in self.hotels if h.get('status') == 'Enriched ✓')
        self.root.after(0, lambda: self.stats_var.set(f"Hotels: {len(self.hotels)} | Enriched: {enriched}"))

    def export_to_excel(self):
        """Export to Excel"""
        if not self.hotels:
            messagebox.showwarning("No Data", "No hotels to export.")
            return

        region = self.region_var.get().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"Norway_Hotels_{region}_{timestamp}.xlsx"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=default_filename
        )

        if not filepath:
            return

        try:
            df = pd.DataFrame(self.hotels)

            # Add metadata columns
            df['data_source'] = 'Proff.no + Google'
            df['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Hotels', index=False)

                worksheet = writer.sheets['Hotels']

                # Style headers
                from openpyxl.styles import Font, PatternFill, Alignment

                header_font = Font(bold=True, color='FFFFFF')
                header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')

                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center')

                worksheet.freeze_panes = 'A2'

            messagebox.showinfo("Success", f"Exported {len(self.hotels)} hotels to:\n{filepath}")
            os.startfile(os.path.dirname(filepath))

        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")


def main():
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = HotelScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
