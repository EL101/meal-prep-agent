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

Backend layout: `api/` (routes) → `services/` (business logic) → `repositories/` (queries) → `models/` (tables). `schemas/` holds the Pydantic request/response models.

**Mobile** (Node 22, Expo)

```bash
cd mobile
npm install
cp .env.example .env.local           # Supabase, backend URL and Google client IDs
npx expo run:ios                     # or run:android; builds a development build
```

Apple and Google sign-in use native modules that Expo Go doesn't include, so run a development build (`npx expo run:ios|android` locally, or `npx eas-cli@latest build --profile development`). Expo Go and web still work for email sign-in; they hide the Apple and Google buttons.

## Sign-in setup

The app signs in with Supabase (Apple, Google, or a 6-digit email code), then calls the backend's `/me` with the Supabase access token. The backend verifies the token and creates the user row on first sign-in.

1. **Supabase keys.** Backend: `SUPABASE_URL` and `SUPABASE_SECRET_KEY` in `backend/.env` and on Railway. App: `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (the publishable key, never the secret one) in `mobile/.env.local`, plus `EXPO_PUBLIC_API_URL`.
2. **Email.** Supabase → Authentication → Emails: in the "Magic Link" and "Confirm signup" templates, include `{{ .Token }}` so the email carries the 6-digit code the app asks for (a first sign-in can use the signup template).
3. **Apple** (iOS). In the Apple Developer portal, turn on "Sign in with Apple" for the app ID `com.musclemom.app` (set in `app.json`). In Supabase → Authentication → Sign In / Providers → Apple, enable it and add `com.musclemom.app` under Client IDs. Native sign-in needs no Apple secret key.
4. **Google.** In Google Cloud → APIs & Services → Credentials, create three OAuth client IDs: Web, iOS (bundle ID `com.musclemom.app`) and Android (package `com.musclemom.app` plus your build's SHA-1; `eas credentials` shows it for EAS builds). In Supabase's Google provider, enable it, put the Web client ID and secret in, add the iOS client ID to "Authorized Client IDs", and turn on "Skip nonce check" (the iOS Google SDK sets a nonce the app can't read). Set `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` and `EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID`; `app.config.ts` derives the iOS URL scheme from the iOS one, so rebuild after changing it.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs backend lint + tests and the mobile type check on every PR and push to `main`. On `main`, once those pass, it deploys `backend/` to Railway.

One-time Railway setup:
1. Create a Railway project with a service for the backend and add a Postgres database. Set the service's `DATABASE_URL` to the Postgres URL with the `postgresql+asyncpg://` scheme.
2. In the Railway project settings, create a **project token**.
3. In GitHub → Settings → Secrets and variables → Actions, add the secret `RAILWAY_TOKEN` (the token) and the variable `RAILWAY_SERVICE` (the service name).
