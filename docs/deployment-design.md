# Deployment Design

## Strategy
The system is designed for reproducible deployment using Docker Compose, separating concerns into distinct services.

## Containers
1. **Frontend**: Nginx serving the compiled React/Vite application.
2. **Backend**: Uvicorn running the FastAPI application.
3. **Database**: PostgreSQL container with a persistent volume.

## Configuration & Environment Variables
- No hardcoded `localhost` URLs in production.
- **Frontend**: `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`
- **Backend**: `DATABASE_URL`, `SIMULATION_RATE_LIMIT`, `MODEL_PATHS`

## Local Development
- Run `docker-compose up` to spin up PostgreSQL.
- Developers can run Frontend and Backend locally via `npm run dev` and `fastapi dev` for faster iteration, relying on `.env` files.
