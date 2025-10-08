from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import json
import os
import requests
import sqlite3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Database connection
def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect('data/restaurants.db')
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_search_history_table():
    """Initialize search history table if it doesn't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                preferences TEXT,
                cuisine TEXT,
                district TEXT,
                budget TEXT,
                results_count INTEGER,
                language TEXT,
                session_id TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating search_history table: {e}")

def init_database_from_json():
    """Initialize database from JSON file if database doesn't exist"""
    import os
    
    db_path = 'data/restaurants.db'
    json_path = 'data/openrice_complete.json'
    
    # Check if database already exists
    if os.path.exists(db_path):
        return False
    
    print("🔧 Database not found. Creating from JSON...")
    
    # Check if JSON file exists
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return False
    
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            restaurants_data = json.load(f)
        
        print(f"📄 Loaded {len(restaurants_data)} restaurants from JSON")
        
        # Create database and table
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_en TEXT,
                name_zh TEXT,
                address_en TEXT,
                address_zh TEXT,
                district_en TEXT,
                district_zh TEXT,
                cuisine_en TEXT,
                cuisine_zh TEXT,
                price TEXT,
                phone TEXT,
                opening_hours_en TEXT,
                opening_hours_zh TEXT,
                rating_smile TEXT,
                rating_ok TEXT,
                rating_cry TEXT,
                description_en TEXT,
                description_zh TEXT,
                popular_dishes_en TEXT,
                popular_dishes_zh TEXT,
                url TEXT
            )
        ''')
        
        # Insert data
        print("💾 Inserting data into database...")
        for restaurant in restaurants_data:
            cursor.execute('''
                INSERT INTO restaurants (
                    name_en, name_zh, address_en, address_zh, district_en, district_zh,
                    cuisine_en, cuisine_zh, price, phone, opening_hours_en, opening_hours_zh,
                    rating_smile, rating_ok, rating_cry, description_en, description_zh,
                    popular_dishes_en, popular_dishes_zh, url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                restaurant.get('name_en'),
                restaurant.get('name_zh'),
                restaurant.get('address_en'),
                restaurant.get('address_zh'),
                restaurant.get('district_en'),
                restaurant.get('district_zh'),
                restaurant.get('cuisine_en'),
                restaurant.get('cuisine_zh'),
                restaurant.get('price'),
                restaurant.get('phone'),
                restaurant.get('opening_hours_en'),
                restaurant.get('opening_hours_zh'),
                restaurant.get('rating_smile'),
                restaurant.get('rating_ok'),
                restaurant.get('rating_cry'),
                restaurant.get('description_en'),
                restaurant.get('description_zh'),
                restaurant.get('popular_dishes_en'),
                restaurant.get('popular_dishes_zh'),
                restaurant.get('url')
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database created successfully with {len(restaurants_data)} restaurants!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def load_restaurants():
    """Load all restaurants from SQLite database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM restaurants')
        rows = cursor.fetchall()
        conn.close()
        
        # Convert Row objects to dictionaries
        restaurants = [dict(row) for row in rows]
        
        print(f"📂 Loaded {len(restaurants)} restaurants from SQLite")
        if restaurants:
            print(f"🔍 Sample restaurant keys: {list(restaurants[0].keys())[:10]}")
        
        return restaurants
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        print("⚠️ Attempting to create database from JSON...")
        
        # Try to initialize from JSON
        if init_database_from_json():
            # Try loading again
            return load_restaurants()
        else:
            print("❌ Failed to initialize database")
            return []

restaurants = load_restaurants()

# Initialize search history table
init_search_history_table()

# AI Service Configuration
AI_SERVICE = os.getenv('AI_SERVICE', 'ollama')  # 'ollama', 'openrouter', or 'openai'
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

def analyze_with_ollama(prompt):
    """Use Ollama local LLM for analysis"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['response']
        else:
            return None
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

def analyze_with_openrouter(prompt):
    """Use OpenRouter cloud AI for analysis"""
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return None
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return None

def analyze_with_openai(prompt):
    """Use OpenAI API for analysis"""
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return None
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None

def analyze_preferences(user_input):
    """Use AI to analyze user preferences and extract key information"""
    lang = user_input.get('lang', 'en')
    conversation_history = user_input.get('conversation_history', [])
    
    # Build context from conversation history
    context = ""
    print(f"🗨️ Conversation history length: {len(conversation_history)}")
    if conversation_history:
        context = "\n\n對話歷史 (用於理解上下文):\n" if lang == 'zh' else "\n\nConversation History (for context):\n"
        for msg in conversation_history[-4:]:  # Last 4 messages
            role = "用戶" if msg['role'] == 'user' else "AI" if lang == 'zh' else msg['role'].title()
            context += f"{role}: {msg['message']}\n"
            if msg['role'] == 'assistant' and 'analysis' in msg:
                analysis = msg['analysis']
                if analysis.get('cuisine_types'):
                    cuisines = ', '.join(analysis['cuisine_types'])
                    context += f"  (之前推薦: {cuisines})\n" if lang == 'zh' else f"  (Previous: {cuisines})\n"
                    print(f"📝 Adding previous cuisine to context: {cuisines}")
        print(f"📋 Context being sent:\n{context}")
    
    if lang == 'zh':
        prompt = f"""分析以下餐廳偏好，提取關鍵信息並生成一個友好的回應：
{context}
當前用戶輸入：{user_input['preferences']}
預算：{user_input['budget']}
地區：{user_input['district']}

**重要規則 - 必須嚴格遵守**:
1. **如果用戶提到新的菜系/餐廳類型**（例如「日本菜」、「酒吧」、「bar」、「pub」、「cafe」），使用新的類型，**忽略歷史**
2. **如果用戶只提到地區**（例如「旺角呢」、「尖沙咀有冇」）而**沒有提到任何菜系**，從對話歷史中複製之前的cuisine_types
3. 如果是第一次對話，cuisine_types可以是空數組

**例子**:
- 對話歷史: 意大利菜
- 用戶說: "旺角呢?" → 返回: "cuisine_types": ["意大利菜"] (保持)
- 用戶說: "想搵bar/酒吧" → 返回: "cuisine_types": ["bar", "pub"] (新類型)
- 用戶說: "食完想去飲嘢" → 返回: "cuisine_types": ["bar", "pub", "cafe"] (新需求)

請提供：
1. 匹配的菜系類型（例如：意大利菜、日本菜、中菜等）
2. 用餐氛圍（休閒、高級、浪漫、家庭友好、慶祝等）
3. 關鍵要求
4. 飲食限制
5. **從用戶輸入中提取的預算範圍**（如果提到，返回："Below $50", "$51-100", "$101-200", "$201-400", "$401-800", "Above $800"，如果沒提到返回null）
6. **從用戶輸入中提取的地區**（如果提到香港地區名稱，返回該地區的英文或中文名，如果沒提到返回null）
7. 一個簡短、友好、口語化的回應（用廣東話風格，像朋友聊天一樣）

**負面提示詞（用戶不想要的）**：
- 如果用戶說「唔要」、「避免」、「不喜歡」、「no」、「avoid」、「don't want」等，將這些加入dietary_restrictions
- 例如：「唔要海鮮」→ dietary_restrictions: ["seafood"]
- 例如：「避免辣」→ dietary_restrictions: ["spicy"]
- 例如：「no pork」→ dietary_restrictions: ["pork"]

只返回JSON格式：{{"cuisine_types": ["菜系"], "atmosphere": "氛圍", "key_requirements": ["要求"], "dietary_restrictions": ["不想要的"], "extracted_budget": "預算範圍或null", "extracted_district": "地區或null", "ai_message": "友好的回應"}}
例如：{{"cuisine_types": ["日本菜"], "atmosphere": "慶祝", "key_requirements": ["高質素", "生日慶祝"], "dietary_restrictions": ["seafood", "spicy"], "extracted_budget": "$201-400", "extracted_district": "旺角", "ai_message": "好呀！生日快樂！我幫你搵旺角太子附近啲高質嘅日本餐廳，慶祝生日就要食好啲！我會避開海鮮同辣嘅！"}}"""
    else:
        prompt = f"""Analyze the following restaurant preference and generate a friendly response:
{context}
Current User Input: {user_input['preferences']}
Budget: {user_input['budget']}
District: {user_input['district']}

**Important Rules - MUST FOLLOW STRICTLY**:
1. **If user mentions NEW cuisine/restaurant type** (e.g., "japanese", "bar", "pub", "cafe", "after dinner drinks"), use the NEW type, **ignore history**
2. **If user only mentions location** (e.g., "how about Mong Kok", "any in TST") and **does NOT mention any cuisine**, copy cuisine_types from conversation history
3. If this is the first conversation, cuisine_types can be empty array

**Examples**:
- History: italian
- User: "how about Mong Kok?" → Return: "cuisine_types": ["italian"] (keep)
- User: "looking for bars" → Return: "cuisine_types": ["bar", "pub"] (new type)
- User: "after dinner drinks" → Return: "cuisine_types": ["bar", "pub", "cafe"] (new need)

Provide:
1. Cuisine types that match (e.g., italian, japanese, chinese, etc.)
2. Dining atmosphere (casual, fine dining, romantic, family-friendly, celebration, etc.)
3. Key requirements or must-haves
4. Any dietary restrictions
5. **Extracted budget range from user input** (if mentioned, return: "Below $50", "$51-100", "$101-200", "$201-400", "$401-800", "Above $800", otherwise return null)
6. **Extracted district from user input** (if Hong Kong district mentioned, return the district name in English or Chinese, otherwise return null)
7. A short, friendly, conversational response (like chatting with a friend)

**Negative prompts (what user doesn't want)**:
- If user says "no", "avoid", "don't want", "not", "without", etc., add these to dietary_restrictions
- Example: "no seafood" → dietary_restrictions: ["seafood"]
- Example: "avoid spicy" → dietary_restrictions: ["spicy"]
- Example: "don't like pork" → dietary_restrictions: ["pork"]

Return ONLY JSON format: {{"cuisine_types": ["cuisine"], "atmosphere": "vibe", "key_requirements": ["requirements"], "dietary_restrictions": ["things to avoid"], "extracted_budget": "budget or null", "extracted_district": "district or null", "ai_message": "friendly response"}}
Example: {{"cuisine_types": ["japanese"], "atmosphere": "celebration", "key_requirements": ["high quality", "birthday"], "dietary_restrictions": ["seafood", "spicy"], "extracted_budget": "$201-400", "extracted_district": "Mong Kok", "ai_message": "Happy birthday! Let me find you some high-quality Japanese restaurants in Mong Kok area for your special celebration! I'll avoid seafood and spicy options."}}"""

    if AI_SERVICE == 'ollama':
        result = analyze_with_ollama(prompt)
    elif AI_SERVICE == 'openrouter':
        result = analyze_with_openrouter(prompt)
    elif AI_SERVICE == 'openai':
        result = analyze_with_openai(prompt)
    else:
        result = None
    
    if result:
        print(f"🤖 AI Raw Response: {result[:200]}...")  # Debug: Show first 200 chars
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                print(f"✅ AI Parsed Analysis: {parsed}")  # Debug: Show parsed result
                # Ensure ai_message exists
                if 'ai_message' not in parsed:
                    parsed['ai_message'] = ''
                return parsed
        except Exception as e:
            print(f"❌ AI Parsing Error: {e}")  # Debug: Show parsing error
            pass
    else:
        print("⚠️ AI returned no result")  # Debug: No AI response
    
    # Fallback to basic analysis
    print("⚠️ Using fallback analysis")  # Debug: Using fallback
    return {
        "cuisine_types": [],
        "atmosphere": "casual",
        "key_requirements": [],
        "dietary_restrictions": [],
        "ai_message": ""
    }

def get_cuisine_keywords(cuisine_query):
    """Extract all possible keywords for a cuisine type"""
    query_lower = cuisine_query.lower().strip()
    keywords = [query_lower]
    
    # Common cuisine mappings
    cuisine_map = {
        'italian': ['italian', 'italy', 'pasta', 'pizza', 'risotto', 'trattoria', 'osteria', '意大利'],
        'japanese': ['japanese', 'japan', 'sushi', 'ramen', 'izakaya', 'tempura', 'sashimi', 'udon', 'yakitori', '日本'],
        'chinese': ['chinese', 'china', 'cantonese', 'sichuan', 'dim sum', 'dumpling', 'noodle', '中菜', '中國'],
        'french': ['french', 'france', 'bistro', 'brasserie', 'croissant', '法國'],
        'korean': ['korean', 'korea', 'bbq', 'kimchi', 'bibimbap', '韓國'],
        'thai': ['thai', 'thailand', 'pad thai', 'tom yum', '泰國'],
        'vietnamese': ['vietnamese', 'vietnam', 'pho', 'banh mi', '越南'],
        'indian': ['indian', 'india', 'curry', 'tandoori', 'naan', '印度'],
        'mexican': ['mexican', 'mexico', 'taco', 'burrito', 'nacho', '墨西哥'],
        'american': ['american', 'burger', 'steak', 'bbq', 'diner', '美國'],
        'spanish': ['spanish', 'spain', 'tapas', 'paella', '西班牙'],
        'greek': ['greek', 'greece', 'gyro', 'souvlaki', '希臘'],
        'turkish': ['turkish', 'turkey', 'kebab', '土耳其'],
        'middle eastern': ['middle eastern', 'lebanese', 'falafel', 'hummus', 'shawarma'],
        'bar': ['bar', 'pub', 'tavern', 'wine bar', 'cocktail', 'lounge', 'brewery', '酒吧', 'wine', 'beer'],
        'cafe': ['cafe', 'coffee', 'bakery', 'dessert', 'patisserie', '咖啡', '茶餐廳'],
        'seafood': ['seafood', 'fish', 'oyster', 'lobster', 'crab', 'prawn', '海鮮'],
        'steak': ['steak', 'steakhouse', 'beef', 'grill', '牛扒'],
        'vegetarian': ['vegetarian', 'vegan', 'plant-based', 'veggie', '素食'],
        'asian': ['asian', 'pan-asian', 'fusion'],
        'european': ['european', 'continental'],
        'international': ['international', 'fusion', 'contemporary'],
        'buffet': ['buffet', 'all you can eat', '自助餐'],
        'hotpot': ['hotpot', 'hot pot', 'steamboat', '火鍋'],
        'bbq': ['bbq', 'barbecue', 'grill', 'yakiniku', '燒烤'],
        'noodles': ['noodles', 'ramen', 'udon', 'pho', '麵'],
        'dim sum': ['dim sum', 'yum cha', '點心', '飲茶'],
    }
    
    # Check if query matches any cuisine category
    for cuisine_type, aliases in cuisine_map.items():
        if query_lower in aliases or any(alias in query_lower for alias in aliases):
            keywords.extend(aliases)
            break
    
    # Also add the original query split by spaces
    keywords.extend(query_lower.split())
    
    # Remove duplicates and short words
    return list(set([k for k in keywords if len(k) >= 3]))

def calculate_match_score(restaurant, analysis, user_input, debug=False):
    """Calculate how well a restaurant matches user preferences"""
    score = 0
    reasons = []
    lang = user_input.get('lang', 'zh')
    
    if debug:
        print(f"\n🔍 DEBUG Scoring: {restaurant.get('name_en', 'N/A')}")
        print(f"   Cuisine: {restaurant.get('cuisine_en', 'N/A')}")
        print(f"   District: {restaurant.get('district_en', 'N/A')}")
        print(f"   Price: {restaurant.get('price', 'N/A')}")
        print(f"   Analysis cuisines: {analysis.get('cuisine_types', [])}")
    
    # Budget matching (40 points) - Strict exact match only
    budget_map = {
        "Below $50": 1,
        "$51-100": 2,
        "$101-200": 3,
        "$201-400": 4,
        "$401-800": 5,
        "Above $800": 6
    }
    
    user_budget = user_input['budget']
    rest_budget = restaurant.get('price', '')
    
    if user_budget == 'Any':
        # If user doesn't care about budget, give small bonus
        score += 5
    elif user_budget == rest_budget:
        score += 40
        if lang == 'zh':
            reasons.append(f"預算完美配對 ({user_budget})")
        else:
            reasons.append(f"Perfect budget match ({user_budget})")
    elif user_budget in budget_map and rest_budget in budget_map:
        diff = abs(budget_map[user_budget] - budget_map[rest_budget])
        if diff == 1:
            score += 15
            if lang == 'zh':
                reasons.append("預算接近")
            else:
                reasons.append("Close budget match")
        else:
            # Penalize restaurants outside budget range
            score -= 15
    
    # District matching (40 points) - Strict requirement
    if user_input['district'] and user_input['district'] != 'Any':
        district_match = False
        # Check both English and Chinese district names
        if (restaurant.get('district_en', '').lower() == user_input['district'].lower() or
            restaurant.get('district_zh', '') == user_input['district']):
            score += 40
            district_name = restaurant.get('district_zh' if lang == 'zh' else 'district_en', user_input['district'])
            if lang == 'zh':
                reasons.append(f"位於{district_name}")
            else:
                reasons.append(f"Located in {district_name}")
            district_match = True
        
        # Heavy penalty for wrong district when user specified one
        if not district_match:
            score -= 20
    
    # Cuisine matching (40 points) - Semantic matching with special handling
    if analysis['cuisine_types']:
        rest_cuisine_en = restaurant.get('cuisine_en', '').lower()
        rest_cuisine_zh = restaurant.get('cuisine_zh', '').lower()
        cuisine_matched = False
        is_fine_dining_query = False
        
        if debug:
            print(f"   Checking cuisines: {analysis['cuisine_types']}")
            print(f"   Restaurant cuisine_en: '{rest_cuisine_en}'")
            print(f"   Restaurant cuisine_zh: '{rest_cuisine_zh}'")
        
        # Fine dining upscale cuisines (typically associated with fine dining)
        fine_dining_cuisines = ['french', 'italian', 'japanese', 'european', 'contemporary', 
                                'modern', 'fusion', 'international', 'steakhouse', 'seafood']
        
        for cuisine in analysis['cuisine_types']:
            cuisine_lower = cuisine.lower().strip()
            
            # Special handling for "fine dining" - it's a style, not a cuisine
            if cuisine_lower in ['fine dining', 'fine-dining', 'fine_dining', 'upscale', 'high-end']:
                is_fine_dining_query = True
                # Match any upscale cuisine + require higher price tier
                if any(fd_cuisine in rest_cuisine_en for fd_cuisine in fine_dining_cuisines):
                    # Check if price is appropriate for fine dining
                    if rest_budget in ['$201-400', '$401-800', 'Above $800']:
                        score += 40
                        if lang == 'zh':
                            reasons.append(f"符合fine dining菜系")
                        else:
                            reasons.append(f"Matches fine dining cuisine")
                        cuisine_matched = True
                        if debug:
                            print(f"   ✓ Matched fine dining: {rest_cuisine_en} in price tier {rest_budget}")
                        break
                    elif rest_budget == '$101-200':
                        # Mid-tier, partial match
                        score += 20
                        cuisine_matched = True
                        if debug:
                            print(f"   ~ Partial fine dining match: {rest_cuisine_en}")
                        break
                continue
            
            # Regular cuisine matching - use dynamic keywords
            search_terms = get_cuisine_keywords(cuisine_lower)
            
            if debug:
                print(f"   Search terms for '{cuisine}': {search_terms[:5]}...")  # Show first 5
            
            # Get restaurant name and description for extended search
            rest_name_en = restaurant.get('name_en', '').lower()
            rest_name_zh = restaurant.get('name_zh', '').lower()
            rest_desc_en = restaurant.get('description_en', '').lower()
            rest_desc_zh = restaurant.get('description_zh', '').lower()
            
            # Check if any search term matches restaurant cuisine, name, or description
            for term in search_terms:
                match_score = 0
                match_location = ""
                
                # Primary match: cuisine field (full points)
                if term in rest_cuisine_en or term in rest_cuisine_zh:
                    if len(term) >= 4 or term == rest_cuisine_en or term == rest_cuisine_zh:
                        match_score = 40
                        match_location = "cuisine"
                
                # Secondary match: restaurant name (good match)
                elif term in rest_name_en or term in rest_name_zh:
                    if len(term) >= 3:
                        match_score = 35
                        match_location = "name"
                
                # Tertiary match: description (partial match)
                elif term in rest_desc_en or term in rest_desc_zh:
                    if len(term) >= 4:
                        match_score = 30
                        match_location = "description"
                
                if match_score > 0:
                    score += match_score
                    if lang == 'zh':
                        reasons.append(f"符合{cuisine}菜系")
                    else:
                        reasons.append(f"Matches {cuisine} cuisine")
                    cuisine_matched = True
                    if debug:
                        print(f"   ✓ Matched cuisine: {cuisine} via term '{term}' in {match_location} (score: {match_score})")
                    break
            
            if cuisine_matched:
                break
        
        # Penalty for no match (but lighter for fine dining since it's style-based)
        if not cuisine_matched and analysis['cuisine_types']:
            penalty = -10 if is_fine_dining_query else -20
            score += penalty
            if debug:
                print(f"   ✗ No cuisine match, {penalty} points")
    
    # Dietary restrictions / Negative prompts (heavy penalty for matches)
    if analysis.get('dietary_restrictions'):
        for restriction in analysis['dietary_restrictions']:
            restriction_lower = restriction.lower().strip()
            
            # Expand restriction keywords
            restriction_keywords = get_cuisine_keywords(restriction_lower)
            
            if debug:
                print(f"   Checking restriction: {restriction} → {restriction_keywords[:3]}...")
            
            # Check if restaurant matches any restriction (bad!)
            for keyword in restriction_keywords:
                if len(keyword) < 3:
                    continue
                    
                # Check in cuisine, name, description, and dishes
                if (keyword in rest_cuisine_en or keyword in rest_cuisine_zh or
                    keyword in rest_name_en or keyword in rest_name_zh or
                    keyword in rest_desc_en or keyword in rest_desc_zh or
                    keyword in restaurant.get('popular_dishes_en', '').lower() or
                    keyword in restaurant.get('popular_dishes_zh', '').lower()):
                    
                    # Heavy penalty for matching a restriction
                    score -= 50
                    if lang == 'zh':
                        reasons.append(f"⚠️ 包含不想要的：{restriction}")
                    else:
                        reasons.append(f"⚠️ Contains unwanted: {restriction}")
                    
                    if debug:
                        print(f"   ✗ RESTRICTION MATCH: {restriction} via '{keyword}' (-50 points)")
                    break
    
    # Rating score (20 points) - Quality indicator
    smile = int(restaurant.get('rating_smile', 0) or 0)
    ok = int(restaurant.get('rating_ok', 0) or 0)
    cry = int(restaurant.get('rating_cry', 0) or 0)
    total_ratings = smile + ok + cry
    
    if total_ratings >= 20:  # Require meaningful number of ratings
        rating_ratio = smile / total_ratings
        if rating_ratio >= 0.75:
            score += 20
            if lang == 'zh':
                reasons.append("顧客評價極高")
            else:
                reasons.append("Highly rated by customers")
        elif rating_ratio >= 0.6:
            score += 12
            if lang == 'zh':
                reasons.append("顧客評價良好")
            else:
                reasons.append("Well rated by customers")
        elif rating_ratio >= 0.5:
            score += 5
        elif rating_ratio < 0.4:
            score -= 10  # Penalty for poor ratings
    elif total_ratings >= 10:
        # Moderate number of ratings
        rating_ratio = smile / total_ratings
        if rating_ratio >= 0.75:
            score += 10
        elif rating_ratio >= 0.6:
            score += 5
        elif rating_ratio < 0.4:
            score -= 5
    
    # Description/atmosphere bonus (10 points)
    if analysis.get('atmosphere') and restaurant.get('description_en'):
        description = restaurant.get('description_en', '').lower()
        atmosphere = analysis['atmosphere'].lower()
        if atmosphere in description:
            score += 10
            if lang == 'zh':
                reasons.append(f"符合{atmosphere}氛圍")
            else:
                reasons.append(f"Matches {atmosphere} atmosphere")
    
    return score, reasons

def generate_welcome_message(lang='zh'):
    """Generate welcome message with helpful hints"""
    if lang == 'zh':
        return """嘿！我係你嘅 AI 美食專家 👋 講俾我知你想食咩，我幫你搵最啱嘅餐廳！
        
<div style="margin-top: 15px; padding: 15px; background: #f0f7f0; border-radius: 10px; font-size: 0.9rem;">
    <strong>💡 點樣搵到最啱嘅餐廳？</strong><br><br>
    
    <strong>✅ 講你想要嘅：</strong><br>
    • "想食浪漫啲嘅意大利餐，中環附近"<br>
    • "想食高質嘅日本菜，慶祝生日，預算$300左右"<br>
    • "想搵間bar飲嘢，旺角附近"<br><br>
    
    <strong>🚫 講你唔想要嘅：</strong><br>
    • "想食火鍋，但<strong>唔要辣</strong>"<br>
    • "想食日本菜，<strong>避免海鮮</strong>"<br>
    • "想食西餐，<strong>no pork</strong>"<br><br>
    
    <strong>🔄 改變主意？</strong><br>
    • "旺角有冇？" → 自動保留之前嘅菜系<br>
    • "改去尖沙咀" → 轉地區，菜系不變<br><br>
    
    隨便講，我會明白你想要咩！😊
</div>"""
    else:
        return """Hey there! I'm your AI foodie buddy 👋 Just tell me what you're craving, and I'll find the perfect spot for you!
        
<div style="margin-top: 15px; padding: 15px; background: #f0f7f0; border-radius: 10px; font-size: 0.9rem;">
    <strong>💡 How to find your perfect restaurant?</strong><br><br>
    
    <strong>✅ Tell me what you want:</strong><br>
    • "Romantic Italian dinner in Central"<br>
    • "High-end Japanese for birthday, budget around $300"<br>
    • "Bar for drinks in Mong Kok"<br><br>
    
    <strong>🚫 Tell me what you DON'T want:</strong><br>
    • "Hotpot but <strong>no spicy</strong>"<br>
    • "Japanese food, <strong>avoid seafood</strong>"<br>
    • "Western food, <strong>no pork</strong>"<br><br>
    
    <strong>🔄 Change your mind?</strong><br>
    • "How about Mong Kok?" → Keeps same cuisine<br>
    • "Change to Tsim Sha Tsui" → Changes location only<br><br>
    
    Just chat naturally, I'll understand! 😊
</div>"""

@app.route('/')
def index():
    """Render the main page"""
    lang = request.args.get('lang', 'zh')
    
    # Generate AI welcome message
    welcome_message = generate_welcome_message(lang)
    
    # Get unique districts and cuisines for filters
    districts_en = sorted(list(set([r.get('district_en', '') for r in restaurants if r.get('district_en')])))
    districts_zh = sorted(list(set([r.get('district_zh', '') for r in restaurants if r.get('district_zh')])))
    cuisines_en = sorted(list(set([r.get('cuisine_en', '') for r in restaurants if r.get('cuisine_en')])))
    cuisines_zh = sorted(list(set([r.get('cuisine_zh', '') for r in restaurants if r.get('cuisine_zh')])))
    
    return render_template('index.html', 
                         lang=lang,
                         welcome_message=welcome_message,
                         districts_en=districts_en, 
                         districts_zh=districts_zh,
                         cuisines_en=cuisines_en,
                         cuisines_zh=cuisines_zh)

@app.route('/recommend', methods=['POST'])
def recommend():
    """Get restaurant recommendations based on user preferences"""
    try:
        request_data = request.json
        print(f"\n🔍 Raw request keys: {list(request_data.keys())}")
        
        user_input = {
            'preferences': request_data.get('preferences', ''),
            'budget': request_data.get('budget', 'Any'),
            'district': request_data.get('district', 'Any'),
            'lang': request_data.get('lang', 'zh'),
            'conversation_history': request_data.get('conversation_history', [])
        }
        
        print(f"\n{'='*60}")
        print(f" User Request:")
        print(f"   Preferences: {user_input['preferences']}")
        print(f"   Budget: {user_input['budget']}")
        print(f"   District: {user_input['district']}")
        print(f"   Language: {user_input['lang']}")
        print(f"   Conv history: {len(user_input.get('conversation_history', []))} items")
        print(f"{'='*60}\n")
        
        # Analyze user preferences with AI
        analysis = analyze_preferences(user_input)
        print(f" Final Analysis: {analysis}\n")
        
        # Override budget and district if AI extracted them from natural language
        extracted_budget = analysis.get('extracted_budget')
        if extracted_budget and extracted_budget not in ['null', 'None', None]:
            user_input['budget'] = extracted_budget
            print(f"✅ Extracted budget from message: {extracted_budget}")
        
        extracted_district = analysis.get('extracted_district')
        if extracted_district and extracted_district not in ['null', 'None', None]:
            user_input['district'] = extracted_district
            print(f"✅ Extracted district from message: {extracted_district}")
        
        print(f"📍 Final search params: Budget={user_input['budget']}, District={user_input['district']}")
        print()
        
        # Score all restaurants (using cached list for now, can optimize with SQL later)
        scored_restaurants = []
        debug_count = 0
        skipped_count = 0
        
        print(f"🔍 Scoring {len(restaurants)} restaurants...")
        
        for idx, restaurant in enumerate(restaurants):
            # Skip restaurants with missing critical data
            if not restaurant.get('name_en') or not restaurant.get('cuisine_en'):
                skipped_count += 1
                continue
            
            # Debug first 3 restaurants
            debug_this = (idx < 3)
            score, reasons = calculate_match_score(restaurant, analysis, user_input, debug=debug_this)
            
            # Debug first valid restaurant
            if idx == 0:
                print(f"🔍 First restaurant being scored:")
                print(f"   Restaurant object type: {type(restaurant)}")
                print(f"   Restaurant keys: {list(restaurant.keys())[:10] if isinstance(restaurant, dict) else 'NOT A DICT'}")
                print(f"   name_en: {restaurant.get('name_en', 'MISSING') if isinstance(restaurant, dict) else 'N/A'}")
                print(f"   Score: {score}")
                print()
            
            # Only include restaurants with meaningful positive scores
            if score >= 30:  # Require at least one match criterion
                scored_restaurants.append({
                    'restaurant': restaurant,
                    'score': score,
                    'reasons': reasons
                })
                debug_count += 1
                if debug_count <= 5:
                    print(f"✓ Restaurant #{debug_count} scored {score}: {restaurant.get('name_en', 'N/A')} - {restaurant.get('cuisine_en', 'N/A')}")
        
        print(f"⚠️ Skipped {skipped_count} restaurants with missing data")
        
        # Sort by score and get top 10
        scored_restaurants.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = scored_restaurants[:10]
        
        print(f"\n🎯 Scoring Results:")
        print(f"   Total scored: {len(scored_restaurants)}")
        print(f"   Top 10 scores: {[item['score'] for item in top_recommendations]}")
        if top_recommendations:
            top_rest = top_recommendations[0]['restaurant']
            print(f"   Top match restaurant object type: {type(top_rest)}")
            print(f"   Top match keys: {list(top_rest.keys())[:10] if isinstance(top_rest, dict) else 'NOT A DICT'}")
            print(f"   Top match name_en value: '{top_rest.get('name_en', 'MISSING')}'")
            print(f"   Top match name_en type: {type(top_rest.get('name_en'))}")
            print(f"   Top match: {top_rest.get('name_en', 'N/A')} (Score: {top_recommendations[0]['score']})")
        print()
        
        # Format recommendations
        recommendations = []
        print(f"\n📦 Formatting {len(top_recommendations)} recommendations...")
        
        for idx, item in enumerate(top_recommendations):
            rest = item['restaurant']
            
            if idx == 0:
                print(f"\n🔍 Formatting first restaurant:")
                print(f"   rest type: {type(rest)}")
                print(f"   rest.get('name_en'): '{rest.get('name_en', 'MISSING')}'")
                print(f"   rest['name_en'] direct: '{rest['name_en'] if 'name_en' in rest else 'KEY NOT FOUND'}'")
            
            formatted = {
                'name_en': rest.get('name_en', ''),
                'name_zh': rest.get('name_zh', ''),
                'cuisine_en': rest.get('cuisine_en', ''),
                'cuisine_zh': rest.get('cuisine_zh', ''),
                'district_en': rest.get('district_en', ''),
                'district_zh': rest.get('district_zh', ''),
                'address_en': rest.get('address_en', ''),
                'address_zh': rest.get('address_zh', ''),
                'price': rest.get('price', ''),
                'phone': rest.get('phone', ''),
                'opening_hours_en': rest.get('opening_hours_en', ''),
                'opening_hours_zh': rest.get('opening_hours_zh', ''),
                'description_en': rest.get('description_en', ''),
                'description_zh': rest.get('description_zh', ''),
                'popular_dishes_en': rest.get('popular_dishes_en', ''),
                'popular_dishes_zh': rest.get('popular_dishes_zh', ''),
                'rating_smile': rest.get('rating_smile', '0'),
                'rating_ok': rest.get('rating_ok', '0'),
                'rating_cry': rest.get('rating_cry', '0'),
                'url': rest.get('url', ''),
                'match_score': item['score'],
                'match_reasons': item['reasons']  # Include reasons for display
            }
            
            if idx == 0:
                print(f"\n📋 Formatted Restaurant Data (#{idx+1}):")
                print(f"   Name: '{formatted['name_en']}' / '{formatted['name_zh']}'")
                print(f"   Cuisine: '{formatted['cuisine_en']}'")
                print(f"   District: '{formatted['district_en']}'")
                print(f"   Price: '{formatted['price']}'")
                print(f"   Ratings: 😊{formatted['rating_smile']} 😐{formatted['rating_ok']} 😢{formatted['rating_cry']}")
            
            recommendations.append(formatted)
        
        print(f"✅ Returning {len(recommendations)} recommendations\n")
        print(f"{'='*60}\n")
        
        # Log search to history
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO search_history (preferences, cuisine, district, budget, results_count, language, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_input['preferences'],
                ', '.join(analysis.get('cuisine_types', [])) if analysis.get('cuisine_types') else None,
                user_input['district'],
                user_input['budget'],
                len(recommendations),
                user_input['lang'],
                session.get('session_id', 'anonymous')
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging search history: {e}")
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'analysis': analysis,
            'total_matches': len(scored_restaurants)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    ai_status = "Unknown"
    
    if AI_SERVICE == 'ollama':
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            ai_status = "Connected" if response.status_code == 200 else "Disconnected"
        except:
            ai_status = "Disconnected"
    elif AI_SERVICE == 'openrouter':
        ai_status = "OpenRouter" if OPENROUTER_API_KEY else "Not Configured"
    elif AI_SERVICE == 'openai':
        ai_status = "OpenAI" if OPENAI_API_KEY else "Not Configured"
    else:
        ai_status = "Unknown Service"
    
    return jsonify({
        'status': 'healthy',
        'ai_service': AI_SERVICE,
        'ai_status': ai_status,
        'restaurants_loaded': len(restaurants)
    })

# ============================================================================
# ADMIN PANEL ROUTES
# ============================================================================

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    lang = request.args.get('lang', 'zh')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use proper password hashing)
        ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
        ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard', lang=lang))
        else:
            error_msg = '用戶名或密碼錯誤' if lang == 'zh' else 'Invalid username or password'
            return render_template('admin_login.html', error=error_msg, lang=lang)
    
    return render_template('admin_login.html', lang=lang)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    lang = request.args.get('lang', 'zh')
    return render_template('admin.html', lang=lang)

@app.route('/admin/api/stats')
@admin_required
def admin_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total restaurants
        cursor.execute('SELECT COUNT(*) as count FROM restaurants')
        total_restaurants = cursor.fetchone()['count']
        
        # Total districts
        cursor.execute('SELECT COUNT(DISTINCT district_en) as count FROM restaurants WHERE district_en IS NOT NULL')
        total_districts = cursor.fetchone()['count']
        
        # Total cuisines
        cursor.execute('SELECT COUNT(DISTINCT cuisine_en) as count FROM restaurants WHERE cuisine_en IS NOT NULL')
        total_cuisines = cursor.fetchone()['count']
        
        # Average rating
        cursor.execute('''
            SELECT 
                SUM(CAST(rating_smile AS INTEGER)) as total_smile,
                SUM(CAST(rating_ok AS INTEGER)) as total_ok,
                SUM(CAST(rating_cry AS INTEGER)) as total_cry
            FROM restaurants
        ''')
        ratings = cursor.fetchone()
        total_ratings = (ratings['total_smile'] or 0) + (ratings['total_ok'] or 0) + (ratings['total_cry'] or 0)
        avg_rating = round((ratings['total_smile'] or 0) / total_ratings * 100) if total_ratings > 0 else 0
        
        # Most popular cuisine
        cursor.execute('''
            SELECT cuisine_en, COUNT(*) as count 
            FROM restaurants 
            WHERE cuisine_en IS NOT NULL 
            GROUP BY cuisine_en 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        popular_cuisine_row = cursor.fetchone()
        popular_cuisine = popular_cuisine_row['cuisine_en'] if popular_cuisine_row else 'N/A'
        
        # Most popular district
        cursor.execute('''
            SELECT district_en, COUNT(*) as count 
            FROM restaurants 
            WHERE district_en IS NOT NULL 
            GROUP BY district_en 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        popular_district_row = cursor.fetchone()
        popular_district = popular_district_row['district_en'] if popular_district_row else 'N/A'
        
        # Price distribution
        cursor.execute('''
            SELECT price, COUNT(*) as count 
            FROM restaurants 
            WHERE price IS NOT NULL 
            GROUP BY price 
            ORDER BY 
                CASE price
                    WHEN 'Below $50' THEN 1
                    WHEN '$51-100' THEN 2
                    WHEN '$101-200' THEN 3
                    WHEN '$201-400' THEN 4
                    WHEN '$401-800' THEN 5
                    WHEN 'Above $800' THEN 6
                    ELSE 7
                END
        ''')
        price_dist = {row['price']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            'total_restaurants': total_restaurants,
            'total_districts': total_districts,
            'total_cuisines': total_cuisines,
            'avg_rating': avg_rating,
            'popular_cuisine': popular_cuisine,
            'popular_district': popular_district,
            'price_distribution': price_dist
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/restaurants')
@admin_required
def admin_get_restaurants():
    """Get all restaurants for admin panel"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM restaurants ORDER BY name_en')
        rows = cursor.fetchall()
        conn.close()
        
        restaurants_list = [dict(row) for row in rows]
        return jsonify({'restaurants': restaurants_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/restaurants/<int:restaurant_id>')
@admin_required
def admin_get_restaurant(restaurant_id):
    """Get single restaurant"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify(dict(row))
        else:
            return jsonify({'error': 'Restaurant not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/restaurants', methods=['POST'])
@admin_required
def admin_add_restaurant():
    """Add new restaurant"""
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO restaurants (
                name_en, name_zh, address_en, address_zh, district_en, district_zh,
                cuisine_en, cuisine_zh, price, phone, opening_hours_en, opening_hours_zh,
                rating_smile, rating_ok, rating_cry, description_en, description_zh,
                popular_dishes_en, popular_dishes_zh, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name_en'), data.get('name_zh'), data.get('address_en'), data.get('address_zh'),
            data.get('district_en'), data.get('district_zh'), data.get('cuisine_en'), data.get('cuisine_zh'),
            data.get('price'), data.get('phone'), data.get('opening_hours_en'), data.get('opening_hours_zh'),
            0, 0, 0,  # Default ratings
            data.get('description_en'), data.get('description_zh'),
            data.get('popular_dishes_en'), data.get('popular_dishes_zh'), data.get('url')
        ))
        
        conn.commit()
        restaurant_id = cursor.lastrowid
        conn.close()
        
        # Reload restaurants in memory
        global restaurants
        restaurants = load_restaurants()
        
        return jsonify({'success': True, 'id': restaurant_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/restaurants/<int:restaurant_id>', methods=['PUT'])
@admin_required
def admin_update_restaurant(restaurant_id):
    """Update restaurant"""
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE restaurants SET
                name_en = ?, name_zh = ?, address_en = ?, address_zh = ?,
                district_en = ?, district_zh = ?, cuisine_en = ?, cuisine_zh = ?,
                price = ?, phone = ?, opening_hours_en = ?, opening_hours_zh = ?,
                description_en = ?, description_zh = ?, popular_dishes_en = ?,
                popular_dishes_zh = ?, url = ?
            WHERE id = ?
        ''', (
            data.get('name_en'), data.get('name_zh'), data.get('address_en'), data.get('address_zh'),
            data.get('district_en'), data.get('district_zh'), data.get('cuisine_en'), data.get('cuisine_zh'),
            data.get('price'), data.get('phone'), data.get('opening_hours_en'), data.get('opening_hours_zh'),
            data.get('description_en'), data.get('description_zh'), data.get('popular_dishes_en'),
            data.get('popular_dishes_zh'), data.get('url'), restaurant_id
        ))
        
        conn.commit()
        conn.close()
        
        # Reload restaurants in memory
        global restaurants
        restaurants = load_restaurants()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/restaurants/<int:restaurant_id>', methods=['DELETE'])
@admin_required
def admin_delete_restaurant(restaurant_id):
    """Delete restaurant"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM restaurants WHERE id = ?', (restaurant_id,))
        conn.commit()
        conn.close()
        
        # Reload restaurants in memory
        global restaurants
        restaurants = load_restaurants()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/settings', methods=['GET'])
@admin_required
def admin_get_settings():
    """Get current settings from .env file"""
    try:
        settings = {
            'ai_service': os.getenv('AI_SERVICE', 'ollama'),
            'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            'ollama_model': os.getenv('OLLAMA_MODEL', 'llama3.2'),
            'openrouter_key': os.getenv('OPENROUTER_API_KEY', ''),
            'openai_key': os.getenv('OPENAI_API_KEY', ''),
            'openai_model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            'admin_username': os.getenv('ADMIN_USERNAME', 'admin')
        }
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/settings', methods=['POST'])
@admin_required
def admin_save_settings():
    """Save settings to .env file"""
    try:
        data = request.json
        env_path = '.env'
        
        # Read current .env file
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # Update settings
        env_vars['AI_SERVICE'] = data.get('ai_service', 'ollama')
        env_vars['OLLAMA_URL'] = data.get('ollama_url', 'http://localhost:11434')
        env_vars['OLLAMA_MODEL'] = data.get('ollama_model', 'llama3.2')
        
        if data.get('openrouter_key'):
            env_vars['OPENROUTER_API_KEY'] = data.get('openrouter_key')
        
        if data.get('openai_key'):
            env_vars['OPENAI_API_KEY'] = data.get('openai_key')
        
        env_vars['OPENAI_MODEL'] = data.get('openai_model', 'gpt-4o-mini')
        
        if data.get('admin_username'):
            env_vars['ADMIN_USERNAME'] = data.get('admin_username')
        
        if data.get('admin_password'):
            env_vars['ADMIN_PASSWORD'] = data.get('admin_password')
        
        # Write back to .env file
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('# AI Service Configuration\n')
            f.write('# Choose \'ollama\' for local AI, \'openrouter\' for cloud AI, or \'openai\' for OpenAI\n')
            f.write(f'AI_SERVICE={env_vars.get("AI_SERVICE", "ollama")}\n\n')
            
            f.write('# Ollama Configuration (for local AI)\n')
            f.write(f'OLLAMA_URL={env_vars.get("OLLAMA_URL", "http://localhost:11434")}\n')
            f.write(f'OLLAMA_MODEL={env_vars.get("OLLAMA_MODEL", "llama3.2")}\n\n')
            
            f.write('# OpenRouter Configuration (for cloud AI)\n')
            f.write('# Get your API key from https://openrouter.ai/\n')
            f.write(f'OPENROUTER_API_KEY={env_vars.get("OPENROUTER_API_KEY", "")}\n\n')
            
            f.write('# OpenAI Configuration\n')
            f.write('# Get your API key from https://platform.openai.com/api-keys\n')
            f.write(f'OPENAI_API_KEY={env_vars.get("OPENAI_API_KEY", "")}\n')
            f.write(f'OPENAI_MODEL={env_vars.get("OPENAI_MODEL", "gpt-4o-mini")}\n\n')
            
            f.write('# Admin Panel Configuration\n')
            f.write(f'ADMIN_USERNAME={env_vars.get("ADMIN_USERNAME", "admin")}\n')
            f.write(f'ADMIN_PASSWORD={env_vars.get("ADMIN_PASSWORD", "admin123")}\n')
            f.write(f'SECRET_KEY={env_vars.get("SECRET_KEY", "your-secret-key-change-this-in-production")}\n')
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Update global variables
        global AI_SERVICE, OLLAMA_URL, OLLAMA_MODEL, OPENROUTER_API_KEY, OPENAI_API_KEY, OPENAI_MODEL
        AI_SERVICE = os.getenv('AI_SERVICE', 'ollama')
        OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
        OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/analytics')
@admin_required
def admin_analytics():
    """Get analytics data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total searches
        cursor.execute('SELECT COUNT(*) as count FROM search_history')
        total_searches = cursor.fetchone()['count']
        
        # Unique users (sessions)
        cursor.execute('SELECT COUNT(DISTINCT session_id) as count FROM search_history')
        unique_users = cursor.fetchone()['count']
        
        # Popular cuisine
        cursor.execute('''
            SELECT cuisine, COUNT(*) as count 
            FROM search_history 
            WHERE cuisine IS NOT NULL AND cuisine != ''
            GROUP BY cuisine 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        popular_cuisine_row = cursor.fetchone()
        popular_cuisine = popular_cuisine_row['cuisine'] if popular_cuisine_row else 'N/A'
        
        # Popular district
        cursor.execute('''
            SELECT district, COUNT(*) as count 
            FROM search_history 
            WHERE district IS NOT NULL AND district != '' AND district != 'Any'
            GROUP BY district 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        popular_district_row = cursor.fetchone()
        popular_district = popular_district_row['district'] if popular_district_row else 'N/A'
        
        # Cuisine stats
        cursor.execute('''
            SELECT cuisine, COUNT(*) as count 
            FROM search_history 
            WHERE cuisine IS NOT NULL AND cuisine != ''
            GROUP BY cuisine 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        cuisine_stats = {row['cuisine']: row['count'] for row in cursor.fetchall()}
        
        # District stats
        cursor.execute('''
            SELECT district, COUNT(*) as count 
            FROM search_history 
            WHERE district IS NOT NULL AND district != '' AND district != 'Any'
            GROUP BY district 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        district_stats = {row['district']: row['count'] for row in cursor.fetchall()}
        
        # Budget stats
        cursor.execute('''
            SELECT budget, COUNT(*) as count 
            FROM search_history 
            WHERE budget IS NOT NULL AND budget != '' AND budget != 'Any'
            GROUP BY budget 
            ORDER BY 
                CASE budget
                    WHEN 'Below $50' THEN 1
                    WHEN '$51-100' THEN 2
                    WHEN '$101-200' THEN 3
                    WHEN '$201-400' THEN 4
                    WHEN '$401-800' THEN 5
                    WHEN 'Above $800' THEN 6
                    ELSE 7
                END
        ''')
        budget_stats = {row['budget']: row['count'] for row in cursor.fetchall()}
        
        # Trend data (last 7 days)
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count 
            FROM search_history 
            WHERE timestamp >= DATE('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''')
        trend_data = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_searches': total_searches,
            'unique_users': unique_users,
            'popular_cuisine': popular_cuisine,
            'popular_district': popular_district,
            'cuisine_stats': cuisine_stats,
            'district_stats': district_stats,
            'budget_stats': budget_stats,
            'trend_data': trend_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/search-history')
@admin_required
def admin_search_history():
    """Get search history with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 50
        filter_type = request.args.get('filter', 'all')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build WHERE clause based on filter
        where_clause = ''
        if filter_type == 'today':
            where_clause = "WHERE DATE(timestamp) = DATE('now')"
        elif filter_type == 'week':
            where_clause = "WHERE timestamp >= DATE('now', '-7 days')"
        elif filter_type == 'month':
            where_clause = "WHERE timestamp >= DATE('now', '-30 days')"
        
        # Get total count
        cursor.execute(f'SELECT COUNT(*) as count FROM search_history {where_clause}')
        total_count = cursor.fetchone()['count']
        total_pages = (total_count + per_page - 1) // per_page
        
        # Get paginated data
        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT * FROM search_history 
            {where_clause}
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'history': history,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/search-history', methods=['DELETE'])
@admin_required
def admin_clear_search_history():
    """Clear all search history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_history')
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# END ADMIN PANEL ROUTES
# ============================================================================

if __name__ == '__main__':
    print(f"🍽️  AIEat - Hong Kong Restaurant Recommendation System")
    print(f"📊 Loaded {len(restaurants)} restaurants")
    print(f"🤖 AI Service: {AI_SERVICE}")
    print(f"🌐 Starting server on http://localhost:5000")
    print(f"🔐 Admin panel: http://localhost:5000/admin")
    app.run(debug=True, host='0.0.0.0', port=5000)
