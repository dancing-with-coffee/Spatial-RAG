# Setup Guide

This guide will help you set up Spatial-RAG from scratch.

## Pre-Flight Checklist

Before pushing to GitHub, ensure:

- [ ] `.env` file is NOT committed (it's in `.gitignore`)
- [ ] `.env.example` contains no sensitive data (no API keys)
- [ ] All sensitive credentials are removed from code
- [ ] Docker images build successfully
- [ ] README.md is up to date
- [ ] LICENSE file is present

## Initial Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/yourusername/Spatial-RAG.git
cd Spatial-RAG
```

### 2. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
# IMPORTANT: Never commit .env to git!
nano .env  # or use your preferred editor
```

**Required for LLM synthesis:**
- Add your `OPENAI_API_KEY` to `.env` (optional - system works without it using mock responses)

**Database credentials** (defaults work with Docker):
- `DATABASE_HOST=db` (use `localhost` if running DB locally)
- `DATABASE_PASSWORD=postgres` (change in production!)

### 3. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

### 4. Verify Installation

```bash
# Check database
docker exec -it spatial_rag_db psql -U postgres -d spatial_rag -c "SELECT PostGIS_version();"

# Check API
curl http://localhost:8080/health

# Check frontend (should return HTML)
curl http://localhost:3000 | head -20
```

### 5. Seed Database

```bash
# Generate and insert 500 synthetic documents
docker exec -it spatial_rag_api python /app/seed.py 500
```

### 6. Access Application

- Frontend: http://localhost:3000
- API Docs: http://localhost:8080/docs
- Health: http://localhost:8080/health

## Troubleshooting Setup

### Port Already in Use

If ports 3000, 8080, or 5432 are already in use:

1. Edit `docker-compose.yml` to change port mappings
2. Or stop the conflicting service

### Database Won't Start

```bash
# Check logs
docker-compose logs db

# Remove old volume and restart
docker-compose down -v
docker-compose up -d db
```

### API Errors

```bash
# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api

# Rebuild if needed
docker-compose up -d --build api
```

### Frontend Build Errors

```bash
# Clear cache and rebuild
cd frontend
rm -rf .next node_modules
npm install
npm run dev
```

## Production Deployment

For production deployment:

1. **Change default passwords** in `.env`
2. **Use environment-specific configs** (`.env.production`)
3. **Enable SSL/TLS** for API and frontend
4. **Set up proper database backups**
5. **Configure CORS** appropriately in `api/app/main.py`
6. **Use production Docker images** (not `:latest` tags)
7. **Set up monitoring** and logging
8. **Configure rate limiting** for API endpoints

## Next Steps

- Read [README.md](README.md) for detailed usage
- Check [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute
- Explore the API at http://localhost:8080/docs
- Try different queries in the frontend

