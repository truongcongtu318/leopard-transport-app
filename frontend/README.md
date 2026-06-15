# LEOPARD — Frontend

LEOPARD is a freight transport platform for Vietnam. Built with **Flutter** and **Clean Architecture**.

## Architecture

```
lib/
├── config/         # App configuration, theming, routing
├── core/           # Shared infrastructure (network, utils, widgets)
├── features/       # Feature modules (auth, booking, tracking, etc.)
│   └── <feature>/
│       ├── data/       # Repositories, data sources
│       ├── domain/     # Models, entities
│       └── presentation/  # BLoC, pages, widgets
└── l10n/           # Localization (Vietnamese)
```

## Getting Started

```bash
# Install dependencies
flutter pub get

# Generate code (freezed, json_serializable)
dart run build_runner build --delete-conflicting-outputs

# Run on device
flutter run
```

## State Management

| Feature        | Library       |
|----------------|---------------|
| Auth           | flutter_bloc  |
| Booking        | flutter_bloc  |
| Tracking       | flutter_bloc  |
| Payment        | flutter_bloc (Cubit) |
| Driver         | flutter_bloc  |
| Dashboard      | flutter_bloc  |
| Notifications  | flutter_bloc  |

## API

Base: `https://api.leopard.vn/api/v1`  
WebSocket: `wss://api.leopard.vn/ws/v1`

## License

Proprietary — All rights reserved.
