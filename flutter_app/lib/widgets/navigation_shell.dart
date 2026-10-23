import 'package:flutter/material.dart';
import '../screens/dashboard_screen.dart';
import '../screens/environment_screen.dart';
import '../screens/physiology_screen.dart';
import '../screens/explanation_screen.dart';
import '../screens/history_screen.dart';
import '../screens/ble_device_screen.dart';
import '../constants.dart';

class NavigationShell extends StatefulWidget {
  const NavigationShell({super.key});

  @override
  State<NavigationShell> createState() => _NavigationShellState();
}

class _NavigationShellState extends State<NavigationShell> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    DashboardScreen(),
    EnvironmentScreen(),
    PhysiologyScreen(),
    ExplanationScreen(),
    HistoryScreen(),
    BleDeviceScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) => setState(() => _currentIndex = idx),
        indicatorColor: AppColors.primary.withValues(alpha: 0.25),
        labelBehavior: NavigationDestinationLabelBehavior.onlyShowSelected,
        height: 65,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard_rounded, color: AppColors.primaryLight),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.cloud_outlined),
            selectedIcon: Icon(Icons.cloud_rounded, color: AppColors.primaryLight),
            label: 'Environment',
          ),
          NavigationDestination(
            icon: Icon(Icons.favorite_outline_rounded),
            selectedIcon: Icon(Icons.favorite_rounded, color: AppColors.primaryLight),
            label: 'Physiology',
          ),
          NavigationDestination(
            icon: Icon(Icons.psychology_outlined),
            selectedIcon: Icon(Icons.psychology_rounded, color: AppColors.primaryLight),
            label: 'SHAP XAI',
          ),
          NavigationDestination(
            icon: Icon(Icons.show_chart_rounded),
            selectedIcon: Icon(Icons.show_chart_rounded, color: AppColors.primaryLight),
            label: 'History',
          ),
          NavigationDestination(
            icon: Icon(Icons.bluetooth_rounded),
            selectedIcon: Icon(Icons.bluetooth_connected_rounded, color: AppColors.primaryLight),
            label: 'BLE Device',
          ),
        ],
      ),
    );
  }
}
