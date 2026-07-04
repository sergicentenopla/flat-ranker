# FlatRanker

A web app to compare flats and get a personalized ranking based on your priorities.

## What it does

When you're actively searching for a flat, FlatRanker helps you decide which one fits you best. Add the flats you're considering, define your points of interest (work, gym, university...), and the app calculates a personalized score for each flat based on what matters most to you.

Each flat gets a ranked score with qualitative comments:
- ✔ Good price per m²
- ✔ Excellent location
- ✘ Small compared to others

## Features

- Add and compare multiple flats
- Define points of interest per flat with custom weights (work matters more than the gym? set it)
- Automatic travel time calculation for 4 transport modes (car, public transport, walking, cycling) via Google Maps API
- Personalized scoring across 3 dimensions: value (€/m²), connectivity, and comfort
- Adjust priority weights with sliders and see the ranking update in real time
- Qualitative comments explaining why each flat scores the way it does

## Tech stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLite
- **Frontend**: React 19, Vite, Axios, React Router
- **External API**: Google Maps Distance Matrix API
- **Deployment**: Render (backend), Vercel (frontend)

## Running locally

### Backend
```bash
cd comparador-pisos
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create a .env file with your GOOGLE_MAPS_API_KEY
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Future improvements

- Scraping listing data automatically from a URL (Idealista, Fotocasa)
- User authentication to save personal flat searches
- Integrate travel time into the scoring formula per transport mode preference
- Mobile-friendly UI
