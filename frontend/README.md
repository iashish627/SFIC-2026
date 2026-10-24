# CNG Network Intelligence — Frontend

React + TypeScript + Vite dashboard for the forecasting API.

## Run locally
1. Start the FastAPI forecasting service on port 8000.
2. From this directory run `npm install`.
3. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL=http://localhost:8000` if your API uses a different URL.
4. Run `npm run dev` and open the URL printed by Vite (normally http://localhost:5173).

The dashboard checks `GET /health` and `GET /api/v1/forecast/stations`. The forecast and demand-shock controls call `POST /api/v1/forecast/generate` and `POST /api/v1/forecast/scenario/demand-shock`.

The UI intentionally labels forecasts as estimates and warns that user-entered baseline demand is an assumption, not actual Gujarat Gas sales. The backend must permit the frontend origin via its CORS configuration.