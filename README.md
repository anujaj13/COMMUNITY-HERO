# Community Hero - Hyperlocal Problem Solver

A modern platform for citizens to identify, report, validate, track, and resolve community issues through collaboration and intelligent automation.

## Features

✨ **Core Features:**
- 🖼️ Image and video-based issue reporting
- 🤖 AI-powered issue categorization
- 📍 Geolocation and interactive mapping
- ✅ Community verification system
- 📊 Real-time issue tracking
- 📈 Impact dashboards
- 🎮 Gamification & leaderboards
- 🏅 Badge & reputation system

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT-based (expandable)
- **APIs**: RESTful architecture

### Frontend
- **HTML5** with semantic markup
- **CSS3** with modern animations and gradients
- **JavaScript (ES6+)** for interactivity
- **Responsive Design** for all devices

## Project Structure

```
COMMUNITY-HERO/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API endpoints
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Helper functions
│   │   └── main.py          # FastAPI app
│   ├── uploads/             # User uploads
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables
├── frontend/
│   ├── index.html           # Main page
│   ├── assets/
│   │   ├── css/style.css    # Animations & styling
│   │   ├── js/app.js        # Interactive logic
│   │   └── images/          # Asset storage
│   └── pages/               # Additional pages
├── README.md
└── .github/copilot-instructions.md
```

## Getting Started

### Prerequisites
- Python 3.9+
- pip
- Modern web browser

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # or
   source venv/bin/activate      # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Start a local server:**
   ```bash
   # Using Python
   python -m http.server 3000
   
   # Or using Node.js http-server
   npx http-server -p 3000
   ```

   Access the app at `http://localhost:3000`

## Production Deployment

For production grade deployment, the `API_BASE_URL` can be passed as an environment variable or replaced in the frontend files.

### GitHub Workflow
The included [.github/workflows/deploy.yaml](.github/workflows/deploy.yaml) automatically:
1. Deploys the Backend to Google Cloud Run.
2. Captures the Backend instance URL.
3. Deploys the Frontend and injects the Backend URL as `API_BASE_URL`.

### Manual Docker Deployment
```bash
# Backend
docker run -e GEMINI_API_KEY=your_key -e DATABASE_URL=your_db_url -p 8000:8080 community-hero-api

# Frontend
docker run -e API_BASE_URL=https://your-api-url.com -p 3000:8080 community-hero-web
```

## AI Image Analysis Setup

The platform uses **Google Gemini AI** to automatically analyze images and categorize issues. This feature requires an API key.

### Quick Setup

1. **Get a Gemini API Key** (free):
   - Visit: https://ai.google.dev/gemini-api
   - Sign in with Google
   - Click "Get API Key"
   - Copy the key

2. **Add to `.env` file** in the `backend/` folder:
   ```
   GEMINI_API_KEY=your-api-key-here
   ```
   Replace `your-api-key-here` with your actual API key.

3. **Restart the backend**:
   ```bash
   # Kill the running backend (Ctrl+C)
   # Then restart:
   uvicorn app.main:app --reload
   ```

4. **Test it**:
   ```bash
   cd backend
   python test_ai_setup.py
   ```

### Full Setup Guide

For detailed setup instructions, see: [GEMINI_SETUP.md](GEMINI_SETUP.md)

### Troubleshooting

If AI analysis fails after uploading an image:

1. **Check the error message** in the backend terminal
2. **Enable debug logging**:
   ```
   DEBUG=true
   ```
3. **See troubleshooting guide**: [AI_ANALYSIS_TROUBLESHOOTING.md](AI_ANALYSIS_TROUBLESHOOTING.md)

**Note**: If the API is unavailable, you can still create issues manually using the standard form.

## API Documentation

### Users
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - Login user
- `GET /api/users/{user_id}` - Get user profile
- `GET /api/users/` - Get all users
- `PUT /api/users/{user_id}` - Update user
- `GET /api/users/{user_id}/leaderboard` - Get leaderboard

### Issues
- `POST /api/issues/` - Create new issue
- `GET /api/issues/` - List all issues
- `GET /api/issues/{issue_id}` - Get issue details
- `PUT /api/issues/{issue_id}` - Update issue
- `GET /api/issues/nearby/list` - Get nearby issues
- `GET /api/issues/trending/list` - Get trending issues
- `POST /api/issues/{issue_id}/upload-image` - Upload image
- `GET /api/issues/stats/by-category` - Get category stats

### Verifications
- `POST /api/verifications/` - Verify an issue
- `GET /api/verifications/issue/{issue_id}` - Get issue verifications
- `GET /api/verifications/user/{user_id}` - Get user verifications

### Comments
- `POST /api/comments/` - Add comment
- `GET /api/comments/issue/{issue_id}` - Get issue comments
- `PUT /api/comments/{comment_id}/like` - Like comment

### Dashboard
- `GET /api/stats/dashboard` - Get dashboard statistics
- `GET /health` - Health check

## Issue Categories

- 🕳️ Pothole
- 💧 Water Leak
- 💡 Streetlight
- 🗑️ Waste Management
- 🛣️ Road Damage
- 🌊 Flooding
- 🏛️ Public Facility
- 🔒 Safety
- ❓ Other

## Priority Levels

- 🟢 Low
- 🟡 Medium
- 🔴 High
- ⚫ Critical

## Issue Status

- 📝 Reported
- ✅ Verified
- 🔧 In Progress
- ✔️ Resolved
- ❌ Closed

## Gamification System

### Badges & Rewards
- **First Report**: Report your first issue
- **Verification Master**: Complete 10 verifications
- **Community Champion**: Report 25 issues
- **Super Verifier**: 50+ verifications
- **Respected Citizen**: 500+ reputation points

### Reputation Points
- Report Issue: +10 points
- Issue Verified: +5 points
- Verification Approved: +15 points
- Issue Resolved: +20 points

## Database Models

### User
- id, username, email, password_hash
- full_name, avatar_url, bio
- latitude, longitude, address
- is_verified, reputation_score
- badges_earned, issues_reported, verifications_made
- created_at, updated_at

### Issue
- id, title, description
- category, priority, status
- latitude, longitude, address
- image_url, video_url
- reported_by_id, verification_count
- impact_score, estimated_resolution_date
- assigned_to_id, created_at, updated_at, resolved_at

### Verification
- id, issue_id, verified_by_id
- is_confirmed, severity_level
- comment, created_at

### Comment
- id, issue_id, user_id
- text, likes
- created_at, updated_at

### UserBadge
- id, user_id, badge_name
- badge_description, badge_icon
- earned_at

## Future Enhancements

- 🗺️ Real map integration (Google Maps/Mapbox)
- 🤖 AI-powered issue categorization
- 📱 Mobile app (React Native/Flutter)
- 🔐 Advanced authentication (OAuth, 2FA)
- 📧 Email notifications
- 📞 SMS alerts
- 🔍 Advanced search & filters
- 📊 Predictive analytics
- 🎯 ML-based priority estimation
- 💬 Real-time chat support
- 🌐 Multi-language support
- 📈 Analytics dashboard for admins

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@communityhero.com or open an issue on GitHub.

## Roadmap

- [ ] Phase 1: Core MVP (Current)
- [ ] Phase 2: Mobile App
- [ ] Phase 3: AI Integration
- [ ] Phase 4: Advanced Analytics
- [ ] Phase 5: Enterprise Features

---

**Made with ❤️ for better communities**
