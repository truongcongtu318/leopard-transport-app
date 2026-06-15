import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:leopard/features/booking/data/booking_repository.dart';
import 'package:leopard/features/booking/domain/order_model.dart';
import 'package:leopard/features/booking/domain/order_stop_model.dart';
import 'package:leopard/features/booking/domain/vehicle_type_enum.dart';
import 'package:leopard/features/booking/presentation/bloc/booking_bloc.dart';
import 'package:leopard/features/booking/presentation/bloc/booking_event.dart';
import 'package:leopard/features/booking/presentation/bloc/booking_state.dart';
import 'package:leopard/core/network/api_exceptions.dart';

class MockBookingRepository extends Mock implements BookingRepository {}

void main() {
  late MockBookingRepository mockRepository;

  final testPickup = OrderStopModel(
    address: '123 Đường Láng, Hà Nội',
    latitude: 21.0285,
    longitude: 105.8542,
    sequence: 0,
  );

  final testDelivery = OrderStopModel(
    address: '456 Nguyễn Trãi, Hà Nội',
    latitude: 21.0073,
    longitude: 105.8252,
    sequence: 1,
  );

  final testStops = [testPickup, testDelivery];

  final testOrder = OrderModel(
    id: 'order-1',
    stops: testStops,
    vehicleType: VehicleType.van,
    cargoWeightKg: 200,
    status: OrderStatus.pending,
    createdAt: DateTime(2025, 1, 1),
    updatedAt: DateTime(2025, 1, 1),
  );

  setUp(() {
    mockRepository = MockBookingRepository();
  });

  group('BookingBloc', () {
    blocTest<BookingBloc, BookingState>(
      'emits [BookingInProgress] when stops changed',
      build: () => BookingBloc(bookingRepository: mockRepository),
      act: (bloc) => bloc.add(BookingStopsChanged(stops: testStops)),
      expect: () => [
        BookingInProgress(stops: testStops, vehicleType: VehicleType.van),
      ],
    );

    blocTest<BookingBloc, BookingState>(
      'emits correct state when vehicle type changed',
      build: () => BookingBloc(bookingRepository: mockRepository),
      act: (bloc) =>
          bloc.add(const BookingVehicleTypeChanged(vehicleType: VehicleType.lightTruck)),
      expect: () => [
        const BookingInProgress(
          stops: [],
          vehicleType: VehicleType.lightTruck,
        ),
      ],
    );

    blocTest<BookingBloc, BookingState>(
      'emits [BookingError] when optimizing with less than 2 stops',
      build: () => BookingBloc(bookingRepository: mockRepository),
      seed: () => BookingInProgress(
        stops: [testPickup],
        vehicleType: VehicleType.van,
      ),
      act: (bloc) => bloc.add(const BookingRouteOptimizeRequested()),
      expect: () => [
        const BookingError(message: 'Cần ít nhất 2 điểm dừng'),
      ],
    );

    blocTest<BookingBloc, BookingState>(
      'emits [BookingOptimizing, BookingOptimized] when route optimization succeeds',
      build: () => BookingBloc(bookingRepository: mockRepository),
      seed: () => BookingInProgress(
        stops: testStops,
        vehicleType: VehicleType.van,
      ),
      setUp: () {
        when(
          () => mockRepository.optimizeRoute(
            stops: any(named: 'stops'),
            vehicleType: any(named: 'vehicleType'),
          ),
        ).thenAnswer((_) async => testStops);
      },
      act: (bloc) => bloc.add(const BookingRouteOptimizeRequested()),
      expect: () => [
        isA<BookingOptimizing>(),
        isA<BookingOptimized>(),
      ],
    );

    blocTest<BookingBloc, BookingState>(
      'emits [BookingError] when route optimization fails',
      build: () => BookingBloc(bookingRepository: mockRepository),
      seed: () => BookingInProgress(
        stops: testStops,
        vehicleType: VehicleType.van,
      ),
      setUp: () {
        when(
          () => mockRepository.optimizeRoute(
            stops: any(named: 'stops'),
            vehicleType: any(named: 'vehicleType'),
          ),
        ).thenThrow(
          const NetworkException(message: 'Network error'),
        );
      },
      act: (bloc) => bloc.add(const BookingRouteOptimizeRequested()),
      expect: () => [
        isA<BookingOptimizing>(),
        isA<BookingError>(),
      ],
    );

    blocTest<BookingBloc, BookingState>(
      'emits [BookingSubmitting, BookingCreated] when booking is created',
      build: () => BookingBloc(bookingRepository: mockRepository),
      seed: () => BookingInProgress(
        stops: testStops,
        vehicleType: VehicleType.van,
      ),
      setUp: () {
        when(
          () => mockRepository.createBooking(
            stops: any(named: 'stops'),
            vehicleType: any(named: 'vehicleType'),
            cargoWeightKg: any(named: 'cargoWeightKg'),
            cargoDescription: any(named: 'cargoDescription'),
            specialInstructions: any(named: 'specialInstructions'),
          ),
        ).thenAnswer((_) async => testOrder);
      },
      act: (bloc) => bloc.add(
        const BookingSubmitRequested(cargoWeightKg: 200),
      ),
      expect: () => [
        const BookingSubmitting(),
        BookingCreated(order: testOrder),
      ],
    );

    blocTest<BookingBloc, BookingState>(
      'emits [BookingError] when booking creation fails',
      build: () => BookingBloc(bookingRepository: mockRepository),
      seed: () => BookingInProgress(
        stops: testStops,
        vehicleType: VehicleType.van,
      ),
      setUp: () {
        when(
          () => mockRepository.createBooking(
            stops: any(named: 'stops'),
            vehicleType: any(named: 'vehicleType'),
            cargoWeightKg: any(named: 'cargoWeightKg'),
            cargoDescription: any(named: 'cargoDescription'),
            specialInstructions: any(named: 'specialInstructions'),
          ),
        ).thenThrow(
          const ValidationException(
            message: 'Invalid data',
            fieldErrors: {},
          ),
        );
      },
      act: (bloc) => bloc.add(
        const BookingSubmitRequested(cargoWeightKg: 200),
      ),
      expect: () => [
        const BookingSubmitting(),
        isA<BookingError>(),
      ],
    );

    blocTest<BookingBloc, BookingState>(
      'emits [BookingInitial] on reset',
      build: () => BookingBloc(bookingRepository: mockRepository),
      seed: () => BookingInProgress(
        stops: testStops,
        vehicleType: VehicleType.van,
      ),
      act: (bloc) => bloc.add(const BookingReset()),
      expect: () => [
        const BookingInitial(),
      ],
    );
  });
}
