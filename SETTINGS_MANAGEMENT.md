# ⚙️ Settings Management Guide

## Overview

The admin panel now includes a comprehensive **Settings** tab that allows you to:
- Read current configuration from `.env` file
- Update AI service settings
- Change admin credentials
- Monitor system status
- Save changes back to `.env` file

## Features

### 1. AI Service Configuration

**Supported Services:**
- **Ollama** (Local AI)
  - URL configuration (default: `http://localhost:11434`)
  - Model selection (e.g., `llama3.2`, `mistral`)
  
- **OpenRouter** (Cloud AI)
  - API Key management
  - Automatic service detection
  
- **OpenAI** (Cloud AI)
  - API Key management
  - Model selection (GPT-4o Mini, GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo)

### 2. Admin Configuration

- **Username**: Change admin login username
- **Password**: Update admin password (leave blank to keep current)
- **Security**: Password changes require re-login

### 3. System Status

**Real-time Monitoring:**
- **Database Status**: Shows connection status and number of restaurants loaded
- **AI Service Status**: Displays current AI service and connection state

## How It Works

### Loading Settings

When you open the Settings tab:
1. Frontend sends GET request to `/admin/api/settings`
2. Backend reads current values from `.env` file
3. Form fields populate with existing configuration
4. System status checks run automatically

### Saving Settings

When you click "Save Settings":
1. Frontend collects all form values
2. Sends POST request to `/admin/api/settings` with JSON data
3. Backend updates `.env` file with new values
4. Environment variables reload automatically
5. Global AI service variables update
6. Success message displays
7. System status refreshes

### Dynamic Form Display

The form intelligently shows/hides fields based on selected AI service:
- Select **Ollama** → Shows URL and Model fields
- Select **OpenRouter** → Shows API Key field
- Select **OpenAI** → Shows API Key and Model fields

## API Endpoints

### GET `/admin/api/settings`
**Description**: Retrieve current settings from `.env`

**Response:**
```json
{
  "ai_service": "openai",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "llama3.2",
  "openrouter_key": "",
  "openai_key": "sk-proj-...",
  "openai_model": "gpt-4o-mini",
  "admin_username": "admin"
}
```

### POST `/admin/api/settings`
**Description**: Save settings to `.env` file

**Request Body:**
```json
{
  "ai_service": "openai",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "llama3.2",
  "openrouter_key": "",
  "openai_key": "sk-proj-...",
  "openai_model": "gpt-4o-mini",
  "admin_username": "admin",
  "admin_password": "newpassword123"
}
```

**Response:**
```json
{
  "success": true
}
```

## Security Considerations

### API Key Protection
- API keys displayed as password fields (hidden by default)
- Keys only sent when explicitly changed
- Stored securely in `.env` file

### Admin Password
- Password field is type="password" (hidden input)
- Leave blank to keep current password
- Changes require immediate re-login
- Stored in `.env` (use proper hashing in production)

### File Permissions
- `.env` file should have restricted permissions
- Only admin users can access settings endpoints
- Session-based authentication required

## Usage Examples

### Example 1: Switch from Ollama to OpenAI

1. Open Settings tab
2. Select "OpenAI" from AI Service dropdown
3. Enter your OpenAI API key
4. Select desired model (e.g., "GPT-4o Mini")
5. Click "Save Settings"
6. System automatically switches to OpenAI

### Example 2: Change Admin Password

1. Open Settings tab
2. Scroll to "Admin Configuration"
3. Enter new password in "Admin Password" field
4. Click "Save Settings"
5. Log out and log back in with new password

### Example 3: Update Ollama Model

1. Open Settings tab
2. Ensure "Ollama" is selected as AI Service
3. Change "Ollama Model" to desired model (e.g., `mistral`)
4. Click "Save Settings"
5. AI will use new model for recommendations

## Bilingual Support

All settings interface elements are bilingual:
- **Chinese (中文)**: Default language
- **English**: Toggle via language switcher

**Translated Elements:**
- Section headers
- Form labels
- Button text
- Status messages
- Success/error alerts

## Technical Implementation

### Frontend (JavaScript)
```javascript
// Load settings from backend
async function loadSettings() {
    const response = await fetch('/admin/api/settings');
    const data = await response.json();
    // Populate form fields
}

// Save settings to backend
async function saveSettings() {
    const settings = { /* collect form data */ };
    await fetch('/admin/api/settings', {
        method: 'POST',
        body: JSON.stringify(settings)
    });
}
```

### Backend (Python/Flask)
```python
@app.route('/admin/api/settings', methods=['GET'])
def admin_get_settings():
    # Read from .env using os.getenv()
    return jsonify(settings)

@app.route('/admin/api/settings', methods=['POST'])
def admin_save_settings():
    # Write to .env file
    # Reload environment variables
    # Update global variables
    return jsonify({'success': True})
```

## Troubleshooting

**Settings not saving?**
- Check file permissions on `.env`
- Verify admin authentication
- Check browser console for errors

**Changes not taking effect?**
- Settings reload automatically
- Restart app if issues persist
- Check `.env` file was actually updated

**API keys not working?**
- Verify key format is correct
- Check key has not expired
- Ensure sufficient API credits

**System status shows disconnected?**
- For Ollama: Ensure service is running (`ollama serve`)
- For OpenRouter/OpenAI: Verify API key is valid
- Check network connectivity

## Best Practices

1. **Backup `.env`**: Always backup before making changes
2. **Test Changes**: Verify AI service works after switching
3. **Secure Keys**: Never commit `.env` to version control
4. **Strong Passwords**: Use complex admin passwords
5. **Regular Updates**: Keep API keys rotated
6. **Monitor Status**: Check system status regularly

## File Structure

```
.env                    # Configuration file (updated by settings)
app.py                  # Backend API endpoints
templates/admin.html    # Settings UI and JavaScript
```

## Future Enhancements

Potential improvements:
- [ ] Backup/restore settings
- [ ] API key validation before saving
- [ ] Settings history/audit log
- [ ] Bulk configuration import/export
- [ ] Advanced AI model parameters
- [ ] Email notifications for changes

---

**Made with ❤️ for AIEat Configuration Management**
