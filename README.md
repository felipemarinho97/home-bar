# Home Bar Platform

Self-hosted cocktail menu and inventory manager for your home bar. Mobile-first guest menu, backoffice inventory tracking, and AI-assisted cocktail creation.

## Features

- **Guest Menu** — mobile-first, auto-filtered to show only available cocktails
- **Inventory Management** — track quantities, bottle sizes, expiry dates (syrups)
- **Ingredient Substitutes** — define per-recipe substitutes so drinks stay available when you run out
- **AI Recipe Generation** — generate detailed preparation steps and tags via DeepSeek (or any OpenAI-compatible API)
- **Dark theme** — amber-on-charcoal, wood-grain texture, custom fonts

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/your-username/drink-manager.git
cd drink-manager

# Edit .env with your password and AI key (optional)
cp .env.example .env   # or edit .env directly
nano .env

docker compose up -d
```

Open [http://localhost:8000](http://localhost:8000) for the guest menu.
Admin at [http://localhost:8000/admin](http://localhost:8000/admin) (username: `admin`, password from `.env`).

### Local (Python)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env

uvicorn main:app --reload
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKOFFICE_PASSWORD` | yes | — | Admin area password |
| `BACKOFFICE_USERNAME` | no | `admin` | Admin username |
| `DATABASE_URL` | no | `sqlite:///./data/homebar.db` | Database path |
| `SECRET_KEY` | no | — | JWT secret (not currently used) |
| `AI_BASE_URL` | no | `https://api.deepseek.com` | OpenAI-compatible endpoint |
| `AI_API_KEY` | no | — | API key for AI features |
| `AI_MODEL` | no | `deepseek-chat` | Model name |

## Usage

1. **Add ingredient types** — generic categories like "London Dry Gin", "Tonic Water"
2. **Add inventory items** — actual bottles/items, mapped to ingredient types
3. **Create cocktails** — ingredients with measures, glasses, accessories, garnish
4. Optionally use **AI** to generate preparation steps and tags
5. **Define substitutes** per recipe ingredient — click the "+ subs" button in the cocktail form

The guest menu auto-filters: only cocktails where **all** ingredients, **at least one** glass, and **all** accessories are in stock appear.

## Tech Stack

- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vanilla JS + HTML + CSS (no build step)
- **AI**: OpenAI-compatible API (DeepSeek, OpenAI, etc.)
- **Deploy**: Docker + GitHub Actions → GHCR

## GitHub Actions

Pushes to `main` trigger a Docker build and push to `ghcr.io/<user>/drink-manager`.
To use the published image:

```bash
docker run -d -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/uploads:/app/uploads \
  -e BACKOFFICE_PASSWORD=yourpass \
  -e AI_API_KEY=sk-... \
  ghcr.io/your-username/drink-manager:latest
```
