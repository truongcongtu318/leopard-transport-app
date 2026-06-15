import 'dart:async';

import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:leopard/features/tracking/data/tracking_repository.dart';
import 'package:leopard/features/tracking/domain/driver_location_model.dart';
import 'package:leopard/features/tracking/presentation/bloc/tracking_bloc.dart';
import 'package:leopard/features/tracking/presentation/bloc/tracking_event.dart';
import 'package:leopard/features/tracking/presentation/bloc/tracking_state.dart';

class MockTrackingRepository extends Mock implements TrackingRepository {}

void main() {
  late MockTrackingRepository mockRepository;

  setUp(() {
    mockRepository = MockTrackingRepository();
  });

  group('TrackingBloc', () {
    blocTest<TrackingBloc, TrackingState>(
      'emits [TrackingConnecting, TrackingActive] on connect success',
      build: () => TrackingBloc(repository: mockRepository),
      setUp: () {
        when(() => mockRepository.connect()).thenAnswer((_) async {});
        when(() => mockRepository.watchDriverLocation(any()))
            .thenAnswer((_) => const Stream<DriverLocationModel>.empty());
        when(() => mockRepository.watchEtaUpdates(any()))
            .thenAnswer((_) => const Stream<Map<String, dynamic>>.empty());
        when(() => mockRepository.watchBookingStatus(any()))
            .thenAnswer((_) => const Stream<Map<String, dynamic>>.empty());
      },
      act: (bloc) => bloc.add(
        const TrackingConnectRequested(bookingId: 'booking-1'),
      ),
      expect: () => [
        const TrackingConnecting(),
        isA<TrackingActive>(),
      ],
      verify: (_) {
        verify(() => mockRepository.connect()).called(1);
        verify(() => mockRepository.watchDriverLocation('booking-1'))
            .called(1);
        verify(() => mockRepository.watchEtaUpdates('booking-1')).called(1);
        verify(() => mockRepository.watchBookingStatus('booking-1'))
            .called(1);
      },
    );

    blocTest<TrackingBloc, TrackingState>(
      'emits [TrackingConnecting, TrackingError] on connect failure',
      build: () => TrackingBloc(repository: mockRepository),
      setUp: () {
        when(() => mockRepository.connect()).thenThrow(Exception('fail'));
      },
      act: (bloc) => bloc.add(
        const TrackingConnectRequested(bookingId: 'booking-1'),
      ),
      expect: () => [
        const TrackingConnecting(),
        isA<TrackingError>(),
      ],
    );

    blocTest<TrackingBloc, TrackingState>(
      'emits updated state when ETA updated',
      build: () => TrackingBloc(repository: mockRepository),
      seed: () => const TrackingActive(bookingId: 'booking-1'),
      act: (bloc) => bloc.add(
        const TrackingEtaUpdated(
          nextStopId: 'stop-2',
          etaArrivalTime: '14:30',
          remainingDistanceMeters: 5000,
          remainingDurationMinutes: 15,
        ),
      ),
      expect: () => [
        isA<TrackingActive>()
            .having((s) => s.nextStopId, 'nextStopId', 'stop-2')
            .having(
                (s) => s.etaArrivalTime, 'etaArrivalTime', '14:30')
            .having((s) => s.remainingDistanceMeters,
                'remainingDistanceMeters', 5000)
            .having((s) => s.remainingDurationMinutes,
                'remainingDurationMinutes', 15),
      ],
    );

    blocTest<TrackingBloc, TrackingState>(
      'emits updated status when status changes',
      build: () => TrackingBloc(repository: mockRepository),
      seed: () => const TrackingActive(bookingId: 'booking-1'),
      act: (bloc) => bloc.add(
        TrackingStatusChanged(
          status: 'in_transit',
          currentStopSequence: 1,
          updatedAt: DateTime(2025, 6, 15),
        ),
      ),
      expect: () => [
        isA<TrackingActive>()
            .having(
                (s) => s.bookingStatus, 'bookingStatus', 'in_transit')
            .having(
                (s) => s.currentStopSequence, 'currentStopSequence', 1),
      ],
    );

    blocTest<TrackingBloc, TrackingState>(
      'emits [TrackingDisconnected] on disconnect',
      build: () => TrackingBloc(repository: mockRepository),
      seed: () => const TrackingActive(bookingId: 'booking-1'),
      setUp: () {
        when(() => mockRepository.disconnect()).thenAnswer((_) async {});
      },
      act: (bloc) => bloc.add(const TrackingDisconnectRequested()),
      expect: () => [
        const TrackingDisconnected(),
      ],
      verify: (_) {
        verify(() => mockRepository.disconnect()).called(1);
      },
    );

    test('close cancels subscriptions and disconnects', () async {
      when(() => mockRepository.disconnect()).thenAnswer((_) async {});

      final bloc = TrackingBloc(repository: mockRepository);
      await bloc.close();

      verify(() => mockRepository.disconnect()).called(1);
    });
  });
}
