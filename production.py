"""
Production WSGI entry point for AIEat
Use with Gunicorn (Linux) or Waitress (Windows)

Linux:
    gunicorn -w 4 -b 0.0.0.0:5000 production:app

Windows:
    waitress-serve --host=0.0.0.0 --port=5000 production:app
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from app import app

# Production configuration
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['TESTING'] = False

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

if __name__ == '__main__':
    # This won't be used in production, but useful for testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
