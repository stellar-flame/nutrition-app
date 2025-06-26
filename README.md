# 🍎 NutritionAI – Smart Nutrition Tracker

**NutritionAI** is a mobile app that lets users log meals naturally (text or voice) and uses OpenAI to extract nutritional information. It tracks daily totals, offers personalized insights, and is built with modern cloud-first architecture.

---

## 📱 Features

- 🧠 AI-powered meal parsing using OpenAI GPT-4
- 🍽️ Natural language meal logging via chat interface  
- 📊 Real-time tracking of calories, protein, carbs, fat, fiber, and sugar
- � Daily meal summaries with date navigation
- 🔥 Automatic nutrition totals calculation
- �️ Meal deletion and management
- 🔒 Firebase Authentication integration
- 💾 PostgreSQL database with structured meal storage
- � Cross-platform mobile app (iOS/Android via Expo)
- 🔄 RESTful API with FastAPI backend
- 🎯 Custom React hooks for state management

---

## 🛠 Tech Stack

| Layer         | Tech                          |
|--------------|-------------------------------|
| Frontend     | React Native (Expo) + TypeScript |
| UI Framework | React Navigation v7           |
| State Management | Custom React Hooks       |
| Backend      | Python (FastAPI)              |
| Database     | PostgreSQL + SQLAlchemy ORM  |
| Migrations   | Alembic                       |
| AI           | OpenAI GPT-4 API              |
| Authentication| Firebase Auth                |
| HTTP Client  | Axios                         |
| CORS         | FastAPI CORS Middleware       |
| Environment  | Python dotenv                 |
| Server       | Uvicorn ASGI                  |

---

## 🚀 Getting Started

### Prerequisites
- Node.js + Expo CLI
- Python 3.9+
- PostgreSQL (local or RDS)
- OpenAI API Key

### Frontend Setup
```bash
cd frontend
npm install
npx expo start
```

---

## 🔒 Security Setup

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Setup database with Alembic migrations
alembic upgrade head

# Start FastAPI development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Environment Variables

This project uses environment variables for sensitive credentials:

```bash
# Copy the example file
cp backend/.env.example backend/.env

# Edit the new .env file with your API keys and credentials
nano backend/.env  # or use any text editor
```

### Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com/
2. Go to Project Settings > Service accounts > Generate new private key
3. Download the JSON file and extract the credentials:

   ```
   # From the downloaded JSON file, copy these values to your .env file:
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-multi-line-key\n-----END PRIVATE KEY-----\n"
   FIREBASE_CLIENT_EMAIL=your-client-email
   # ... and other values as needed
   ```

4. Make sure your `.env` file is listed in `.gitignore` to prevent accidental commits

⚠️ **IMPORTANT: Never commit credential files or `.env` files to version control!** ⚠️

---
