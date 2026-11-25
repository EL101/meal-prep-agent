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

Prereqs: Python 3.12+ with [uv](https://docs.astral.sh/uv/), Node 22, Docker, and the Expo Go app on your phone.

```bash
make setup                          # uv sync + npm install
cp backend/.env.example backend/.env   # fill in ANTHROPIC_API_KEY, Supabase keys, etc.
cp mobile/.env.example mobile/.env.local
make services                       # Postgres + Redis in Docker
make migrate                        # Alembic migrations
make api                            # FastAPI on http://localhost:8000 (docs at /docs)
make worker                         # arq worker that runs Claude jobs
make mobile                         # Expo dev server
```

`make test` and `make lint` run what CI runs. `make evals` makes real Claude calls.

## Repo layout

```
backend/
  app/
    api/routes/       health, profile (+ excluded foods), inventory (+ photo scan), plans, ratings
    models/           SQLAlchemy models; migrations live in backend/alembic/
    schemas/          api.py = HTTP models, llm.py = structured outputs Claude must fill
    services/
      claude.py       every Claude call (Anthropic SDK, structured outputs, refusal fallback)
      exclusions.py   hard allergen/dislike filter, enforced in code
      optimizer.py    OR-Tools CP-SAT: picks recipes + servings within budget and macro goals
      pricing/        receipt → Kroger estimate → BLS estimate
      nutrition/      USDA FoodData Central, Open Food Facts allergens
      storage.py      Supabase Storage for photos
    worker/           arq jobs: scan_inventory, generate_plan, weekly inventory carry-over
  evals/              Claude only vs +validation vs +optimizer, with the README's metrics
  tests/
mobile/               Expo Router app: Plan, Inventory, Groceries, Profile tabs
  lib/                API client, Supabase auth client, shared types
```

Plan generation flow: the app calls `POST /plans`, the API queues a job, and the worker asks Claude for candidate recipes, drops any that hit an excluded food, prices the missing ingredients, and lets the optimizer choose the week. `PATCH /plans/{id}` locks or swaps meals and re-solves the rest.
