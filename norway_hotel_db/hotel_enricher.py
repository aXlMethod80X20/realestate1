"""
Norway Hotel Database Enricher - POC
Enriches hotel data from multiple sources:
1. Google Places API - commercial name, ratings, stars
2. Proff.no - ownership, financials (API or scraping)
3. TripAdvisor - room count (human-like scraping)
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
# CONFIGURATION - Add your API keys here
# ============================================================
GOOGLE_PLACES_API_KEY = ""  # Add your Google Places API key
PROFF_API_KEY = ""          # Add your Proff.no API key (if you have trial)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'no,en;q=0.9',
}

# List of user agents to rotate (human-like behavior)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]


class HotelEnricherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Norway Hotel Database Enricher")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        self.input_df = None
        self.output_df = None
        self.is_running = False

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Norway Hotel Database Enricher",
            font=('Helvetica', 16, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 5))

        subtitle_label = ttk.Label(
            main_frame,
            text="Enrich hotel data from Google Places, Proff.no & TripAdvisor",
            font=('Helvetica', 10)
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 15))

        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Step 1: Load Input Data", padding="10")
        input_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Excel file:").grid(row=0, column=0, sticky="w")
        self.file_path_var = tk.StringVar(value="No file selected")
        ttk.Label(input_frame, textvariable=self.file_path_var).grid(row=0, column=1, sticky="w", padx=(10, 10))
        ttk.Button(input_frame, text="Browse...", command=self.load_file).grid(row=0, column=2)

        self.record_count_var = tk.StringVar(value="")
        ttk.Label(input_frame, textvariable=self.record_count_var, foreground="green").grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))

        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Step 2: Enriched Data Preview", padding="5")
        results_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Treeview with all columns
        columns = ('org_number', 'legal_name', 'commercial_name', 'address', 'municipality',
                   'property_type', 'stars', 'rooms', 'brand', 'operator', 'owner',
                   'revenue', 'google_rating', 'status')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=12)

        # Configure column headings and widths
        column_config = {
            'org_number': ('Org Nr', 80),
            'legal_name': ('Legal Name', 150),
            'commercial_name': ('Commercial Name', 150),
            'address': ('Address', 180),
            'municipality': ('Municipality', 100),
            'property_type': ('Type', 80),
            'stars': ('Stars', 50),
            'rooms': ('Rooms', 50),
            'brand': ('Brand', 100),
            'operator': ('Operator', 100),
            'owner': ('Owner', 120),
            'revenue': ('Revenue', 80),
            'google_rating': ('Rating', 50),
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
        progress_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Load an Excel file to start")
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, sticky="ew")

        self.enrich_btn = ttk.Button(
            buttons_frame,
            text="🔍 Enrich Data",
            command=self.start_enrichment,
            width=20,
            state="disabled"
        )
        self.enrich_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ttk.Button(
            buttons_frame,
            text="⏹ Stop",
            command=self.stop_enrichment,
            width=10,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(0, 10))

        self.export_btn = ttk.Button(
            buttons_frame,
            text="📊 Export to Excel",
            command=self.export_to_excel,
            width=20,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=(0, 10))

        # API key status
        api_frame = ttk.Frame(main_frame)
        api_frame.grid(row=6, column=0, sticky="w", pady=(10, 0))

        google_status = "✅" if GOOGLE_PLACES_API_KEY else "❌"
        proff_status = "✅" if PROFF_API_KEY else "❌"

        ttk.Label(
            api_frame,
            text=f"Google Places: {google_status}  |  Proff.no API: {proff_status}  |  TripAdvisor: 🔄 Human-like scraping",
            font=('Helvetica', 8),
            foreground='gray'
        ).pack(side="left")

    def load_file(self):
        """Load Excel file with hotel data"""
        filepath = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")],
            title="Select Hotel Data File"
        )

        if not filepath:
            return

        try:
            if filepath.endswith('.csv'):
                self.input_df = pd.read_csv(filepath)
            else:
                self.input_df = pd.read_excel(filepath)

            self.file_path_var.set(os.path.basename(filepath))
            self.record_count_var.set(f"Loaded {len(self.input_df)} records")
            self.enrich_btn.config(state="normal")
            self.status_var.set("Ready to enrich data. Click 'Enrich Data' to start.")

            # Show preview
            self.clear_tree()
            for idx, row in self.input_df.head(10).iterrows():
                self.tree.insert('', 'end', values=(
                    row.get('org_number', ''),
                    str(row.get('legal_name', ''))[:25],
                    '',  # commercial_name
                    str(row.get('address', ''))[:30],
                    row.get('municipality', ''),
                    row.get('property_type', ''),
                    '',  # stars
                    '',  # rooms
                    '',  # brand
                    '',  # operator
                    '',  # owner
                    '',  # revenue
                    '',  # google_rating
                    'Pending'
                ))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def clear_tree(self):
        """Clear treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def stop_enrichment(self):
        """Stop the enrichment process"""
        self.is_running = False
        self.status_var.set("Stopping... (will stop after current hotel)")

    def start_enrichment(self):
        """Start the enrichment process"""
        if self.is_running or self.input_df is None:
            return

        self.is_running = True
        self.enrich_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.export_btn.config(state="disabled")
        self.clear_tree()

        thread = threading.Thread(target=self.enrich_data)
        thread.daemon = True
        thread.start()

    def enrich_data(self):
        """Main enrichment logic"""
        total = len(self.input_df)
        results = []

        for idx, row in self.input_df.iterrows():
            if not self.is_running:
                self.update_status(f"Stopped at {idx}/{total}")
                break

            legal_name = str(row.get('legal_name', ''))
            address = str(row.get('address', ''))
            org_number = str(row.get('org_number', ''))
            municipality = str(row.get('municipality', ''))
            property_type = str(row.get('property_type', ''))

            self.update_status(f"Processing {idx + 1}/{total}: {legal_name[:30]}...")
            self.update_progress((idx + 1) / total * 100)

            # Initialize result with all columns
            result = {
                'org_number': org_number,
                'legal_name': legal_name,
                'commercial_name': '',
                'address': address,
                'municipality': municipality,
                'property_type': property_type,
                'stars': '',
                'rooms': '',
                'brand': '',
                'operator': '',
                'owner': '',
                'board_members': '',
                'revenue': '',
                'google_rating': '',
                'tripadvisor_url': '',
                'website': '',
                'phone': '',
                'email': '',
                'data_source': '',
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'status': 'Pending'
            }

            sources_found = []

            # ============================================================
            # PHASE 1: Google Places API
            # ============================================================
            if GOOGLE_PLACES_API_KEY:
                google_data = self.lookup_google_places(legal_name, address)
                if google_data:
                    result['commercial_name'] = google_data.get('name', '')
                    result['google_rating'] = google_data.get('rating', '')
                    result['stars'] = self.rating_to_stars(google_data.get('rating', 0))
                    result['phone'] = google_data.get('phone', '')
                    result['website'] = google_data.get('website', '')
                    sources_found.append('Google')

            # ============================================================
            # PHASE 2: Proff.no (API or scraping)
            # ============================================================
            if org_number and len(org_number.replace(' ', '')) >= 9:
                if PROFF_API_KEY:
                    proff_data = self.lookup_proff_api(org_number)
                else:
                    proff_data = self.lookup_proff_scrape(org_number)

                if proff_data:
                    result['owner'] = proff_data.get('owner', '')
                    result['board_members'] = proff_data.get('board', '')
                    result['revenue'] = proff_data.get('revenue', '')
                    result['operator'] = proff_data.get('daglig_leder', '')
                    sources_found.append('Proff')

            # ============================================================
            # PHASE 3: TripAdvisor (human-like scraping for rooms)
            # ============================================================
            if result['commercial_name'] or legal_name:
                search_name = result['commercial_name'] or legal_name
                tripadvisor_data = self.lookup_tripadvisor_humanlike(search_name, address)
                if tripadvisor_data:
                    result['rooms'] = tripadvisor_data.get('rooms', '')
                    result['tripadvisor_url'] = tripadvisor_data.get('url', '')
                    if not result['stars']:
                        result['stars'] = tripadvisor_data.get('stars', '')
                    sources_found.append('TripAdvisor')

            # ============================================================
            # Determine brand from commercial name
            # ============================================================
            result['brand'] = self.detect_brand(result['commercial_name'] or legal_name)

            # Set status and data source
            result['data_source'] = ', '.join(sources_found) if sources_found else 'None'
            if sources_found:
                result['status'] = 'Complete ✓' if len(sources_found) >= 2 else 'Partial'
            else:
                result['status'] = 'No data'

            results.append(result)

            # Update UI
            self.root.after(0, lambda r=result: self.add_tree_row(r))

            # Human-like delay (random between 2-8 seconds)
            if self.is_running:
                delay = random.uniform(2, 8)
                time.sleep(delay)

                # Take a longer break every 15-25 hotels
                if idx > 0 and idx % random.randint(15, 25) == 0:
                    break_time = random.uniform(30, 60)
                    self.update_status(f"Taking a break ({int(break_time)}s) to avoid blocking...")
                    time.sleep(break_time)

        self.output_df = pd.DataFrame(results)
        self.is_running = False

        self.root.after(0, self.enrichment_complete)

    def rating_to_stars(self, rating):
        """Convert Google rating to star category"""
        try:
            r = float(rating)
            if r >= 4.5:
                return '5'
            elif r >= 4.0:
                return '4'
            elif r >= 3.5:
                return '3'
            elif r >= 3.0:
                return '2'
            else:
                return '1'
        except:
            return ''

    def detect_brand(self, name):
        """Detect hotel brand from name"""
        brands = {
            'Thon': 'Thon Hotels',
            'Scandic': 'Scandic',
            'Clarion': 'Nordic Choice',
            'Comfort': 'Nordic Choice',
            'Quality': 'Nordic Choice',
            'Radisson': 'Radisson',
            'Hilton': 'Hilton',
            'Best Western': 'Best Western',
            'Smarthotel': 'Smarthotel',
            'Citybox': 'Citybox',
            'First': 'First Hotels',
            'Rica': 'Scandic',
            'P-Hotels': 'P-Hotels',
        }

        name_upper = name.upper()
        for key, brand in brands.items():
            if key.upper() in name_upper:
                return brand
        return ''

    def lookup_google_places(self, name, address):
        """Lookup hotel in Google Places API"""
        if not GOOGLE_PLACES_API_KEY:
            return None

        try:
            # Clean up legal name for search
            search_name = re.sub(r'\b(AS|ANS|DA|ENK|DRIFT)\b', '', name, flags=re.IGNORECASE).strip()
            query = f"{search_name} {address} Norway"

            url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            params = {
                'input': query,
                'inputtype': 'textquery',
                'fields': 'name,rating,formatted_address,place_id,formatted_phone_number,website',
                'key': GOOGLE_PLACES_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('candidates'):
                place = data['candidates'][0]
                return {
                    'name': place.get('name', ''),
                    'rating': place.get('rating', ''),
                    'address': place.get('formatted_address', ''),
                    'phone': place.get('formatted_phone_number', ''),
                    'website': place.get('website', ''),
                }

        except Exception as e:
            print(f"Google Places error: {e}")

        return None

    def lookup_proff_api(self, org_number):
        """Lookup company using Proff.no API"""
        if not PROFF_API_KEY:
            return None

        try:
            org_number = re.sub(r'\D', '', str(org_number))

            # Proff.no API endpoint (adjust based on actual API docs)
            url = f"https://api.proff.no/api/companies/NO/{org_number}"
            headers = {
                'Authorization': f'Bearer {PROFF_API_KEY}',
                'Accept': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'owner': data.get('ceo', {}).get('name', ''),
                    'daglig_leder': data.get('ceo', {}).get('name', ''),
                    'board': ', '.join([m.get('name', '') for m in data.get('boardMembers', [])[:3]]),
                    'revenue': data.get('financials', {}).get('revenue', ''),
                }

        except Exception as e:
            print(f"Proff API error: {e}")

        return None

    def lookup_proff_scrape(self, org_number):
        """Lookup company by scraping Proff.no"""
        try:
            org_number = re.sub(r'\D', '', str(org_number))
            if len(org_number) != 9:
                return None

            url = f"https://www.proff.no/selskap/-/-/{org_number}"

            headers = {**HEADERS, 'User-Agent': random.choice(USER_AGENTS)}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            result = {}

            # Try to find owner/CEO (Daglig leder)
            role_elements = soup.find_all(['div', 'span', 'td'], string=re.compile(r'Daglig leder|Styreleder|CEO', re.I))
            for elem in role_elements:
                parent = elem.find_parent(['div', 'tr', 'li', 'table'])
                if parent:
                    text = parent.get_text()
                    # Look for name pattern after role
                    match = re.search(r'(?:Daglig leder|Styreleder)[:\s]+([A-ZÆØÅ][a-zæøå]+ [A-ZÆØÅ][a-zæøå]+)', text)
                    if match:
                        result['owner'] = match.group(1)
                        result['daglig_leder'] = match.group(1)
                        break

            # Try to find revenue (Driftsinntekter)
            revenue_elem = soup.find(string=re.compile(r'Driftsinntekter|Omsetning|Salgsinntekt', re.I))
            if revenue_elem:
                parent = revenue_elem.find_parent(['div', 'tr', 'table'])
                if parent:
                    numbers = re.findall(r'([\d\s,\.]+)\s*(?:MNOK|TNOK|NOK|mill|tusen)?', parent.get_text())
                    if numbers:
                        result['revenue'] = numbers[0].strip()

            return result if result else None

        except Exception as e:
            print(f"Proff.no scrape error: {e}")
            return None

    def lookup_tripadvisor_humanlike(self, name, address):
        """
        Human-like TripAdvisor lookup for room count
        Uses random delays, scrolling simulation, varied user agents
        """
        try:
            # Clean name for search
            search_name = re.sub(r'\b(AS|ANS|DA|ENK|DRIFT|HOTELL?)\b', '', name, flags=re.IGNORECASE).strip()

            # Random user agent
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,no;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }

            # First, search for the hotel
            search_url = f"https://www.tripadvisor.com/Search?q={search_name.replace(' ', '+')}&geo=190455"

            # Random delay before request (human-like)
            time.sleep(random.uniform(1, 3))

            response = requests.get(search_url, headers=headers, timeout=15)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for room count in various patterns
            text = soup.get_text()

            # Pattern: "123 rooms" or "123 rom"
            room_match = re.search(r'(\d+)\s*(?:rooms?|rom|værelser?)', text, re.IGNORECASE)
            if room_match:
                return {
                    'rooms': room_match.group(1),
                    'url': search_url
                }

            # Pattern for stars
            star_match = re.search(r'(\d(?:\.\d)?)\s*(?:star|stjerne)', text, re.IGNORECASE)

            return {
                'rooms': '',
                'stars': star_match.group(1) if star_match else '',
                'url': ''
            }

        except Exception as e:
            print(f"TripAdvisor error: {e}")
            return None

    def add_tree_row(self, result):
        """Add row to treeview"""
        self.tree.insert('', 'end', values=(
            str(result.get('org_number', ''))[:12],
            str(result.get('legal_name', ''))[:25],
            str(result.get('commercial_name', ''))[:25],
            str(result.get('address', ''))[:30],
            str(result.get('municipality', ''))[:15],
            str(result.get('property_type', ''))[:10],
            result.get('stars', ''),
            result.get('rooms', ''),
            str(result.get('brand', ''))[:15],
            str(result.get('operator', ''))[:20],
            str(result.get('owner', ''))[:20],
            str(result.get('revenue', ''))[:12],
            result.get('google_rating', ''),
            result.get('status', '')
        ))

    def update_status(self, message):
        """Update status from any thread"""
        self.root.after(0, lambda: self.status_var.set(message))

    def update_progress(self, value):
        """Update progress bar"""
        self.root.after(0, lambda: self.progress.configure(value=value))

    def enrichment_complete(self):
        """Called when enrichment is done"""
        self.enrich_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.export_btn.config(state="normal")
        self.status_var.set(f"Enrichment complete! {len(self.output_df)} records processed.")

    def export_to_excel(self):
        """Export enriched data to Excel"""
        if self.output_df is None:
            messagebox.showwarning("No Data", "No enriched data to export.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"Norway_Hotels_Enriched_{timestamp}.xlsx"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=default_filename
        )

        if not filepath:
            return

        try:
            # Define column order for export
            export_columns = [
                'org_number', 'legal_name', 'commercial_name', 'address', 'municipality',
                'property_type', 'stars', 'rooms', 'brand', 'operator', 'owner',
                'board_members', 'revenue', 'google_rating', 'phone', 'email', 'website',
                'tripadvisor_url', 'data_source', 'last_updated', 'status'
            ]

            # Only include columns that exist
            available_columns = [c for c in export_columns if c in self.output_df.columns]
            export_df = self.output_df[available_columns]

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                export_df.to_excel(writer, sheet_name='Norway Hotels', index=False)

                worksheet = writer.sheets['Norway Hotels']

                # Column widths
                column_widths = {
                    'A': 12, 'B': 25, 'C': 25, 'D': 30, 'E': 15,
                    'F': 12, 'G': 8, 'H': 8, 'I': 15, 'J': 20,
                    'K': 20, 'L': 25, 'M': 12, 'N': 8, 'O': 15,
                    'P': 20, 'Q': 30, 'R': 40, 'S': 20, 'T': 12, 'U': 10
                }

                for col, width in column_widths.items():
                    worksheet.column_dimensions[col].width = width

                # Style headers
                from openpyxl.styles import Font, PatternFill, Alignment

                header_font = Font(bold=True, color='FFFFFF')
                header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')

                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center', wrap_text=True)

                # Freeze header row
                worksheet.freeze_panes = 'A2'

            messagebox.showinfo("Success", f"Exported {len(export_df)} hotels to:\n{filepath}")
            os.startfile(os.path.dirname(filepath))

        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")


def main():
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = HotelEnricherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
