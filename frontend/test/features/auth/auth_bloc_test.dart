import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:leopard/features/auth/domain/user_model.dart';
import 'package:leopard/features/auth/data/auth_repository.dart';
import 'package:leopard/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:leopard/features/auth/presentation/bloc/auth_event.dart';
import 'package:leopard/features/auth/presentation/bloc/auth_state.dart';
import 'package:leopard/core/network/api_exceptions.dart';

class MockAuthRepository extends Mock implements AuthRepository {}

void main() {
  late MockAuthRepository mockAuthRepository;

  final testUser = UserModel(
    id: 'user-1',
    phone: '+84123456789',
    fullName: 'Nguyen Van A',
    role: UserRole.shipper,
    createdAt: DateTime(2025, 1, 1),
    updatedAt: DateTime(2025, 1, 1),
  );

  setUp(() {
    mockAuthRepository = MockAuthRepository();
  });

  group('AuthBloc', () {
    blocTest<AuthBloc, AuthState>(
      'emits [AuthLoading, AuthAuthenticated] when check succeeds',
      build: () => AuthBloc(authRepository: mockAuthRepository),
      setUp: () {
        when(() => mockAuthRepository.isAuthenticated())
            .thenAnswer((_) async => true);
        when(() => mockAuthRepository.getProfile())
            .thenAnswer((_) async => testUser);
      },
      act: (bloc) => bloc.add(const AuthCheckRequested()),
      expect: () => [
        const AuthLoading(),
        AuthAuthenticated(user: testUser),
      ],
    );

    blocTest<AuthBloc, AuthState>(
      'emits [AuthLoading, AuthUnauthenticated] when check fails',
      build: () => AuthBloc(authRepository: mockAuthRepository),
      setUp: () {
        when(() => mockAuthRepository.isAuthenticated())
            .thenAnswer((_) async => false);
      },
      act: (bloc) => bloc.add(const AuthCheckRequested()),
      expect: () => [
        const AuthLoading(),
        const AuthUnauthenticated(),
      ],
    );

    blocTest<AuthBloc, AuthState>(
      'emits [AuthLoading, AuthOtpSent] when OTP requested',
      build: () => AuthBloc(authRepository: mockAuthRepository),
      setUp: () {
        when(
          () => mockAuthRepository.requestPhoneOtp(any()),
        ).thenAnswer((_) async {});
      },
      act: (bloc) => bloc.add(
        const AuthPhoneOtpRequested(phoneNumber: '0987654321'),
      ),
      expect: () => [
        const AuthLoading(),
        const AuthOtpSent(phoneNumber: '0987654321'),
      ],
    );

    blocTest<AuthBloc, AuthState>(
      'emits [AuthLoading, AuthError] when OTP request fails',
      build: () => AuthBloc(authRepository: mockAuthRepository),
      setUp: () {
        when(
          () => mockAuthRepository.requestPhoneOtp(any()),
        ).thenThrow(
          const BadRequestException(message: 'Invalid phone'),
        );
      },
      act: (bloc) => bloc.add(
        const AuthPhoneOtpRequested(phoneNumber: '123'),
      ),
      expect: () => [
        const AuthLoading(),
        const AuthError(message: 'Invalid phone'),
      ],
    );

    blocTest<AuthBloc, AuthState>(
      'emits [AuthLoading, AuthUnauthenticated] on logout',
      build: () => AuthBloc(authRepository: mockAuthRepository),
      setUp: () {
        when(() => mockAuthRepository.logout()).thenAnswer((_) async {});
      },
      act: (bloc) => bloc.add(const AuthLogoutRequested()),
      expect: () => [
        const AuthLoading(),
        const AuthUnauthenticated(),
      ],
    );

    blocTest<AuthBloc, AuthState>(
      'emits [AuthLoading, AuthError] when registration fails',
      build: () => AuthBloc(authRepository: mockAuthRepository),
      setUp: () {
        when(
          () => mockAuthRepository.register(
            phone: any(named: 'phone'),
            fullName: any(named: 'fullName'),
            role: any(named: 'role'),
            email: any(named: 'email'),
          ),
        ).thenThrow(
          const ServerException(message: 'Server error'),
        );
      },
      act: (bloc) => bloc.add(
        const AuthRegisterRequested(
          phone: '0987654321',
          fullName: 'Test User',
          role: 'shipper',
        ),
      ),
      expect: () => [
        const AuthLoading(),
        const AuthError(message: 'Server error'),
      ],
    );
  });
}
