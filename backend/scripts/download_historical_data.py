"""Script to download 30 years of historical Indian market data from iTick and save to MongoDB"""
import sys
import os
from datetime import datetime, timedelta
import time
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.mongodb import mongodb_manager
from app.services.market_data import market_data_service

# Import comprehensive stock list
from fetch_nse_stocks import get_comprehensive_nse_stocks

# Get comprehensive stock list (2000+ companies)
INDIAN_STOCKS = get_comprehensive_nse_stocks()

# Major Indian Market Indices (use Yahoo Finance symbol format)
INDIAN_INDICES = [
    "^NSEI",       # Nifty 50
    "^NSEBANK",    # Nifty Bank
    "^CNXIT",      # Nifty IT
    "^CNXAUTO",    # Nifty Auto
    "^CNXPHARMA",  # Nifty Pharma
    "^CNXFMCG",    # Nifty FMCG
    "^CNXMETAL",   # Nifty Metal
    "^CNXREALTY",  # Nifty Realty
    "^CNXENERGY",  # Nifty Energy
    "^CNXINFRA",   # Nifty Infrastructure
    "^CNXPSE",     # Nifty PSU Bank
    "^CNXMEDIA",   # Nifty Media
    "^NSEMDCP50",  # Nifty Midcap 50
    "^NSEMDCP100", # Nifty Midcap 100
    "^NSMIDCP",    # Nifty Midcap 150
    "^CNXSC",      # Nifty Smallcap 250
    "^BSESN",      # BSE Sensex
    "^CRSLDX",     # BSE SmallCap
    "^BSEMDCP",    # BSE MidCap
]

# Intervals to download
INTERVALS = ["1d"]  # Start with daily data, can add "1h", "15m" later


def download_stock_data(symbol: str, interval: str = "1d", years: int = 30, is_index: bool = False):
    """
    Download historical data for a symbol
    
    Args:
        symbol: Stock symbol (NSE) or Index symbol (e.g., ^NSEI)
        interval: Time interval
        years: Number of years of historical data
        is_index: True if symbol is a market index, False for stocks
    """
    display_name = symbol if is_index else f"{symbol} (NSE)"
    print(f"\n📊 Downloading {display_name} - {interval} data...")
    
    try:
        # Check if data already exists
        collection = mongodb_manager.get_collection("market_data")
        existing_count = collection.count_documents({
            "symbol": symbol,
            "interval": interval
        })
        
        if existing_count > 0:
            print(f"  ⏭️  Skipping {symbol} - {existing_count} records already exist")
            return existing_count
        
        # Calculate date range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=years * 365)
        
        # For indices, use symbol as-is. For stocks, add .NS suffix
        yf_symbol = symbol if is_index else f"{symbol}.NS"
        
        # Fetch data using market data service
        df = market_data_service._fetch_yfinance_data(
            symbol=yf_symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time
        )
        
        if df.empty:
            print(f"  ⚠️  No data found for {symbol}")
            return 0
        
        # Convert DataFrame to list of dicts for MongoDB
        records = []
        for timestamp, row in df.iterrows():
            record = {
                'timestamp': timestamp.to_pydatetime(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            }
            records.append(record)
        
        # Save to MongoDB
        count = mongodb_manager.insert_market_data(symbol, interval, records)
        print(f"  ✓ Saved {count} records for {symbol} ({df.index.min()} to {df.index.max()})")
        
        return count
        
    except Exception as e:
        print(f"  ❌ Error downloading {symbol}: {str(e)}")
        return 0


def main():
    """Main function to download all historical data"""
    print("=" * 70)
    print("🚀 Starting Historical Data Download")
    print("=" * 70)
    print(f"MongoDB URI: {settings.MONGODB_URI}")
    print(f"iTick API Key: {'*' * 20}{settings.ITICK_API_KEY[-10:]}")
    print(f"Market Indices to download: {len(INDIAN_INDICES)}")
    print(f"Stocks to download: {len(INDIAN_STOCKS)}")
    print(f"Total symbols: {len(INDIAN_INDICES) + len(INDIAN_STOCKS)}")
    print(f"Intervals: {INTERVALS}")
    print("=" * 70)
    
    # Connect to MongoDB
    try:
        mongodb_manager.connect()
        print("✓ Connected to MongoDB")
        
        # Create indexes
        mongodb_manager.create_indexes()
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # Download data
    total_records = 0
    successful = 0
    failed = 0
    skipped = 0
    
    start_time = time.time()
    
    # Phase 1: Download Market Indices
    print("\n" + "=" * 70)
    print("📈 Phase 1: Downloading Market Indices")
    print("=" * 70)
    
    for idx, symbol in enumerate(INDIAN_INDICES, 1):
        print(f"\n[{idx}/{len(INDIAN_INDICES)}] Processing {symbol}...")
        
        for interval in INTERVALS:
            try:
                count = download_stock_data(symbol, interval, years=30, is_index=True)
                if count > 0:
                    total_records += count
                    successful += 1
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed += 1
    
    # Phase 2: Download Individual Stocks (TEMPORARILY DISABLED - TESTING INDICES ONLY)
    print("\n" + "=" * 70)
    print("⏸️  Phase 2: Skipping Individual Stocks (testing indices only)")
    print("=" * 70)
    
    # UNCOMMENT BELOW TO ENABLE FULL STOCK DOWNLOAD
    """
    # Sort stocks alphabetically for better organization
    sorted_stocks = sorted(INDIAN_STOCKS)
    
    for idx, symbol in enumerate(sorted_stocks, 1):
        print(f"\n[{idx}/{len(sorted_stocks)}] Processing {symbol}...")
        
        for interval in INTERVALS:
            try:
                count = download_stock_data(symbol, interval, years=30)
                if count > 0:
                    total_records += count
                    successful += 1
                elif count == 0:
                    failed += 1
                else:
                    skipped += 1
                
                # Rate limiting - pause between requests
                time.sleep(1)
                
                # Progress update every 50 stocks
                if idx % 50 == 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx + len(INDIAN_INDICES))
                    remaining = (len(sorted_stocks) - idx) * avg_time
                    print(f"\n📊 Progress: {idx}/{len(sorted_stocks)} stocks ({idx*100//len(sorted_stocks)}%)")
                    print(f"⏱️  Estimated time remaining: {remaining/60:.1f} minutes")
                    print(f"💾 Total records saved so far: {total_records:,}\n")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed += 1
    """
    sorted_stocks = []  # Empty for now
    
    # Summary
    elapsed_time = time.time() - start_time
    total_symbols = len(INDIAN_INDICES) + len(sorted_stocks)
    print("\n" + "=" * 70)
    print("🎉 Download Complete!")
    print("=" * 70)
    print(f"Market Indices processed: {len(INDIAN_INDICES)}")
    print(f"Individual Stocks processed: {len(sorted_stocks)}")
    print(f"Total symbols processed: {total_symbols}")
    print(f"Successful downloads: {successful}")
    print(f"Failed downloads: {failed}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Total records saved: {total_records:,}")
    print(f"Time taken: {elapsed_time / 60:.2f} minutes ({elapsed_time / 3600:.2f} hours)")
    print(f"Average time per symbol: {elapsed_time / total_symbols:.2f} seconds")
    print("=" * 60)
    
    # Close MongoDB connection
    mongodb_manager.disconnect()
    print("\n✅ All done!")


if __name__ == "__main__":
    main()
