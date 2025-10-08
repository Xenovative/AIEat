# 🛠️ Admin Panel Guide

## Access

**URL:** `http://localhost:5000/admin`

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **Change these in `.env` for production!**

## Features

### 1. Dashboard (儀表板)
- **Total Restaurants** - View total number of restaurants in database
- **Districts** - Number of unique districts covered
- **Cuisine Types** - Number of different cuisines available
- **Average Rating** - Overall customer satisfaction percentage
- **Quick Stats** - Most popular cuisine, district, and price distribution

### 2. Restaurant Management (餐廳管理)
- **View All Restaurants** - Browse complete restaurant list with ratings
- **Search** - Filter by name, cuisine, or district
- **Add New Restaurant** - Complete form with bilingual fields:
  - Name (English & Chinese)
  - Cuisine type (English & Chinese)
  - District (English & Chinese)
  - Price range
  - Phone number
  - Address (English & Chinese)
  - Opening hours (English & Chinese)
  - Description (English & Chinese)
  - Popular dishes (English & Chinese)
  - Website URL
- **Edit Restaurant** - Update any restaurant information
- **Delete Restaurant** - Remove restaurants from database

### 3. Settings (設定)
- **AI Service Configuration** - Choose between Ollama, OpenRouter, or OpenAI
- **Database Status** - Check database connection

## Language Support

The admin panel is fully bilingual (English/中文):
- Toggle language using the language switcher in top-right corner
- All interface elements translate automatically
- Form labels and messages adapt to selected language
- Default language: Chinese (中文)

## Security Features

- **Session-based Authentication** - Secure login system
- **Protected Routes** - All admin endpoints require authentication
- **Auto-logout** - Session expires when browser closes
- **Password Protection** - Credentials stored in environment variables

## Configuration

Edit `.env` to customize:

```env
# Admin Panel Configuration
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=generate-a-random-secret-key-here
```

## API Endpoints

All admin API endpoints are protected and require authentication:

- `GET /admin/api/stats` - Dashboard statistics
- `GET /admin/api/restaurants` - List all restaurants
- `GET /admin/api/restaurants/<id>` - Get single restaurant
- `POST /admin/api/restaurants` - Create new restaurant
- `PUT /admin/api/restaurants/<id>` - Update restaurant
- `DELETE /admin/api/restaurants/<id>` - Delete restaurant

## Usage Tips

1. **Adding Restaurants**: Fill in at least the required fields (marked with *)
2. **Bilingual Content**: Provide both English and Chinese for better user experience
3. **Search**: Use the search bar to quickly find specific restaurants
4. **Real-time Updates**: Changes are immediately reflected in the main app
5. **Data Persistence**: All changes are saved to SQLite database

## Troubleshooting

**Can't login?**
- Check credentials in `.env` file
- Ensure SECRET_KEY is set
- Clear browser cookies and try again

**Changes not showing?**
- Refresh the main app page
- Check database connection
- Verify restaurant data was saved

**Language not switching?**
- Click the language toggle in top-right
- URL should include `?lang=zh` or `?lang=en`

## Best Practices

1. **Regular Backups** - Backup `data/restaurants.db` regularly
2. **Strong Passwords** - Use secure credentials in production
3. **HTTPS** - Enable HTTPS for production deployment
4. **Data Validation** - Verify restaurant information before saving
5. **Consistent Formatting** - Follow existing data patterns

---

**Made with ❤️ for AIEat Restaurant Management**
