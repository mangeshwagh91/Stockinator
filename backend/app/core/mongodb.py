"""MongoDB connection and management"""
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from app.core.config import settings


class MongoDBManager:
    """Manager for MongoDB connections"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.async_client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.async_db = None
    
    def connect(self):
        """Connect to MongoDB (synchronous)"""
        self.client = MongoClient(settings.MONGODB_URI)
        db_name = settings.MONGODB_URI.split('/')[-1] or "Stockinator"
        self.db = self.client[db_name]
        return self
    
    def connect_async(self):
        """Connect to MongoDB (asynchronous)"""
        self.async_client = AsyncIOMotorClient(settings.MONGODB_URI)
        db_name = settings.MONGODB_URI.split('/')[-1] or "Stockinator"
        self.async_db = self.async_client[db_name]
        return self
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client is not None:
            self.client.close()
        if self.async_client is not None:
            self.async_client.close()
    
    def get_collection(self, name: str):
        """Get a collection from the database"""
        if self.db is None:
            self.connect()
        return self.db[name]
    
    def insert_market_data(self, symbol: str, interval: str, data: list):
        """Insert market data into MongoDB"""
        collection = self.get_collection("market_data")
        
        # Add metadata to each record
        records = []
        for record in data:
            record['symbol'] = symbol
            record['interval'] = interval
            records.append(record)
        
        if records:
            result = collection.insert_many(records)
            return len(result.inserted_ids)
        return 0
    
    def get_market_data(self, symbol: str, interval: str, start_time=None, end_time=None):
        """Retrieve market data from MongoDB"""
        collection = self.get_collection("market_data")
        
        query = {
            "symbol": symbol,
            "interval": interval
        }
        
        if start_time or end_time:
            query['timestamp'] = {}
            if start_time:
                query['timestamp']['$gte'] = start_time
            if end_time:
                query['timestamp']['$lte'] = end_time
        
        cursor = collection.find(query).sort('timestamp', 1)
        return list(cursor)
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        collection = self.get_collection("market_data")
        
        # Create compound index on symbol, interval, and timestamp
        collection.create_index([
            ("symbol", 1),
            ("interval", 1),
            ("timestamp", 1)
        ], unique=True)
        
        print("✓ MongoDB indexes created")


# Global MongoDB instance
mongodb_manager = MongoDBManager()
