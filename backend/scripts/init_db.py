"""Database initialization script"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init_db, engine, Base
from app.models.trade import Trade
from app.models.signal import Signal
from app.models.news import News


def create_tables():
    """Create all database tables"""
    print("🗄️  Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
    
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)


def drop_tables():
    """Drop all database tables (use with caution!)"""
    print("⚠️  Dropping all database tables...")
    
    response = input("Are you sure? This will delete all data! (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped!")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization")
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Drop all tables before creating'
    )
    
    args = parser.parse_args()
    
    if args.drop:
        drop_tables()
    
    create_tables()
