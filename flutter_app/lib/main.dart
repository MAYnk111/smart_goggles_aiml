import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'constants.dart';
import 'providers/app_state.dart';
import 'screens/splash_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const SmartGoggleApp());
}

class SmartGoggleApp extends StatelessWidget {
  const SmartGoggleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(),
      child: Consumer<AppState>(
        builder: (context, appState, _) {
          return MaterialApp(
            title: 'Smart Goggle Monitoring',
            debugShowCheckedModeBanner: false,
            themeMode: appState.isDarkMode ? ThemeMode.dark : ThemeMode.light,
            theme: ThemeData(
              useMaterial3: true,
              brightness: Brightness.light,
              colorSchemeSeed: AppColors.primary,
              scaffoldBackgroundColor: const Color(0xFFF8FAFC),
              cardColor: Colors.white,
              appBarTheme: const AppBarTheme(
                backgroundColor: Colors.white,
                elevation: 0,
                scrolledUnderElevation: 0,
                titleTextStyle: TextStyle(
                  color: Color(0xFF0F172A),
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                ),
                iconTheme: IconThemeData(color: Color(0xFF0F172A)),
              ),
              navigationBarTheme: NavigationBarThemeData(
                backgroundColor: Colors.white,
                elevation: 4,
                labelTextStyle: WidgetStateProperty.resolveWith((states) {
                  if (states.contains(WidgetState.selected)) {
                    return const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                    );
                  }
                  return const TextStyle(fontSize: 11, color: Colors.grey);
                }),
              ),
            ),
            darkTheme: ThemeData(
              useMaterial3: true,
              brightness: Brightness.dark,
              colorSchemeSeed: AppColors.primary,
              scaffoldBackgroundColor: AppColors.darkBackground,
              cardColor: AppColors.darkCard,
              appBarTheme: const AppBarTheme(
                backgroundColor: AppColors.darkBackground,
                elevation: 0,
                scrolledUnderElevation: 0,
                titleTextStyle: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                ),
                iconTheme: IconThemeData(color: Colors.white),
              ),
              navigationBarTheme: NavigationBarThemeData(
                backgroundColor: const Color(0xFF1E293B),
                elevation: 8,
                labelTextStyle: WidgetStateProperty.resolveWith((states) {
                  if (states.contains(WidgetState.selected)) {
                    return const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primaryLight,
                    );
                  }
                  return const TextStyle(fontSize: 11, color: Colors.grey);
                }),
              ),
            ),
            home: const SplashScreen(),
          );
        },
      ),
    );
  }
}
