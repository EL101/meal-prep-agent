// Import each weight on its own so only these three font files ship with the app.
import { DMSans_400Regular } from '@expo-google-fonts/dm-sans/400Regular';
import { DMSans_600SemiBold } from '@expo-google-fonts/dm-sans/600SemiBold';
import { DMSans_700Bold } from '@expo-google-fonts/dm-sans/700Bold';
import { useFonts } from 'expo-font';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useState } from 'react';
import { View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import {
  CANCELLED,
  isAppleSignInSupported,
  isGoogleSignInConfigured,
  signInWithApple,
  signInWithGoogle,
  signOut,
} from './src/auth/providers';
import { useSession } from './src/auth/useSession';
import { ApiError, getMe, type Me } from './src/lib/api';
import { config } from './src/lib/config';
import EmailSignInScreen from './src/screens/EmailSignInScreen';
import HomeScreen from './src/screens/HomeScreen';
import SignInScreen from './src/screens/SignInScreen';
import { colors } from './src/theme';

export default function App() {
  const [fontsLoaded, fontError] = useFonts({
    DMSans_400Regular,
    DMSans_600SemiBold,
    DMSans_700Bold,
  });
  const { session, loading } = useSession();

  // Fonts load in a few milliseconds; show the cream background until then.
  // If they fail to load, render anyway so the app falls back to the system font
  // instead of staying on a blank screen.
  if ((!fontsLoaded && !fontError) || loading) {
    return <View style={{ flex: 1, backgroundColor: colors.cream }} />;
  }

  return (
    <SafeAreaProvider>
      {session ? <SignedIn userId={session.user.id} /> : <SignedOut />}
      <StatusBar style="dark" />
    </SafeAreaProvider>
  );
}

function SignedOut() {
  const [screen, setScreen] = useState<'start' | 'email'>('start');
  const [appleSupported, setAppleSupported] = useState(false);
  const [busy, setBusy] = useState<'apple' | 'google' | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    isAppleSignInSupported().then(setAppleSupported, () => setAppleSupported(false));
  }, []);

  async function run(provider: 'apple' | 'google', signIn: () => Promise<void | typeof CANCELLED>) {
    setBusy(provider);
    setError(null);
    try {
      await signIn();
      // On success the session listener swaps this screen out; on CANCELLED nothing changes.
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sign-in didn’t work. Try again.');
    } finally {
      setBusy(null);
    }
  }

  if (screen === 'email') {
    return <EmailSignInScreen onBack={() => setScreen('start')} />;
  }
  return (
    <SignInScreen
      onApple={appleSupported ? () => run('apple', signInWithApple) : undefined}
      onGoogle={isGoogleSignInConfigured ? () => run('google', signInWithGoogle) : undefined}
      onEmail={() => {
        setError(null);
        setScreen('email');
      }}
      busy={busy}
      error={error}
    />
  );
}

function SignedIn({ userId }: { userId: string }) {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  // The first /me call verifies the Supabase token on the backend and creates the user's row.
  const load = useCallback(async () => {
    setError(null);
    try {
      setMe(await getMe());
    } catch (e) {
      if (e instanceof ApiError) {
        setError(
          e.status === 401
            ? 'The server didn’t accept your sign-in. Sign out and try again.'
            : `The server returned an error (${e.status}). Try again in a moment.`,
        );
      } else {
        setError(__DEV__ ? `Couldn’t reach the server at ${config.apiUrl}.` : 'Check your connection and try again.');
      }
    }
  }, []);

  useEffect(() => {
    setMe(null);
    load();
  }, [userId, load]);

  return (
    <HomeScreen
      me={me}
      error={error}
      onRetry={load}
      onSignOut={() => {
        signOut().catch(() => {});
      }}
    />
  );
}
