# Real Estate Marketplace Platform 🏡

A modern, full-stack real estate marketplace platform featuring free seller listings, private buyer-seller meeting scheduling, deal tracking, and a built-in 1% brokerage commission facilitation model.

---

## ✨ Key Features

- **Free Property Listings for Sellers**: Sellers can list apartments, villas, houses, plots, and commercial properties with photos and specs at no upfront charge.
- **Direct Buyer Interest & Shielded Details**: Buyers browse listings with shielded seller contact details to safeguard marketplace integrity.
- **Meeting & Deal Facilitation**: Buyers submit offers and meeting requests. The platform coordinates meetings and tracks deal progress.
- **1% Commission Model**: Clear 1% fee calculation on finalized transactions for sustainable platform monetization.
- **Admin Moderation & Analytics**: Complete dashboard to manage listings, approve meetings, monitor revenue, and settle fees.
- **PostgreSQL & SQLite Support**: Zero-config SQLite for local development; production-grade PostgreSQL support with connection pooling for cloud deployment.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL (Production) / SQLite (Development) with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens) with Bcrypt password hashing
- **Frontend**: Single Page Application (HTML5, Tailwind CSS, Responsive UI)
- **Deployment**: Docker, Render, Railway, Heroku compatible

---

## 🚀 Quick Start (Local Setup)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/farooqkhan29889-svg/realestate-marketplace.git
   cd realestate-marketplace
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
   Interactive API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 🌐 Deploying to Production (Render / Railway / Neon)

### 1. Database Setup (PostgreSQL)
Create a free database on [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or [Render](https://render.com) and copy your connection string:
```text
postgresql://username:password@host:port/dbname?sslmode=require
```

### 2. Deploy on Render (Recommended & Free)
1. Go to [Render.com](https://render.com) and click **New + > Web Service**.
2. Connect your GitHub repository.
3. Configure service settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. In the **Environment Variables** tab, add:
   - `DATABASE_URL` = *(Your PostgreSQL connection string)*
   - `SECRET_KEY` = *(A secure random string)*
5. Click **Deploy Web Service**!

### 3. Deploy with Docker
```bash
docker build -t realestate-marketplace .
docker run -p 8000:8000 -e DATABASE_URL="postgresql://user:pass@host/db" realestate-marketplace
```

---

## 🧪 Running Tests
```bash
python test_marketplace.py
```
