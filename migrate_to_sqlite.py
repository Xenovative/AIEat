"""
Migrate restaurant data from JSON to SQLite database
"""
import json
import sqlite3
from pathlib import Path

def create_database():
    """Create SQLite database with restaurants table"""
    conn = sqlite3.connect('data/restaurants.db')
    cursor = conn.cursor()
    
    # Create restaurants table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_en TEXT,
        name_zh TEXT,
        cuisine_en TEXT,
        cuisine_zh TEXT,
        district_en TEXT,
        district_zh TEXT,
        address_en TEXT,
        address_zh TEXT,
        price TEXT,
        phone TEXT,
        url TEXT,
        rating_smile INTEGER DEFAULT 0,
        rating_ok INTEGER DEFAULT 0,
        rating_cry INTEGER DEFAULT 0,
        description_en TEXT,
        description_zh TEXT,
        popular_dishes_en TEXT,
        popular_dishes_zh TEXT,
        opening_hours_en TEXT,
        opening_hours_zh TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cuisine_en ON restaurants(cuisine_en)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_district_en ON restaurants(district_en)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price ON restaurants(price)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rating_smile ON restaurants(rating_smile)')
    
    conn.commit()
    return conn

def migrate_data():
    """Migrate data from JSON to SQLite"""
    print("🔄 Starting migration from JSON to SQLite...")
    
    # Load JSON data
    with open('data/openrice_complete.json', 'r', encoding='utf-8') as f:
        restaurants = json.load(f)
    
    print(f"📂 Loaded {len(restaurants)} restaurants from JSON")
    
    # Create database
    conn = create_database()
    cursor = conn.cursor()
    
    # Insert data
    inserted = 0
    for restaurant in restaurants:
        try:
            cursor.execute('''
            INSERT INTO restaurants (
                name_en, name_zh, cuisine_en, cuisine_zh,
                district_en, district_zh, address_en, address_zh,
                price, phone, url,
                rating_smile, rating_ok, rating_cry,
                description_en, description_zh,
                popular_dishes_en, popular_dishes_zh,
                opening_hours_en, opening_hours_zh
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                restaurant.get('name_en', ''),
                restaurant.get('name_zh', ''),
                restaurant.get('cuisine_en', ''),
                restaurant.get('cuisine_zh', ''),
                restaurant.get('district_en', ''),
                restaurant.get('district_zh', ''),
                restaurant.get('address_en', ''),
                restaurant.get('address_zh', ''),
                restaurant.get('price', ''),
                restaurant.get('phone', ''),
                restaurant.get('url', ''),
                int(restaurant.get('rating_smile', 0) or 0),
                int(restaurant.get('rating_ok', 0) or 0),
                int(restaurant.get('rating_cry', 0) or 0),
                restaurant.get('description_en', ''),
                restaurant.get('description_zh', ''),
                restaurant.get('popular_dishes_en', ''),
                restaurant.get('popular_dishes_zh', ''),
                restaurant.get('opening_hours_en', ''),
                restaurant.get('opening_hours_zh', '')
            ))
            inserted += 1
            
            if inserted % 500 == 0:
                print(f"   ✓ Inserted {inserted} restaurants...")
                
        except Exception as e:
            print(f"   ❌ Error inserting restaurant: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✅ Migration complete! Inserted {inserted} restaurants into SQLite")
    print(f"📊 Database saved to: data/restaurants.db")

if __name__ == '__main__':
    migrate_data()
