# Setup

One-time configuration for services the app depends on.

## Development builds

Apple and Google sign-in use native modules that Expo Go doesn't include, so run a development build (`npm run ios` locally, or `npx eas-cli@latest build --profile development`). Expo Go and web still work for email sign-in; Expo Go hides the Apple and Google buttons, and web shows Google (through Supabase's sign-in page) but not Apple.

To test on a physical phone, run the backend with `docker compose up -d` (it listens on your LAN; use a network you trust) and set `EXPO_PUBLIC_API_URL` to your computer's LAN IP, e.g. `http://192.168.1.20:8000`.

## Sign-in

The app signs in with Supabase (Apple, Google, or a 6-digit email code), then calls the backend's `/me` with the Supabase access token. The backend verifies the token and creates the user row on first sign-in.

1. **Supabase keys.** Backend: `SUPABASE_URL` and `SUPABASE_SECRET_KEY` in `backend/.env` and on Railway. App: `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (the publishable key, never the secret one) in `mobile/.env.local`, plus `EXPO_PUBLIC_API_URL`.
2. **Email.** Supabase only allows template edits once custom SMTP is set up (Authentication → Emails → SMTP Settings). Then paste `supabase/templates/magic-link.html` into the "Magic Link" template and `supabase/templates/confirm-signup.html` into "Confirm signup" (a first sign-in uses the signup one). Suggested subjects: "Your Muscle Mom sign-in code" and "Welcome to Muscle Mom".
3. **Apple** (iOS). In the Apple Developer portal, turn on "Sign in with Apple" for the app ID `com.musclemom.app` (set in `app.json`). In Supabase → Authentication → Sign In / Providers → Apple, enable it and add `com.musclemom.app` under Client IDs. Native sign-in needs no Apple secret key.
4. **Google.** In Google Cloud → APIs & Services → Credentials, create two OAuth client IDs: Web (with `https://<project-ref>.supabase.co/auth/v1/callback` as a redirect URI) and iOS (bundle ID `com.musclemom.app`). In Supabase's Google provider, enable it, put the Web client ID and secret in, add the iOS client ID to "Authorized Client IDs", and turn on "Skip nonce check" (the iOS Google SDK sets a nonce the app can't read). Set `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` and `EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID`; `app.config.ts` derives the iOS URL scheme from the iOS one, so rebuild after changing it. For web, also add `http://localhost:8081` under Supabase → Authentication → URL Configuration → Redirect URLs, so Supabase sends you back to the app after Google sign-in.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs backend lint + tests and the mobile type check on every PR and push to `main`. On `main`, once those pass, it deploys `backend/` to Railway.

One-time Railway setup:
1. Create a Railway project with a service for the backend and add a Postgres database. Set the service's `DATABASE_URL` to the Postgres URL with the `postgresql+asyncpg://` scheme.
2. In the Railway project settings, create a **project token**.
3. In GitHub → Settings → Secrets and variables → Actions, add the secret `RAILWAY_TOKEN` (the token) and the variable `RAILWAY_SERVICE` (the service name).
