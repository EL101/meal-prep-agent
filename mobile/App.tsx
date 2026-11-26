// Import each weight on its own so only these three font files ship with the app.
import { DMSans_400Regular } from '@expo-google-fonts/dm-sans/400Regular';
import { DMSans_600SemiBold } from '@expo-google-fonts/dm-sans/600SemiBold';
import { DMSans_700Bold } from '@expo-google-fonts/dm-sans/700Bold';
import { useFonts } from 'expo-font';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import SignInScreen from './src/screens/SignInScreen';
import { colors } from './src/theme';

export default function App() {
  const [fontsLoaded] = useFonts({
    DMSans_400Regular,
    DMSans_600SemiBold,
    DMSans_700Bold,
  });

  if (!fontsLoaded) {
    // Fonts load in a few milliseconds; show the cream background until then.
    return <View style={{ flex: 1, backgroundColor: colors.cream }} />;
  }

  return (
    <SafeAreaProvider>
      <SignInScreen />
      <StatusBar style="dark" />
    </SafeAreaProvider>
  );
}
