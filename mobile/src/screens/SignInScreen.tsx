import * as AppleAuthentication from 'expo-apple-authentication';
import type { ReactNode } from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
  type PressableStateCallbackType,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { GoogleLogo } from '../components/BrandIcons';
import { colors, fonts } from '../theme';

const mascot = require('../../assets/mascot.png');

type Props = {
  // A provider's button is hidden when its handler isn't passed (e.g. Apple off iOS).
  onApple?: () => void;
  onGoogle?: () => void;
  onEmail: () => void;
  onTerms?: () => void;
  onPrivacy?: () => void;
  /** Which provider is mid sign-in; every button is disabled meanwhile. */
  busy?: 'apple' | 'google' | null;
  error?: string | null;
};

export default function SignInScreen({
  onApple,
  onGoogle,
  onEmail,
  onTerms,
  onPrivacy,
  busy = null,
  error,
}: Props) {
  const insets = useSafeAreaInsets();
  const { height } = useWindowDimensions();
  // 280pt on a standard phone; smaller on short screens so the buttons stay in view.
  const mascotSize = Math.round(Math.min(280, Math.max(180, height * 0.33)));

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={[
        styles.content,
        { paddingTop: insets.top + 24, paddingBottom: insets.bottom + 16 },
      ]}
      bounces={false}
    >
      <Image
        source={mascot}
        style={{ width: mascotSize, height: mascotSize }}
        accessibilityLabel="Muscle Mom flexing in a striped apron"
      />
      <Text style={styles.title} accessibilityRole="header">
        Muscle Mom
      </Text>
      <Text style={styles.tagline}>
        A week of high-protein meals, planned around your budget and what's in your fridge.
      </Text>

      <View style={styles.spacer} />

      {error ? (
        <Text style={styles.error} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}

      <View style={styles.buttons} pointerEvents={busy ? 'none' : 'auto'}>
        {onApple ? (
          // Apple's own button: Apple requires its sign-in button to follow its guidelines, and
          // this one renders the system artwork and localized label.
          <View style={[styles.appleWrap, busy && busy !== 'apple' && styles.dimmed]}>
            <AppleAuthentication.AppleAuthenticationButton
              buttonType={AppleAuthentication.AppleAuthenticationButtonType.CONTINUE}
              buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
              cornerRadius={14}
              style={styles.appleButton}
              onPress={onApple}
            />
            {busy === 'apple' ? <ActivityIndicator style={styles.appleSpinner} color={colors.white} /> : null}
          </View>
        ) : null}
        {onGoogle ? (
          <AuthButton
            label="Continue with Google"
            icon={busy === 'google' ? <ActivityIndicator color={colors.ink} /> : <GoogleLogo />}
            onPress={onGoogle}
            disabled={busy !== null}
            style={({ pressed }) => [
              styles.button,
              styles.outlined,
              { backgroundColor: pressed ? colors.whitePressed : colors.white },
              busy && busy !== 'google' && styles.dimmed,
            ]}
            textColor={colors.ink}
          />
        ) : null}
        <AuthButton
          label="Continue with email"
          onPress={onEmail}
          disabled={busy !== null}
          style={({ pressed }) => [
            styles.button,
            { backgroundColor: pressed ? colors.tomatoPressed : colors.tomatoDeep },
            busy && styles.dimmed,
          ]}
          textColor={colors.white}
        />
      </View>

      <Text style={styles.legal}>
        By continuing you agree to the{' '}
        <Text style={styles.link} onPress={onTerms} accessibilityRole="link">
          Terms
        </Text>{' '}
        and{' '}
        <Text style={styles.link} onPress={onPrivacy} accessibilityRole="link">
          Privacy Policy
        </Text>
        .
      </Text>
    </ScrollView>
  );
}

type AuthButtonProps = {
  label: string;
  icon?: ReactNode;
  onPress?: () => void;
  disabled?: boolean;
  style: (state: PressableStateCallbackType) => StyleProp<ViewStyle>;
  textColor: string;
};

function AuthButton({ label, icon, onPress, disabled, style, textColor }: AuthButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={style}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
    >
      {icon}
      <Text style={[styles.buttonText, { color: textColor }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.cream,
  },
  content: {
    flexGrow: 1,
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  title: {
    marginTop: 8,
    fontFamily: fonts.bold,
    fontSize: 34,
    lineHeight: 42,
    letterSpacing: -0.5,
    color: colors.ink,
  },
  tagline: {
    marginTop: 8,
    maxWidth: 290,
    textAlign: 'center',
    fontFamily: fonts.regular,
    fontSize: 16,
    lineHeight: 23,
    color: colors.inkMuted,
  },
  spacer: {
    flexGrow: 1,
    minHeight: 32,
  },
  buttons: {
    alignSelf: 'stretch',
    gap: 12,
  },
  button: {
    height: 54,
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  appleWrap: {
    height: 54,
    justifyContent: 'center',
  },
  appleButton: {
    height: 54,
  },
  appleSpinner: {
    position: 'absolute',
    right: 18,
  },
  dimmed: {
    opacity: 0.5,
  },
  error: {
    alignSelf: 'stretch',
    marginBottom: 12,
    textAlign: 'center',
    fontFamily: fonts.regular,
    fontSize: 14,
    lineHeight: 20,
    color: colors.link,
  },
  outlined: {
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  buttonText: {
    fontFamily: fonts.semiBold,
    fontSize: 16,
  },
  legal: {
    marginTop: 20,
    textAlign: 'center',
    fontFamily: fonts.regular,
    fontSize: 12,
    lineHeight: 17,
    color: colors.inkMuted,
  },
  link: {
    color: colors.link,
  },
});
