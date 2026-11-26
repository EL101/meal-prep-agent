import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { sendEmailCode, verifyEmailCode } from '../auth/providers';
import { colors, fonts } from '../theme';

type Props = {
  onBack: () => void;
};

const CODE_LENGTH = 6;
const looksLikeEmail = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);

// Two steps: send a one-time code to the address, then enter it. Signing in with a new address
// creates the account. On success App.tsx sees the new session and moves on.
export default function EmailSignInScreen({ onBack }: Props) {
  const insets = useSafeAreaInsets();
  const [step, setStep] = useState<'email' | 'code'>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmedEmail = email.trim().toLowerCase();

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Try again.');
    } finally {
      setBusy(false);
    }
  }

  const sendCode = () =>
    run(async () => {
      await sendEmailCode(trimmedEmail);
      setCode('');
      setStep('code');
    });

  const verify = () => run(() => verifyEmailCode(trimmedEmail, code));

  const canSubmit = step === 'email' ? looksLikeEmail(trimmedEmail) : code.length === CODE_LENGTH;

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={[
          styles.content,
          { paddingTop: insets.top + 12, paddingBottom: insets.bottom + 16 },
        ]}
        keyboardShouldPersistTaps="handled"
      >
        <Pressable
          onPress={step === 'code' ? () => setStep('email') : onBack}
          hitSlop={12}
          accessibilityRole="button"
          accessibilityLabel="Back"
          style={styles.back}
        >
          <Text style={styles.backText}>‹ Back</Text>
        </Pressable>

        <Text style={styles.title} accessibilityRole="header">
          {step === 'email' ? 'Continue with email' : 'Check your email'}
        </Text>
        <Text style={styles.subtitle}>
          {step === 'email'
            ? 'We’ll send you a 6-digit code. No password needed.'
            : `Enter the code we sent to ${trimmedEmail}.`}
        </Text>

        {step === 'email' ? (
          <TextInput
            key="email"
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            placeholder="you@example.com"
            placeholderTextColor={colors.inkMuted}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="email"
            textContentType="emailAddress"
            returnKeyType="send"
            onSubmitEditing={() => canSubmit && !busy && sendCode()}
            editable={!busy}
            autoFocus
            accessibilityLabel="Email address"
          />
        ) : (
          <TextInput
            key="code"
            style={[styles.input, styles.codeInput]}
            value={code}
            onChangeText={(text) => setCode(text.replace(/\D/g, '').slice(0, CODE_LENGTH))}
            placeholder="123456"
            placeholderTextColor={colors.inkMuted}
            keyboardType="number-pad"
            autoComplete="one-time-code"
            textContentType="oneTimeCode"
            maxLength={CODE_LENGTH}
            returnKeyType="done"
            onSubmitEditing={() => canSubmit && !busy && verify()}
            editable={!busy}
            autoFocus
            accessibilityLabel="6-digit code"
          />
        )}

        {error ? (
          <Text style={styles.error} accessibilityRole="alert">
            {error}
          </Text>
        ) : null}

        <Pressable
          onPress={step === 'email' ? sendCode : verify}
          disabled={!canSubmit || busy}
          style={({ pressed }) => [
            styles.button,
            { backgroundColor: pressed ? colors.tomatoPressed : colors.tomatoDeep },
            (!canSubmit || busy) && styles.disabled,
          ]}
          accessibilityRole="button"
          accessibilityState={{ disabled: !canSubmit || busy }}
        >
          {busy ? (
            <ActivityIndicator color={colors.white} />
          ) : (
            <Text style={styles.buttonText}>{step === 'email' ? 'Send code' : 'Sign in'}</Text>
          )}
        </Pressable>

        {step === 'code' ? (
          <Pressable onPress={sendCode} disabled={busy} hitSlop={8} style={styles.resend}>
            <Text style={styles.link}>Send a new code</Text>
          </Pressable>
        ) : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.cream,
  },
  content: {
    flexGrow: 1,
    paddingHorizontal: 24,
  },
  back: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
  },
  backText: {
    fontFamily: fonts.semiBold,
    fontSize: 16,
    color: colors.ink,
  },
  title: {
    marginTop: 24,
    fontFamily: fonts.bold,
    fontSize: 28,
    lineHeight: 36,
    letterSpacing: -0.3,
    color: colors.ink,
  },
  subtitle: {
    marginTop: 8,
    fontFamily: fonts.regular,
    fontSize: 16,
    lineHeight: 23,
    color: colors.inkMuted,
  },
  input: {
    marginTop: 28,
    height: 54,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.white,
    paddingHorizontal: 16,
    fontFamily: fonts.regular,
    fontSize: 17,
    color: colors.ink,
  },
  codeInput: {
    fontFamily: fonts.semiBold,
    fontSize: 22,
    letterSpacing: 8,
    textAlign: 'center',
  },
  error: {
    marginTop: 12,
    fontFamily: fonts.regular,
    fontSize: 14,
    lineHeight: 20,
    color: colors.link,
  },
  button: {
    marginTop: 20,
    height: 54,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabled: {
    opacity: 0.5,
  },
  buttonText: {
    fontFamily: fonts.semiBold,
    fontSize: 16,
    color: colors.white,
  },
  resend: {
    alignSelf: 'center',
    marginTop: 20,
  },
  link: {
    fontFamily: fonts.semiBold,
    fontSize: 15,
    color: colors.link,
  },
});
