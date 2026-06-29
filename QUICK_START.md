# Community Hero - Quick Start Guide

## 🎉 Welcome!

Your Community Hero hyperlocal problem solver platform is ready to run. This guide will get you up and running in minutes.

## ⚡ Installation (Choose One)

### Option 1: Using Docker (Recommended for Windows)

If you have Docker installed, this is the easiest:

```bash
# Build the Docker image
docker build -t community-hero .

# Run the backend
docker run -p 8000:8000 community-hero

# In another terminal, start the frontend
cd frontend
python -m http.server 3000
```

### Option 2: Manual Installation

#### Prerequisites
- Python 3.11+ (not 3.13, due to pydantic-core build issues)
- pip

#### Step 1: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend will be available at: **http://localhost:8000**

#### Step 2: Frontend Setup (in another terminal)

```bash
# Navigate to frontend
cd frontend

# Start the server
python -m http.server 3000
```

✅ Frontend will be available at: **http://localhost:3000**

## 🌐 Access Points

Once both are running:

- **Frontend App**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (interactive Swagger UI)
- **API Testing**: http://localhost:8000/redoc (ReDoc documentation)

## 🚀 First Steps

1. **Create an Account**
   - Click "Sign Up" on the frontend
   - Fill in your details and submit

2. **Report Your First Issue**
   - Click "Report Issue"
   - Fill in the form with issue details
   - Click "Report Issue"

3. **View Dashboard**
   - Navigate to "Dashboard" to see statistics
   - Check "Leaderboard" to see community leaders

4. **Verify Issues**
   - Verify other users' reports
   - Earn reputation points and badges

## 📁 Project Structure

```
COMMUNITY-HERO/
├── backend/                 # FastAPI server
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   ├── schemas/        # Data schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt    # Python packages
│   └── .env               # Configuration
├── frontend/               # HTML/CSS/JS
│   ├── index.html         # Main page
│   ├── assets/
│   │   ├── css/           # Styling
│   │   └── js/            # Interactivity
│   └── pages/             # Additional pages
├── README.md              # Full documentation
└── INSTALL.md             # Installation guide
```

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Change ports:
# Backend:
uvicorn app.main:app --port 8001

# Frontend:
python -m http.server 3001
```

### Dependencies Won't Install
```bash
# Try upgrading pip first
pip install --upgrade pip

# Then install requirements
pip install -r requirements.txt
```

### CORS Errors
- Ensure backend is running on http://localhost:8000
- Ensure frontend is on http://localhost:3000
- Check browser console for exact errors

### Python Version Issues
- This project requires Python 3.11 or later
- Check your Python version: `python --version`
- On Windows, you may need to use `python3` instead of `python`

## 📚 API Endpoints Quick Reference

### Users
- `POST /api/users/register` - Create account
- `POST /api/users/login` - Login
- `GET /api/users/` - List all users
- `GET /api/users/{id}` - Get user profile
- `PUT /api/users/{id}` - Update profile

### Issues
- `POST /api/issues/` - Report new issue
- `GET /api/issues/` - List all issues
- `GET /api/issues/{id}` - Get issue details
- `PUT /api/issues/{id}` - Update issue
- `GET /api/issues/nearby/list` - Nearby issues
- `GET /api/issues/trending/list` - Trending issues

### Verifications
- `POST /api/verifications/` - Verify an issue
- `GET /api/verifications/issue/{id}` - Get verifications for issue

### Comments
- `POST /api/comments/` - Add comment
- `GET /api/comments/issue/{id}` - Get comments on issue

## 🎮 Features to Try

### 1. Report Issues
- Try reporting various types of issues (Pothole, Water Leak, etc.)
- Set priority levels (Low, Medium, High, Critical)
- Add location automatically or manually
- Earn +10 reputation points per report

### 2. Verify Issues
- View other users' reports
- Mark issues as confirmed or need more info
- Earn +15 reputation points per verification

### 3. Track Progress
- See real-time issue statistics
- View trending issues (most verified)
- Track your own contributions

### 4. Gamification
- Earn badges for milestones (5 reports, 10 verifications, etc.)
- Climb the leaderboard
- Build your reputation score

## 🎨 UI Highlights

- Modern gradient designs
- Smooth animations throughout
- Responsive mobile design
- Toast notifications for feedback
- Interactive modals
- Real-time leaderboard updates

## 🔐 Authentication

The system uses mock tokens for development. In production, implement:
- JWT tokens
- Refresh tokens
- OAuth integration
- Two-factor authentication

##💡 Next Steps

1. **Add Real Maps**: Replace map placeholder with Google Maps/Mapbox
2. **Database**: Migrate from SQLite to PostgreSQL
3. **Email Notifications**: Add email alerts for issue updates
4. **Mobile App**: Build React Native mobile application
5. **AI Integration**: Add ML-based issue categorization
6. **Advanced Analytics**: Create admin dashboard

## 📞 Support

- Check README.md for detailed documentation
- Review API docs at http://localhost:8000/docs
- Check copilot-instructions.md for project info

## 🎉 Enjoy!

You now have a fully functional hyperlocal problem solver platform! 

Start reporting issues, verify community problems, and help make your community better! 🚀

---

**Made with ❤️ for better communities**
