# 🍎 HealthAI – Smart Nutrition Tracker

**HealthAI** is a mobile app that lets users log meals naturally (text or voice) and uses OpenAI to extract nutritional information. It tracks daily totals, offers personalized insights, and is built with modern cloud-first architecture.

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
