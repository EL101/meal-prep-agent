Generate meal prep plans based on:
- A picture of your fridge, grocery receipt (most accurate), and/or pantry
- Or generate meal plans without those, and give a budget price

User inputs:
- Inventory: photo of fridge/pantry and/or grocery receipt (confirm uncertain items)
- Weekly budget (added on to what the user has already) + preferred store
- Daily calorie and protein goals
- Cook days, time per session, servings, kitchen equipment (optional with defaults)
- Optional preferences (e.g. low fat, easy to cook, etc.)
- Excluded foods (e.g. allergies, foods the user dislikes, etc.) (enforced by code)
- Rating for each recipe generated from 1-5 stars based on how well they like it, with an optional input for what they dont like about it. Ratings and explanations will go into consideration for future recipes 

Outputs:
- Weekly meal plan + recipes
- Grocery list with prices and estimated total
- Cooking-session timeline
- Editable plan (lock/swap → re-solve)
- Inventory carried to next week (with expiry)

Mobile app tech stack:
- React Native + Expo (frontend)
- Python + FastAPI (backend)
- PostgreSQL + SQLAlchemy + Alembic (database)
- Supabase (auth + image storage + database hosting)
- Anthropic Python SDK (Claude API)
- Railway backend hosting
- Redis + arq (queuing claude jobs)
- Google OR-Tools (optimization)
- USDA FoodData Central (food nutrition facts)
- Open Food Facts (ingredients for allergens)


How pricing is determined:
- Receipt uploads
- Kroger API (labeled as an estimate)
- BLS regional average (labeled as an estimate)

Evals:
- Claude only vs. +validation vs. +optimizer
- Measure: budget violations, calorie/protein error, allergen violations, cost per day, food waste, taste ratings

## Getting started

**Backend** (Python 3.12, [uv](https://docs.astral.sh/uv/))

```bash
docker compose up -d                 # local Postgres
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head          # once models exist: uv run alembic revision --autogenerate -m "..."
uv run fastapi dev app/main.py       # http://localhost:8000/health
uv run pytest
```

**Mobile** (Node 22, Expo)

```bash
cd mobile
npm install
npx expo start                       # scan the QR code with Expo Go
```
