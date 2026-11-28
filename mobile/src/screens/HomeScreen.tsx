import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import type { Me } from '../lib/api';
import { colors, fonts } from '../theme';

type Props = {
  me: Me | null;
  /** Set when the backend couldn't be reached or rejected the token. */
  error?: string | null;
  onRetry: () => void;
  onSignOut: () => void;
};

// Placeholder for the signed-in app until the meal-plan screens exist.
export default function HomeScreen({ me, error, onRetry, onSignOut }: Props) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.screen, { paddingTop: insets.top + 24, paddingBottom: insets.bottom + 16 }]}>
      <View style={styles.body}>
        {me ? (
          <>
            <Text style={styles.title} accessibilityRole="header">
              You’re in
            </Text>
            <Text style={styles.subtitle}>Signed in as {me.email ?? 'your account'}.</Text>
          </>
        ) : error ? (
          <>
            <Text style={styles.title} accessibilityRole="header">
              Couldn’t reach Muscle Mom
            </Text>
            <Text style={styles.subtitle}>{error}</Text>
            <Pressable onPress={onRetry} style={styles.retry} accessibilityRole="button">
              <Text style={styles.link}>Try again</Text>
            </Pressable>
          </>
        ) : (
          <ActivityIndicator color={colors.tomato} />
        )}
      </View>

      <Pressable
        onPress={onSignOut}
        style={({ pressed }) => [styles.button, { backgroundColor: pressed ? colors.whitePressed : colors.white }]}
        accessibilityRole="button"
      >
        <Text style={styles.buttonText}>Sign out</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.cream,
    paddingHorizontal: 24,
  },
  body: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontFamily: fonts.bold,
    fontSize: 28,
    lineHeight: 36,
    color: colors.ink,
    textAlign: 'center',
  },
  subtitle: {
    marginTop: 8,
    fontFamily: fonts.regular,
    fontSize: 16,
    lineHeight: 23,
    color: colors.inkMuted,
    textAlign: 'center',
  },
  retry: {
    marginTop: 16,
  },
  link: {
    fontFamily: fonts.semiBold,
    fontSize: 15,
    color: colors.link,
  },
  button: {
    height: 54,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    fontFamily: fonts.semiBold,
    fontSize: 16,
    color: colors.ink,
  },
});
