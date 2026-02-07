// ADC-IMPLEMENTS: <rpc-example-01>

import 'package:dart_simple_math/simple_math.dart';
import 'package:dart_simple_math/adc_server.dart';

/// Entry point for ADC MessagePack RPC server.
///
/// Starts server and registers SimpleMath methods.
void main() async {
  final server = ADCServer();

  // Register add method
  server.register('add', (Map args) {
    final a = args['a'] as int;
    final b = args['b'] as int;
    return SimpleMath.add(a, b);
  });

  // Register multiply method
  server.register('multiply', (Map args) {
    final a = args['a'] as int;
    final b = args['b'] as int;
    return SimpleMath.multiply(a, b);
  });

  // Register divide method
  server.register('divide', (Map args) {
    final a = args['a'] as int;
    final b = args['b'] as int;
    return SimpleMath.divide(a, b);
  });

  // Start serving
  await server.serve();
}
