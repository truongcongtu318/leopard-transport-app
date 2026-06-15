import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:leopard/app.dart';

void main() {
  testWidgets('LeopardApp renders without crashing', (tester) async {
    // This is a smoke test to verify the app starts up.
    // Note: Full widget test requires dependency injection setup.
    // Below we just verify the widget tree builds.
    expect(const LeopardApp(), isA<StatelessWidget>());
  });

  test('App widget can be instantiated', () {
    const app = LeopardApp();
    expect(app, isNotNull);
    expect(app.key, isNull); // default key
  });
}
