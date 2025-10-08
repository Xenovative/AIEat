# 🍽️ AIEat - AI Hong Kong Restaurant Recommendation System

An intelligent restaurant recommendation system for Hong Kong that uses AI to match users with the perfect dining experience based on their preferences, budget, and location.

## ✨ Features

- 🤖 **AI-Powered Analysis**: Supports Ollama (local LLM), OpenRouter, and OpenAI for intelligent preference analysis
- 🎯 **Smart Matching**: Matches restaurants based on cuisine type, budget, location, and user preferences
- 🌏 **Hong Kong Focus**: Comprehensive database of Hong Kong restaurants from OpenRice
- 🌐 **Bilingual Interface**: Full support for English and Traditional Chinese (繁體中文)
- 📱 **Responsive Design**: Beautiful, modern UI that works on desktop and mobile
- ⭐ **Rating Integration**: Shows customer ratings (smile/ok/cry) from OpenRice
- 🔒 **Privacy First**: Option to run completely locally with Ollama
- 🛠️ **Admin Panel**: Full-featured admin dashboard for managing restaurants

## 🎯 System Requirements

- Python 3.8+
- AI Service (choose one):
  - **Ollama** (local LLM service) - Recommended for privacy
  - **OpenRouter API** key (cloud AI service) - Free tier available
  - **OpenAI API** key (cloud AI service) - High quality results
- Modern web browser

## 📊 Database Migration

The system now uses SQLite for better performance and reliability. To migrate your data:

```bash
# Run the migration script (one-time setup)
python migrate_to_sqlite.py
```

This will:
- Create `data/restaurants.db` SQLite database
- Migrate all restaurant data from JSON
- Create indexes for faster queries
- Show migration progress

## 🚀 Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure AI Service

**Option A: Using Ollama (Local AI - Recommended)**

1. Install Ollama:
   - **macOS/Linux**: 
     ```bash
     curl -fsSL https://ollama.ai/install.sh | sh
     ```
   - **Windows**: Download from [ollama.ai](https://ollama.ai)

2. Download the AI model:
   ```bash
   ollama pull llama3.2
   ```

3. Start Ollama service:
   ```bash
   ollama serve
   ```

4. Configure `.env`:
   ```env
   AI_SERVICE=ollama
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   ```

**Option B: Using OpenRouter (Cloud AI)**

1. Get your API key from [openrouter.ai](https://openrouter.ai/)

2. Configure `.env`:
   ```env
   AI_SERVICE=openrouter
   OPENROUTER_API_KEY=your_api_key_here
   ```

**Option C: Using OpenAI**

1. Get your API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

2. Configure `.env`:
   ```env
   AI_SERVICE=openai
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ```

### 3. Verify Data

Ensure your restaurant data is in place:
```
data/openrice_complete.json
```

## 🎮 Usage

### Start the Application

```bash
python app.py
```

The server will start at `http://localhost:5000`

### Using the Web Interface

1. **Choose Language**: Click "English" or "繁體中文" in the top-right corner

2. **Enter Your Preferences**: Describe what you're looking for (e.g., "romantic Italian dinner" or "casual dim sum with family")

3. **Set Your Budget**: Choose your price range per person

4. **Select District**: Pick your preferred Hong Kong district or choose "Any"

5. **Get Recommendations**: Click "Find Perfect Restaurant" and let AI analyze your preferences

6. **Browse Results**: View personalized restaurant recommendations with:
   - Match score and reasons
   - Restaurant details and ratings (bilingual)
   - Popular dishes
   - Contact information and directions

## 🛠️ Admin Panel

Access the admin panel at `http://localhost:5000/admin`

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change these credentials in `.env` for production use!

### Admin Features

1. **Dashboard**
   - View total restaurants, districts, and cuisines
   - See average ratings and statistics
   - Monitor price distribution
   - Identify most popular cuisines and districts

2. **Restaurant Management**
   - Add new restaurants with full details
   - Edit existing restaurant information
   - Delete restaurants
   - Search and filter restaurants
   - Bulk operations

3. **Settings**
   - Configure AI service
   - Check database status
   - System configuration

### Changing Admin Credentials

Edit `.env` file:
```env
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=generate-a-random-secret-key-here
```

### Security Notes
- Admin panel requires login authentication
- Session-based authentication
- Change default credentials immediately
- Use a strong SECRET_KEY in production
- Consider adding HTTPS in production

## 📊 Restaurant Data Structure

The system uses OpenRice data with the following fields:
- Name (English & Chinese)
- Cuisine type
- District/Location
- Price range
- Contact information
- Opening hours
- Customer ratings
- Popular dishes
- Descriptions

## 🏗️ Technical Architecture

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Flask (Python)
- **AI Engine**: Ollama (Llama 3.2) or OpenRouter
- **Data Format**: JSON
- **UI Design**: Responsive with gradient themes and Font Awesome icons

## 🔧 Configuration

### Environment Variables (.env)

```env
# AI Service: 'ollama', 'openrouter', or 'openai'
AI_SERVICE=ollama

# Ollama Settings
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OpenRouter Settings
OPENROUTER_API_KEY=your_key_here

# OpenAI Settings
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

## 🩺 Health Check

Check system status:
```
http://localhost:5000/health
```

Returns:
- Server status
- AI service type and connection status
- Number of restaurants loaded

## ⚠️ Important Notes

- This system provides recommendations for reference only
- Always verify restaurant information before visiting
- Ratings and information are sourced from OpenRice data
- For best AI analysis, use descriptive preferences

## 🐛 Troubleshooting

### Ollama Connection Failed

- Ensure Ollama is running: `ollama serve`
- Check if port 11434 is available
- Verify the model is downloaded: `ollama list`

### No Restaurants Found

- Check that `data/openrice_complete.json` exists
- Verify the JSON file is valid
- Try broader search criteria

### Server Won't Start

- Ensure port 5000 is not in use
- Check all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version is 3.8 or higher

### AI Analysis Not Working

- **Ollama**: Ensure service is running and model is downloaded
- **OpenRouter**: Verify API key is valid and has credits
- **OpenAI**: Verify API key is valid and has credits
- Check `.env` configuration is correct

## 📝 API Endpoints

### `GET /`
Main application page

### `POST /recommend`
Get restaurant recommendations

**Request Body:**
```json
{
  "preferences": "Looking for spicy Sichuan food",
  "budget": "$101-200",
  "district": "Central"
}
```

**Response:**
```json
{
  "success": true,
  "recommendations": [...],
  "analysis": {...},
  "total_matches": 50
}
```

### `GET /health`
System health check

### Admin API Endpoints

All admin endpoints require authentication via session.

#### `POST /admin/login`
Admin login

#### `GET /admin/logout`
Admin logout

#### `GET /admin`
Admin dashboard page

#### `GET /admin/api/stats`
Get dashboard statistics

#### `GET /admin/api/restaurants`
Get all restaurants

#### `GET /admin/api/restaurants/<id>`
Get single restaurant

#### `POST /admin/api/restaurants`
Add new restaurant

#### `PUT /admin/api/restaurants/<id>`
Update restaurant

#### `DELETE /admin/api/restaurants/<id>`
Delete restaurant

## 🎨 Customization

### Changing AI Models

For Ollama, you can use different models:
```bash
ollama pull mistral
ollama pull codellama
```

Update `.env`:
```env
OLLAMA_MODEL=mistral
```

### Adjusting Match Algorithm

Edit `calculate_match_score()` in `app.py` to customize:
- Budget weight (default: 40 points)
- District weight (default: 30 points)
- Cuisine weight (default: 20 points)
- Rating weight (default: 10 points)

## 📄 License

This project is for educational and personal use.

## 🙏 Acknowledgments

- Restaurant data sourced from OpenRice Hong Kong
- Inspired by the [Doctor](https://github.com/Xenovative/Doctor) medical matching system
- AI powered by Ollama and OpenRouter

## 🚀 Future Enhancements

- [ ] Add user reviews and favorites
- [ ] Implement map integration
- [ ] Support for dietary restrictions filtering
- [x] Multi-language interface (繁體中文) ✅
- [ ] Restaurant booking integration
- [ ] Save and share recommendation lists
- [ ] Voice input support
- [ ] Simplified Chinese (简体中文) support

---

**Made with ❤️ for Hong Kong food lovers**
