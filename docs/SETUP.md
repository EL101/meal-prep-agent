# Setup

One-time configuration for services the app depends on.

## Development builds

Apple and Google sign-in use native modules that Expo Go doesn't include, so run a development build (`npx expo run:ios|android` locally, or `npx eas-cli@latest build --profile development`). Expo Go and web still work for email sign-in; they hide the Apple and Google buttons.

## Sign-in

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
