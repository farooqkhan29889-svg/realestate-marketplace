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
- **Frontend**: Streamlit (100% Python — no JavaScript)
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

4. **Configure secrets** (optional for local dev):
   ```bash
   cp .env.example .env                       # backend settings
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # frontend -> backend URL
   ```
   With defaults, the UI talks to the backend at `http://127.0.0.1:8000`.

5. **Run the application** (starts backend + Streamlit UI together):
   ```bash
   python run.py
   ```
   - Frontend UI: [http://127.0.0.1:8501](http://127.0.0.1:8501)
   - Backend API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

   To run them separately (e.g. in two terminals):
   ```bash
   uvicorn app.main:app --reload --port 8000          # backend
   streamlit run streamlit_app.py                      # frontend
   ```

---

## 🔑 Demo logins (development only)

Seeded when `ENVIRONMENT=development`. The admin password comes from `ADMIN_PASSWORD` in `.env`
(a secure one is generated and printed to the backend console on first run if unset).

| Role   | Email                     | Password                    |
|--------|---------------------------|-----------------------------|
| Seller | `seller@realestate.com`   | `seller123`                 |
| Buyer  | `buyer@realestate.com`    | `buyer123`                  |
| Admin  | `admin@realestate.com`    | value of `ADMIN_PASSWORD`   |

---

## 🔒 How contact shielding protects the 1% commission

Listing a property is free. Buyer and seller contact details stay **hidden** while a deal is
`PENDING_REVIEW`. Only after an admin/broker **schedules the meeting** are contacts unlocked for
the two parties — and the platform bills **1% from each side** when the deal is closed. This flow
is enforced server-side in `app/routers/deals.py`, so it cannot be bypassed from the UI.

---

## 🌐 Deploying to Production

The app is **two Python services**: the FastAPI backend and the Streamlit frontend. Deploy both.

### 1. Backend on Render (free)

The repo includes a `render.yaml` blueprint (web service + free Postgres).

1. Push this repo to GitHub and sign in to [Render.com](https://render.com) with GitHub.
2. Click **New + > Blueprint** and select this repository. Render reads `render.yaml` and
   creates the `realestate-backend` web service plus the `realestate-db` Postgres instance.
3. Render auto-generates `SECRET_KEY` and `ADMIN_PASSWORD`. Open the service's
   **Environment** tab to read the generated `ADMIN_PASSWORD` (you need it to sign in as admin).
4. Deploy. Your backend URL looks like `https://realestate-backend.onrender.com`.
   Health check: `https://<your-backend>/api/v1/meta`.

> Prefer manual setup instead of the blueprint? Create a **Web Service** with
> Build `pip install -r requirements.txt`, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`,
> and set `ENVIRONMENT=production`, `SECRET_KEY`, `ADMIN_PASSWORD`, and `DATABASE_URL`.

### 2. Frontend on Streamlit Community Cloud (free)

1. Sign in to [share.streamlit.io](https://share.streamlit.io) with GitHub.
2. Click **New app** → repository = this repo, branch = `main`,
   **Main file path = `streamlit_app.py`**.
3. Before first run, open **Advanced settings > Secrets** and paste:
   ```toml
   api_base_url = "https://<your-backend>.onrender.com"
   ```
   (no trailing slash). This is the only config the UI needs.
4. Deploy. Streamlit installs `requirements.txt` (which includes `streamlit` + `requests`)
   and runs `streamlit run streamlit_app.py`.

### 3. Alternative: single Docker container / VPS
```bash
docker build -t realestate-marketplace .
docker run -p 8000:8000 -e DATABASE_URL="postgresql://user:pass@host/db" realestate-marketplace
```
> The Dockerfile runs the **backend** only. For the UI on the same host, run
> `streamlit run streamlit_app.py` alongside it with `API_BASE_URL` pointed at the backend.

### Production checklist
- `ENVIRONMENT=production` (refuses to boot with a weak/missing `SECRET_KEY`).
- Strong `SECRET_KEY` and explicit `ADMIN_PASSWORD` (never the dev defaults).
- Real Postgres `DATABASE_URL` (SQLite is dev-only).
- Restrict `CORS_ORIGINS` to your frontend origin if you ever call the API from a browser.

---

## 🧪 Running Tests
```bash
python test_marketplace.py
```
