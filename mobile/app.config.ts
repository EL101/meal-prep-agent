import type { ConfigContext, ExpoConfig } from 'expo/config';

// Extends app.json. Google Sign-In on iOS needs the reversed iOS client ID registered as a URL
// scheme, so it's derived here from EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID instead of hard-coded.
// Without that variable the plugin is skipped and the Google button stays hidden on iOS.
export default ({ config }: ConfigContext): ExpoConfig => {
  const iosClientId = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID;
  const plugins: ExpoConfig['plugins'] = [...(config.plugins ?? [])];
  if (iosClientId) {
    const prefix = iosClientId.replace(/\.apps\.googleusercontent\.com$/, '');
    plugins.push([
      '@react-native-google-signin/google-signin',
      { iosUrlScheme: `com.googleusercontent.apps.${prefix}` },
    ]);
  }
  return { ...config, name: config.name ?? 'Muscle Mom', slug: config.slug ?? 'mobile', plugins };
};
