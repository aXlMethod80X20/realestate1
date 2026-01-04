# Helsinki 5-Star Hotels Scraper

A simple Windows application that fetches 5-star hotel data from Helsinki and exports it to Excel.

## Features

- 🏨 Fetches 5-star hotel data (name, address, star rating)
- 📊 Exports data to formatted Excel file
- 🖥️ User-friendly GUI interface
- 📦 Single executable - no installation required

## For Customers (Using the EXE)

1. **Double-click** `Helsinki_Hotels_Scraper.exe`
2. Click **"Fetch Hotels"** to get the latest hotel data
3. Click **"Export to Excel"** to save the data
4. Choose where to save your Excel file
5. Done! Your hotel data is ready.

## For Developers (Building the EXE)

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Build Steps

1. Open Command Prompt in this folder
2. Run the build script:

```batch
build_exe.bat
```

Or using Python:

```bash
python build_exe.py
```

3. Find your executable in the `dist/` folder

### Manual Build

```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller --onefile --windowed --name "Helsinki_Hotels_Scraper" hotel_scraper_gui.py
```

## Files

| File | Description |
|------|-------------|
| `hotel_scraper_gui.py` | Main GUI application |
| `hotel_scraper.py` | Console version (alternative) |
| `requirements.txt` | Python dependencies |
| `build_exe.bat` | Windows build script |
| `build_exe.py` | Python build script |

## Output Format

The Excel file contains:

| Hotel Name | Address | Star Rating |
|------------|---------|-------------|
| Hotel Kämp | Pohjoisesplanadi 29, 00100 Helsinki | 5-Star |
| Hotel St. George | Yrjönkatu 13, 00120 Helsinki | 5-Star |
| ... | ... | ... |

## Notes

- Internet connection required to fetch latest data
- Data sourced from TripAdvisor
- Updates can be fetched anytime by clicking "Fetch Hotels"
