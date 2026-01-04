"""
Build script for creating the Helsinki Hotels Scraper executable
Run this script to generate the .exe file
"""

import subprocess
import sys
import os


def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def build_executable():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable...")

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Single executable
        "--windowed",          # No console window (GUI app)
        "--name", "Helsinki_Hotels_Scraper",
        "--hidden-import=openpyxl",
        "--hidden-import=pandas",
        "--hidden-import=requests",
        "--hidden-import=bs4",
        "--hidden-import=tkinter",
        "--hidden-import=openpyxl.styles",
        "--clean",             # Clean build
        "hotel_scraper_gui.py"
    ]

    subprocess.check_call(cmd)


def main():
    print("=" * 50)
    print("  Helsinki Hotels Scraper - Build Script")
    print("=" * 50)
    print()

    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    try:
        install_requirements()
        build_executable()

        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)
        print("\nYour executable is located at:")
        print(f"  {os.path.join(script_dir, 'dist', 'Helsinki_Hotels_Scraper.exe')}")
        print("\nYou can distribute this single .exe file to customers.")

    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
