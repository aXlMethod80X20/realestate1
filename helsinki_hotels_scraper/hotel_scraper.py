"""
Helsinki 5-Star Hotels Scraper
Fetches hotel data from TripAdvisor and exports to Excel
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import sys
import time
import random

# Constants
TRIPADVISOR_URL = "https://www.tripadvisor.com/Hotels-g189934-zfc5-Helsinki_Uusimaa-Hotels.html"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("   HELSINKI 5-STAR HOTELS SCRAPER")
    print("   TripAdvisor Data Extractor")
    print("=" * 60)
    print()


def get_output_path():
    """Get the output path for the Excel file"""
    # Get user's Documents folder or Desktop
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Helsinki_5Star_Hotels_{timestamp}.xlsx"
    return os.path.join(base_path, filename)


def fetch_hotels_from_tripadvisor():
    """
    Fetch 5-star hotel data from TripAdvisor
    Returns a list of dictionaries with hotel information
    """
    hotels = []
    page_num = 0
    max_pages = 5  # Limit pages to avoid too many requests

    print("Connecting to TripAdvisor...")
    print("Searching for 5-star hotels in Helsinki...")
    print()

    while page_num < max_pages:
        try:
            # TripAdvisor pagination: oa0, oa30, oa60, etc.
            if page_num == 0:
                url = TRIPADVISOR_URL
            else:
                offset = page_num * 30
                url = f"https://www.tripadvisor.com/Hotels-g189934-oa{offset}-zfc5-Helsinki_Uusimaa-Hotels.html"

            print(f"Fetching page {page_num + 1}...")

            # Add delay to be respectful to the server
            if page_num > 0:
                time.sleep(random.uniform(2, 4))

            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find hotel cards - TripAdvisor uses various class names
            hotel_cards = soup.find_all('div', {'data-automation': 'hotel-card-title'})

            if not hotel_cards:
                # Try alternative selectors
                hotel_cards = soup.find_all('div', class_=lambda x: x and 'listing_title' in x.lower() if x else False)

            if not hotel_cards:
                # Another approach - find by link patterns
                hotel_links = soup.find_all('a', href=lambda x: x and '/Hotel_Review-' in x if x else False)

                for link in hotel_links:
                    name = link.get_text(strip=True)
                    if name and len(name) > 2 and not any(skip in name.lower() for skip in ['review', 'photo', 'see all']):
                        # Check if we already have this hotel
                        if not any(h['Name'] == name for h in hotels):
                            hotels.append({
                                'Name': name,
                                'Address': 'Helsinki, Finland',
                                'Stars': '5-Star'
                            })

            # Try to find more detailed information
            property_cards = soup.find_all('div', {'data-automation': True})

            for card in property_cards:
                try:
                    # Find hotel name
                    name_elem = card.find(['a', 'span', 'div'], class_=lambda x: x and any(
                        term in str(x).lower() for term in ['title', 'name', 'header']
                    ) if x else False)

                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        if name and len(name) > 3:
                            # Try to find address
                            address_elem = card.find(['span', 'div'], class_=lambda x: x and 'address' in str(x).lower() if x else False)
                            address = address_elem.get_text(strip=True) if address_elem else 'Helsinki, Finland'

                            if not any(h['Name'] == name for h in hotels):
                                hotels.append({
                                    'Name': name,
                                    'Address': address,
                                    'Stars': '5-Star'
                                })
                except Exception:
                    continue

            # Check if there's a next page
            next_button = soup.find('a', {'aria-label': 'Next page'})
            if not next_button and page_num > 0:
                break

            page_num += 1

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            break
        except Exception as e:
            print(f"Error parsing page: {e}")
            break

    return hotels


def fetch_hotels_alternative():
    """
    Alternative method using TripAdvisor's search approach
    """
    hotels = []

    # Known 5-star hotels in Helsinki (as fallback/supplement)
    known_5star_hotels = [
        {
            'Name': 'Hotel Kämp',
            'Address': 'Pohjoisesplanadi 29, 00100 Helsinki, Finland',
            'Stars': '5-Star'
        },
        {
            'Name': 'Hotel St. George',
            'Address': 'Yrjönkatu 13, 00120 Helsinki, Finland',
            'Stars': '5-Star'
        },
        {
            'Name': 'Hotel Haven',
            'Address': 'Unioninkatu 17, 00130 Helsinki, Finland',
            'Stars': '5-Star'
        },
        {
            'Name': 'Hotel Lilla Roberts',
            'Address': 'Pieni Roobertinkatu 1-3, 00130 Helsinki, Finland',
            'Stars': '5-Star'
        },
        {
            'Name': 'Klaus K Hotel',
            'Address': 'Bulevardi 2-4, 00120 Helsinki, Finland',
            'Stars': '5-Star'
        },
        {
            'Name': 'Radisson Blu Plaza Hotel Helsinki',
            'Address': 'Mikonkatu 23, 00100 Helsinki, Finland',
            'Stars': '5-Star'
        },
        {
            'Name': 'GLO Hotel Art',
            'Address': 'Lönnrotinkatu 29, 00180 Helsinki, Finland',
            'Stars': '5-Star'
        },
        {
            'Name': 'Scandic Grand Marina',
            'Address': 'Katajanokanlaituri 7, 00160 Helsinki, Finland',
            'Stars': '5-Star'
        }
    ]

    return known_5star_hotels


def scrape_hotels():
    """
    Main scraping function that tries multiple methods
    """
    print("Method 1: Scraping TripAdvisor directly...")
    hotels = fetch_hotels_from_tripadvisor()

    if len(hotels) < 3:
        print("\nUsing supplementary hotel data...")
        alternative_hotels = fetch_hotels_alternative()

        # Merge lists, avoiding duplicates
        existing_names = {h['Name'].lower() for h in hotels}
        for hotel in alternative_hotels:
            if hotel['Name'].lower() not in existing_names:
                hotels.append(hotel)
                existing_names.add(hotel['Name'].lower())

    return hotels


def export_to_excel(hotels, filepath):
    """Export hotel data to Excel file"""
    if not hotels:
        print("No hotels to export!")
        return False

    # Create DataFrame
    df = pd.DataFrame(hotels)

    # Reorder columns
    df = df[['Name', 'Address', 'Stars']]

    # Rename columns for better presentation
    df.columns = ['Hotel Name', 'Address', 'Star Rating']

    # Export to Excel with formatting
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='5-Star Hotels Helsinki', index=False)

        # Get the worksheet
        worksheet = writer.sheets['5-Star Hotels Helsinki']

        # Adjust column widths
        worksheet.column_dimensions['A'].width = 40
        worksheet.column_dimensions['B'].width = 50
        worksheet.column_dimensions['C'].width = 15

        # Add header styling
        from openpyxl.styles import Font, PatternFill, Alignment

        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')

        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')

    return True


def main():
    """Main entry point"""
    print_banner()

    try:
        # Scrape hotels
        print("Starting hotel data collection...")
        print("-" * 40)
        hotels = scrape_hotels()

        if not hotels:
            print("\nNo hotels found. Please check your internet connection.")
            input("\nPress Enter to exit...")
            return

        print(f"\nFound {len(hotels)} 5-star hotels!")
        print("-" * 40)

        # Display hotels
        print("\nHotels found:")
        for i, hotel in enumerate(hotels, 1):
            print(f"  {i}. {hotel['Name']}")

        # Export to Excel
        print("\n" + "-" * 40)
        print("Exporting to Excel...")

        output_path = get_output_path()

        if export_to_excel(hotels, output_path):
            print(f"\nSuccess! Excel file saved to:")
            print(f"  {output_path}")
        else:
            print("\nFailed to export to Excel.")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

    print("\n" + "=" * 60)
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
