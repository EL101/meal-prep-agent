// Each sign-in method ends with a Supabase session. App.tsx listens for it and then calls the
// backend's /me, which verifies the token and creates the user row on first sign-in.

import * as AppleAuthentication from 'expo-apple-authentication';
import { isRunningInExpoGo } from 'expo';
import * as Crypto from 'expo-crypto';
import * as Linking from 'expo-linking';
import * as WebBrowser from 'expo-web-browser';
import { Platform } from 'react-native';

import { config } from '../lib/config';
import { requireSupabase } from '../lib/supabase';

/** Thrown with a message that's safe to show the user. */
export class SignInError extends Error {}

/** Returned when the user closes the provider's sheet, which isn't an error. */
export const CANCELLED = 'cancelled' as const;
type Result = void | typeof CANCELLED;

const isErrorWithCode = (e: unknown): e is { code: string } =>
  typeof e === 'object' && e !== null && typeof (e as { code?: unknown }).code === 'string';

// --- Apple (iOS only) -----------------------------------------------------------------------

export function isAppleSignInSupported(): Promise<boolean> {
  return Platform.OS === 'ios' ? AppleAuthentication.isAvailableAsync() : Promise.resolve(false);
}

export async function signInWithApple(): Promise<Result> {
  const supabase = requireSupabase();
  // Apple gets the SHA-256 of the nonce and puts it in the ID token; Supabase gets the raw nonce
  // and checks the two match, so a stolen token can't be replayed.
  const rawNonce = Crypto.randomUUID();
  const hashedNonce = await Crypto.digestStringAsync(Crypto.CryptoDigestAlgorithm.SHA256, rawNonce);

  let credential: AppleAuthentication.AppleAuthenticationCredential;
  try {
    credential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
      nonce: hashedNonce,
    });
  } catch (e) {
    if (isErrorWithCode(e) && e.code === 'ERR_REQUEST_CANCELED') return CANCELLED;
    throw new SignInError('Apple sign-in didn’t work. Try again.');
  }
  if (!credential.identityToken) {
    throw new SignInError('Apple didn’t return a sign-in token. Try again.');
  }

  const { error } = await supabase.auth.signInWithIdToken({
    provider: 'apple',
    token: credential.identityToken,
    nonce: rawNonce,
  });
  if (error) throw new SignInError(error.message);

  // Apple shares the user's name only on their first sign-in, and it isn't in the ID token.
  const { givenName, familyName } = credential.fullName ?? {};
  if (givenName || familyName) {
    await supabase.auth.updateUser({
      data: {
        full_name: [givenName, familyName].filter(Boolean).join(' '),
        given_name: givenName ?? undefined,
        family_name: familyName ?? undefined,
      },
    });
  }
}

// --- Google (iOS and web) ------------------------------------------------------------------

// iOS development builds with an iOS client ID use the native Google SDK, which needs that client
// ID (and the URL scheme app.config.ts derives from it). Expo Go doesn't ship that native module,
// and importing the package there throws at load time, so it's only required once we know the
// module exists. Everywhere else (web, Expo Go) goes through Supabase's Google sign-in page, for
// which the web client ID only signals that the Google provider is set up.
const isWeb = Platform.OS === 'web';
const isNativeGoogleConfigured =
  Platform.OS === 'ios' &&
  !isRunningInExpoGo() &&
  Boolean(config.googleWebClientId) &&
  Boolean(config.googleIosClientId);

export const isGoogleSignInConfigured =
  (isWeb || Platform.OS === 'ios') && Boolean(config.googleWebClientId);

type GoogleSdk = typeof import('@react-native-google-signin/google-signin');
let googleSdk: GoogleSdk | null = null;

function loadGoogle(): GoogleSdk {
  if (googleSdk) return googleSdk;
  const sdk: GoogleSdk = require('@react-native-google-signin/google-signin');
  sdk.GoogleSignin.configure({
    // The ID token's audience is the web client ID, which is the one Supabase is told to accept.
    webClientId: config.googleWebClientId,
    iosClientId: config.googleIosClientId || undefined,
  });
  googleSdk = sdk;
  return sdk;
}

export async function signInWithGoogle(): Promise<Result> {
  const supabase = requireSupabase();
  if (!isGoogleSignInConfigured) {
    throw new SignInError('Google sign-in isn’t set up yet.');
  }
  if (isWeb) {
    // Leaves the page; Supabase picks up the session from the URL when the app loads again.
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin },
    });
    if (error) throw new SignInError(error.message);
    return;
  }
  if (!isNativeGoogleConfigured) return signInWithGoogleInBrowser();
  const { GoogleSignin, isSuccessResponse, statusCodes } = loadGoogle();

  let idToken: string | null;
  try {
    const response = await GoogleSignin.signIn();
    if (!isSuccessResponse(response)) return CANCELLED;
    idToken = response.data.idToken;
  } catch (e) {
    if (isErrorWithCode(e)) {
      if (e.code === statusCodes.SIGN_IN_CANCELLED || e.code === statusCodes.IN_PROGRESS) {
        return CANCELLED;
      }
    }
    throw new SignInError('Google sign-in didn’t work. Try again.');
  }
  if (!idToken) {
    throw new SignInError('Google didn’t return a sign-in token. Try again.');
  }

  const { error } = await supabase.auth.signInWithIdToken({ provider: 'google', token: idToken });
  if (error) throw new SignInError(error.message);
}

// Opens Supabase's Google sign-in page in an in-app browser, which redirects back to the app
// (exp://… in Expo Go, musclemom://… in a build) with the session tokens in the URL fragment.
async function signInWithGoogleInBrowser(): Promise<Result> {
  const supabase = requireSupabase();
  const redirectTo = Linking.createURL('auth/callback');
  // Shown in the Metro terminal so the exact address can be added to Supabase's Redirect URLs.
  if (__DEV__) console.log('[auth] Google redirect URL (add it to Supabase Redirect URLs):', redirectTo);
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo, skipBrowserRedirect: true },
  });
  if (error || !data.url) throw new SignInError(error?.message ?? 'Google sign-in didn’t work.');

  const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
  if (result.type !== 'success') return CANCELLED;

  const params = new URLSearchParams(result.url.split('#')[1] ?? result.url.split('?')[1] ?? '');
  const description = params.get('error_description');
  if (description) throw new SignInError(description.replace(/\+/g, ' '));
  const accessToken = params.get('access_token');
  const refreshToken = params.get('refresh_token');
  if (!accessToken || !refreshToken) {
    throw new SignInError('Google sign-in didn’t finish. Try again.');
  }
  const { error: sessionError } = await supabase.auth.setSession({
    access_token: accessToken,
    refresh_token: refreshToken,
  });
  if (sessionError) throw new SignInError(sessionError.message);
}

// --- Email (one-time code) ------------------------------------------------------------------

// A 6-digit code instead of a magic link, so sign-in never leaves the app and needs no deep link.
export async function sendEmailCode(email: string): Promise<void> {
  const { error } = await requireSupabase().auth.signInWithOtp({
    email,
    options: { shouldCreateUser: true },
  });
  if (error) throw new SignInError(error.message);
}

export async function verifyEmailCode(email: string, code: string): Promise<void> {
  const { error } = await requireSupabase().auth.verifyOtp({ email, token: code, type: 'email' });
  if (error) throw new SignInError(error.message);
}

// --- Sign out -------------------------------------------------------------------------------

export async function signOut(): Promise<void> {
  if (isNativeGoogleConfigured) {
    // Clears Google's cached account so the next sign-in shows the account picker again.
    await loadGoogle().GoogleSignin.signOut().catch(() => {});
  }
  // Local scope clears this device's session before calling the server, so signing out works
  // offline too. It still revokes this device's refresh token when the server is reachable.
  await requireSupabase().auth.signOut({ scope: 'local' });
}
