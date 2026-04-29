import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'screens/overview_screen.dart';
import 'screens/subsystem_screen.dart';
import 'screens/compare_screen.dart';
import 'screens/alerts_screen.dart';
import 'screens/settings_screen.dart';

final goRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const OverviewScreen(),
    ),
    GoRoute(
      path: '/subsystem/:name',
      builder: (context, state) {
        final name = state.pathParameters['name']!;
        return SubsystemScreen(subsystem: name);
      },
    ),
    GoRoute(
      path: '/compare',
      builder: (context, state) => const CompareScreen(),
    ),
    GoRoute(
      path: '/alerts',
      builder: (context, state) => const AlertsScreen(),
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
  ],
);
