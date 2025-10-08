# 📊 Analytics & Search History Guide

## Overview

The admin panel now includes powerful **Analytics** and **Search History** features to help you understand user behavior and optimize your restaurant recommendations.

## Features

### 📈 Analytics Tab

**Real-time Statistics:**
- **Total Searches** - Total number of restaurant searches performed
- **Unique Users** - Number of unique user sessions
- **Most Popular Cuisine** - Top searched cuisine type
- **Most Popular District** - Most frequently searched district

**Visual Charts (Chart.js):**
1. **Popular Cuisine Searches** - Doughnut chart showing cuisine distribution
2. **Popular District Searches** - Bar chart of district popularity
3. **Budget Distribution** - Horizontal bar chart of price range preferences
4. **Search Trends** - Line chart showing search volume over last 7 days

### 🔍 Search History Tab

**Features:**
- **Complete Search Log** - All user searches with timestamps
- **Pagination** - 50 records per page
- **Time Filters** - Today, This Week, This Month, All
- **Export to CSV** - Download search history data
- **Clear History** - Remove all search records
- **Search Details** - Preferences, cuisine, district, budget, results count, language

## Database Schema

### search_history Table

```sql
CREATE TABLE search_history (
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
```

## API Endpoints

### Analytics

#### GET `/admin/api/analytics`
**Description**: Get comprehensive analytics data

**Response:**
```json
{
  "total_searches": 150,
  "unique_users": 45,
  "popular_cuisine": "Japanese",
  "popular_district": "Central",
  "cuisine_stats": {
    "Japanese": 35,
    "Italian": 28,
    "Chinese": 25
  },
  "district_stats": {
    "Central": 40,
    "Tsim Sha Tsui": 30
  },
  "budget_stats": {
    "$101-200": 50,
    "$201-400": 35
  },
  "trend_data": [
    {"date": "2025-10-01", "count": 20},
    {"date": "2025-10-02", "count": 25}
  ]
}
```

### Search History

#### GET `/admin/api/search-history?page=1&filter=all`
**Description**: Get paginated search history

**Parameters:**
- `page` - Page number (default: 1)
- `filter` - Time filter: `all`, `today`, `week`, `month`

**Response:**
```json
{
  "history": [
    {
      "id": 1,
      "timestamp": "2025-10-08 14:30:00",
      "preferences": "romantic Italian dinner",
      "cuisine": "Italian",
      "district": "Central",
      "budget": "$201-400",
      "results_count": 10,
      "language": "zh",
      "session_id": "abc123"
    }
  ],
  "current_page": 1,
  "total_pages": 3,
  "total_count": 150
}
```

#### DELETE `/admin/api/search-history`
**Description**: Clear all search history

**Response:**
```json
{
  "success": true
}
```

## How It Works

### Automatic Logging

Every time a user searches for restaurants:
1. Search parameters are captured
2. Results count is recorded
3. Data is inserted into `search_history` table
4. Session ID tracks unique users

### Analytics Generation

When you open the Analytics tab:
1. Backend queries `search_history` table
2. Aggregates data by cuisine, district, budget
3. Calculates trends over time
4. Returns JSON data to frontend
5. Chart.js renders interactive visualizations

### Search History Display

When you open the Search History tab:
1. Fetches paginated records from database
2. Applies time filter if selected
3. Displays in sortable table
4. Provides export and clear options

## Usage Examples

### View Analytics

1. Open admin panel
2. Click "數據分析" (Analytics) tab
3. View real-time statistics and charts
4. Analyze user search patterns

### Filter Search History

1. Click "搜尋記錄" (Search History) tab
2. Select time filter (Today/Week/Month)
3. Click "篩選" (Filter)
4. Browse filtered results

### Export Data

1. Open Search History tab
2. Click "匯出" (Export) button
3. CSV file downloads automatically
4. Open in Excel or Google Sheets

### Clear History

1. Click "清除全部" (Clear All) button
2. Confirm deletion
3. All search records removed
4. Analytics reset to zero

## Bilingual Support

All interface elements support Chinese/English:
- Tab names
- Chart labels
- Table headers
- Button text
- Filter options
- Export filenames

## Chart Types

### 1. Doughnut Chart (Cuisine)
- Shows percentage distribution
- Color-coded segments
- Interactive legend
- Hover for details

### 2. Bar Chart (District)
- Vertical bars
- Sorted by popularity
- Green color scheme
- Shows exact counts

### 3. Horizontal Bar Chart (Budget)
- Easy price range comparison
- Blue color scheme
- Sorted by price tier
- Clear labels

### 4. Line Chart (Trends)
- 7-day time series
- Smooth curves
- Filled area
- Date labels

## Performance Considerations

### Database Indexes
Consider adding indexes for better performance:
```sql
CREATE INDEX idx_timestamp ON search_history(timestamp);
CREATE INDEX idx_cuisine ON search_history(cuisine);
CREATE INDEX idx_district ON search_history(district);
```

### Data Retention
Implement automatic cleanup:
- Delete records older than 90 days
- Archive historical data
- Maintain optimal database size

### Pagination
- 50 records per page
- Efficient offset queries
- Fast page navigation

## Privacy & Security

### Data Protection
- Search history is admin-only
- Session IDs are anonymized
- No personal information stored
- GDPR-compliant design

### Access Control
- Requires admin authentication
- Protected API endpoints
- Session-based security

## Troubleshooting

**No data showing?**
- Perform some searches first
- Check database connection
- Verify table was created

**Charts not rendering?**
- Check Chart.js loaded
- Verify data format
- Check browser console

**Export not working?**
- Check browser download settings
- Verify CSV generation
- Try different browser

**Pagination issues?**
- Check page number
- Verify total count
- Reset to page 1

## Best Practices

1. **Regular Monitoring** - Check analytics weekly
2. **Data Analysis** - Identify popular trends
3. **Export Backups** - Save historical data
4. **Clean Old Data** - Remove outdated records
5. **Privacy Compliance** - Follow data protection laws

## Future Enhancements

Potential additions:
- [ ] User demographics
- [ ] Conversion tracking
- [ ] A/B testing support
- [ ] Custom date ranges
- [ ] Advanced filtering
- [ ] Real-time updates
- [ ] Email reports
- [ ] Data visualization dashboard

---

**Made with ❤️ for AIEat Analytics**
