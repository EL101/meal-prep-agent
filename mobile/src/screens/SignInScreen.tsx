import type { ReactNode } from 'react';
import {
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

import { AppleLogo, GoogleLogo } from '../components/BrandIcons';
import { colors, fonts } from '../theme';

const mascot = require('../../assets/mascot.png');

type Props = {
  onApple?: () => void;
  onGoogle?: () => void;
  onEmail?: () => void;
  onTerms?: () => void;
  onPrivacy?: () => void;
};

export default function SignInScreen({ onApple, onGoogle, onEmail, onTerms, onPrivacy }: Props) {
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

      <View style={styles.buttons}>
        <AuthButton
          label="Continue with Apple"
          icon={<AppleLogo />}
          onPress={onApple}
          style={({ pressed }) => [styles.button, { backgroundColor: pressed ? colors.blackPressed : colors.black }]}
          textColor={colors.white}
        />
        <AuthButton
          label="Continue with Google"
          icon={<GoogleLogo />}
          onPress={onGoogle}
          style={({ pressed }) => [
            styles.button,
            styles.outlined,
            { backgroundColor: pressed ? colors.whitePressed : colors.white },
          ]}
          textColor={colors.ink}
        />
        <AuthButton
          label="Continue with email"
          onPress={onEmail}
          style={({ pressed }) => [styles.button, { backgroundColor: pressed ? colors.tomatoPressed : colors.tomatoDeep }]}
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
  style: (state: PressableStateCallbackType) => StyleProp<ViewStyle>;
  textColor: string;
};

function AuthButton({ label, icon, onPress, style, textColor }: AuthButtonProps) {
  return (
    <Pressable onPress={onPress} style={style} accessibilityRole="button" accessibilityLabel={label}>
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
