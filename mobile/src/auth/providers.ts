// Each sign-in method ends with a Supabase session. App.tsx listens for it and then calls the
// backend's /me, which verifies the token and creates the user row on first sign-in.

import * as AppleAuthentication from 'expo-apple-authentication';
import * as Crypto from 'expo-crypto';
import {
  GoogleSignin,
  isErrorWithCode,
  isSuccessResponse,
  statusCodes,
} from '@react-native-google-signin/google-signin';
import { Platform } from 'react-native';

import { config } from '../lib/config';
import { requireSupabase } from '../lib/supabase';

/** Thrown with a message that's safe to show the user. */
export class SignInError extends Error {}

/** Returned when the user closes the provider's sheet, which isn't an error. */
export const CANCELLED = 'cancelled' as const;
type Result = void | typeof CANCELLED;

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

// --- Google (iOS and Android) ---------------------------------------------------------------

// iOS needs its own client ID (and the URL scheme app.config.ts derives from it); Android only
// needs the web client ID, plus an Android client registered with the app's SHA-1.
export const isGoogleSignInConfigured =
  Platform.OS !== 'web' &&
  Boolean(config.googleWebClientId) &&
  (Platform.OS !== 'ios' || Boolean(config.googleIosClientId));

let googleConfigured = false;

function configureGoogle() {
  if (googleConfigured) return;
  GoogleSignin.configure({
    // The ID token's audience is the web client ID, which is the one Supabase is told to accept.
    webClientId: config.googleWebClientId,
    iosClientId: config.googleIosClientId || undefined,
  });
  googleConfigured = true;
}

export async function signInWithGoogle(): Promise<Result> {
  const supabase = requireSupabase();
  if (!isGoogleSignInConfigured) {
    throw new SignInError('Google sign-in isn’t set up yet.');
  }
  configureGoogle();

  let idToken: string | null;
  try {
    if (Platform.OS === 'android') {
      await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
    }
    const response = await GoogleSignin.signIn();
    if (!isSuccessResponse(response)) return CANCELLED;
    idToken = response.data.idToken;
  } catch (e) {
    if (isErrorWithCode(e)) {
      if (e.code === statusCodes.SIGN_IN_CANCELLED || e.code === statusCodes.IN_PROGRESS) {
        return CANCELLED;
      }
      if (e.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
        throw new SignInError('Google sign-in needs Google Play services on this device.');
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
  if (isGoogleSignInConfigured) {
    configureGoogle();
    // Clears Google's cached account so the next sign-in shows the account picker again.
    await GoogleSignin.signOut().catch(() => {});
  }
  await requireSupabase().auth.signOut();
}
