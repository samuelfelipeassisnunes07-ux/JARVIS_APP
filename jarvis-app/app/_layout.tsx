import { DarkTheme, DefaultTheme, ThemeProvider as NavigationThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';
import { ThemeProvider, useTheme } from '../context/ThemeContext';

export const unstable_settings = {
  anchor: '(tabs)',
};

function RootLayoutContent() {
  const { darkMode } = useTheme();

  const CustomDarkTheme = {
    ...DarkTheme,
    colors: {
      ...DarkTheme.colors,
      primary: '#818cf8',
      background: '#111827',
      card: '#1f2937',
      text: '#f9fafb',
      border: '#374151',
    },
  };

  const CustomLightTheme = {
    ...DefaultTheme,
    colors: {
      ...DefaultTheme.colors,
      primary: '#6366f1',
      background: '#f3f4f6',
      card: '#ffffff',
      text: '#1f2937',
      border: '#e5e7eb',
    },
  };

  return (
    <NavigationThemeProvider value={darkMode ? CustomDarkTheme : CustomLightTheme}>
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: darkMode ? '#1f2937' : '#ffffff',
          },
          headerTintColor: darkMode ? '#f9fafb' : '#1f2937',
          headerTitleStyle: {
            fontWeight: '600',
          },
          contentStyle: {
            backgroundColor: darkMode ? '#111827' : '#f3f4f6',
          },
        }}
      >
        <Stack.Screen 
          name="(tabs)" 
          options={{ 
            headerShown: false,
            title: 'Jarvis'
          }} 
        />
        <Stack.Screen 
          name="modal" 
          options={{ 
            presentation: 'modal',
            title: 'Configurações',
            headerLeft: () => null,
          }} 
        />
      </Stack>
      <StatusBar style={darkMode ? 'light' : 'dark'} />
    </NavigationThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <ThemeProvider>
      <RootLayoutContent />
    </ThemeProvider>
  );
}