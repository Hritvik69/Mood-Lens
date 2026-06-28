#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kaggle Dataset Downloader
Downloads FER2013 emotion dataset for training and evaluation.
"""

import os
import sys
from pathlib import Path

def download_dataset():
    """
    Downloads the FER2013 dataset from Kaggle using kaggle-cli.
    Requires kaggle package to be installed and authenticated.
    """
    print("=" * 60)
    print("🚀 Kaggle Dataset Downloader")
    print("=" * 60)
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "fer2013"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Target directory: {data_dir}")
    
    # Check if kaggle is installed
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("❌ Kaggle package not found!")
        print("💡 Install it with: pip install kaggle")
        sys.exit(1)
    
    # Setup authentication
    # For Kaggle API, you need a kaggle.json file in ~/.kaggle/
    # The format should be: {"username":"your_username","key":"your_key"}
    # However, if you have KAGGLE_USERNAME and KAGGLE_KEY env vars, they work too.
    
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    
    if not kaggle_json.exists():
        print("⚠️  kaggle.json not found!")
        print(f"📝 Create it at: {kaggle_json}")
        print('   Format: {"username":"USERNAME","key":"API_KEY"}')
        print()
        print("🔗 Get your API key from: https://www.kaggle.com/account")
        
        # Try to use environment variables as fallback
        if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
            print("❌ No environment variables found either (KAGGLE_USERNAME, KAGGLE_KEY)")
            sys.exit(1)
        else:
            print("✅ Using environment variables for authentication")
    
    # Initialize API
    try:
        api = KaggleApi()
        api.authenticate()
        print("✅ Kaggle authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)
    
    # Download dataset
    dataset_name = "msambare/fer2013"
    print(f"\n⬇️  Downloading dataset: {dataset_name}")
    print("⏳ This may take a few minutes...")
    
    try:
        api.dataset_download_files(
            dataset_name, 
            path=str(data_dir), 
            unzip=True,
            quiet=False
        )
        print(f"\n✅ Dataset downloaded successfully to: {data_dir}")
        
        # List downloaded files
        files = list(data_dir.rglob("*"))
        print(f"\n📊 Downloaded {len(files)} files:")
        for f in sorted(files)[:10]:  # Show first 10
            if f.is_file():
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"   - {f.name} ({size_mb:.2f} MB)")
        if len(files) > 10:
            print(f"   ... and {len(files) - 10} more files")
            
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Download complete! Dataset ready for use.")
    print("=" * 60)

if __name__ == "__main__":
    download_dataset()
