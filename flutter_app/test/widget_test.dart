import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/main.dart';

void main() {
  testWidgets('Smart Goggle App splash and navigation test', (WidgetTester tester) async {
    await tester.pumpWidget(const SmartGoggleApp());
    await tester.pump();
    expect(find.text('SMART GOGGLE'), findsOneWidget);

    // Advance past splash transition
    await tester.pump(const Duration(milliseconds: 3000));
    await tester.pump(const Duration(milliseconds: 700));

    // Verify main navigation destination rendered
    expect(find.text('Dashboard'), findsWidgets);
  });
}
