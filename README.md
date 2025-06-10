# 🍎 NutritionAI – Smart Nutrition Tracker

**NutritionAI** is a mobile app that lets users log meals naturally (text or voice) and uses OpenAI to extract nutritional information. It tracks daily totals, offers personalized insights, and is built with modern cloud-first architecture.

---

## 📱 Features

- 🧠 AI-powered meal parsing using OpenAI (GPT)
- 🧾 Real-time tracking of calories, protein, carbs, fat, and sugar
- 📊 Daily summaries and running totals
- 🔄 AWS-hosted backend with PostgreSQL storage
- 🔒 (Planned) Secure login with Firebase/Cognito
- 🧭 (Planned) Apple Health / Google Fit sync

---

## 🛠 Tech Stack

| Layer         | Tech                          |
|--------------|-------------------------------|
| Frontend     | React Native (Expo)           |
| Backend      | Python (Flask or Django)      |
| AI           | OpenAI GPT-4 API              |
| Database     | PostgreSQL (AWS RDS)          |
| Hosting      | AWS (Elastic Beanstalk or ECS)|
| Auth (Planned)| Firebase Auth / Cognito      |

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
