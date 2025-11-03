# 🛠️ MindBridge Flutter - Setup Guide

## Voraussetzungen

### System Requirements
- **macOS** (für iOS-Entwicklung) oder **Windows/Linux** (nur Android)
- **8GB RAM** minimum (16GB empfohlen)
- **10GB freier Speicher**
- **Git** installiert

---

## 1️⃣ Flutter SDK Installation

### macOS
```bash
# Flutter SDK herunterladen
cd ~/development
git clone https://github.com/flutter/flutter.git -b stable

# Path hinzufügen
echo 'export PATH="$PATH:$HOME/development/flutter/bin"' >> ~/.zshrc
source ~/.zshrc

# Installation verifizieren
flutter doctor
```

### Windows
```powershell
# Download Flutter SDK von https://docs.flutter.dev/get-started/install/windows
# Entpacken nach C:\flutter

# Path in System Environment Variables hinzufügen
# PATH += C:\flutter\bin

# Installation verifizieren
flutter doctor
```

### Linux
```bash
# Flutter SDK herunterladen
cd ~/development
git clone https://github.com/flutter/flutter.git -b stable

# Path hinzufügen
echo 'export PATH="$PATH:$HOME/development/flutter/bin"' >> ~/.bashrc
source ~/.bashrc

# Installation verifizieren
flutter doctor
```

---

## 2️⃣ IDE Setup

### VS Code (Empfohlen)
```bash
# VS Code installieren: https://code.visualstudio.com/

# Flutter Extension installieren
code --install-extension Dart-Code.flutter
code --install-extension Dart-Code.dart-code

# Weitere hilfreiche Extensions
code --install-extension alexisvt.flutter-snippets
code --install-extension Nash.awesome-flutter-snippets
code --install-extension pflannery.vscode-versionlens
code --install-extension esbenp.prettier-vscode
```

**VS Code Settings** (`settings.json`):
```json
{
  "dart.flutterSdkPath": "/Users/yourname/development/flutter",
  "editor.formatOnSave": true,
  "editor.rulers": [80, 120],
  "[dart]": {
    "editor.formatOnSave": true,
    "editor.formatOnType": true,
    "editor.rulers": [80],
    "editor.selectionHighlight": false,
    "editor.suggest.snippetsPreventQuickSuggestions": false,
    "editor.suggestSelection": "first",
    "editor.tabCompletion": "onlySnippets",
    "editor.wordBasedSuggestions": false
  }
}
```

### Android Studio (Alternative)
- Download: https://developer.android.com/studio
- Flutter Plugin installieren: `Settings → Plugins → Flutter`
- Dart Plugin wird automatisch installiert

---

## 3️⃣ Android Setup

### Android SDK installieren
```bash
# Android Studio öffnen → SDK Manager
# Installiere:
# - Android SDK Platform 33 (Android 13)
# - Android SDK Build-Tools
# - Android Emulator
# - Android SDK Platform-Tools
```

### Android Emulator erstellen
```bash
# AVD Manager öffnen (Android Studio)
# Create Virtual Device → Pixel 6 → System Image (API 33) → Finish

# Emulator starten
flutter emulators --launch Pixel_6_API_33
```

### Android Licenses akzeptieren
```bash
flutter doctor --android-licenses
# Alle Licenses mit 'y' akzeptieren
```

---

## 4️⃣ iOS Setup (nur macOS)

### Xcode installieren
```bash
# Xcode aus App Store installieren (ca. 12GB)
# oder via Terminal:
xcode-select --install

# Xcode Command Line Tools
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch

# Licenses akzeptieren
sudo xcodebuild -license accept
```

### CocoaPods installieren
```bash
# CocoaPods (iOS Dependency Manager)
sudo gem install cocoapods
pod setup
```

### iOS Simulator starten
```bash
# Simulator öffnen
open -a Simulator

# Oder via Flutter
flutter emulators --launch apple_ios_simulator
```

---

## 5️⃣ Projekt initialisieren

### Neues Flutter-Projekt erstellen
```bash
# In dein Workspace-Verzeichnis wechseln
cd /path/to/workspace

# Flutter-Projekt erstellen
flutter create mindbridge_flutter --org com.mindbridge

# In Projekt-Verzeichnis wechseln
cd mindbridge_flutter

# Projekt öffnen
code .
```

### Projektstruktur anpassen
```bash
# Verzeichnisse erstellen
mkdir -p lib/{core,features,shared}
mkdir -p lib/core/{config,constants,errors,network,services,utils}
mkdir -p lib/features/{auth,mood,dreams,therapy,analytics,chat,settings}
mkdir -p lib/shared/{widgets,models,extensions}
mkdir -p assets/{images,icons,animations,translations}
mkdir -p test/{unit,widget,integration}
```

---

## 6️⃣ Dependencies hinzufügen

### pubspec.yaml konfigurieren
```yaml
name: mindbridge_flutter
description: MindBridge Mental Health Platform
version: 1.0.0+1

environment:
  sdk: '>=3.2.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_riverpod: ^2.5.1
  riverpod_annotation: ^2.3.5

  # Navigation
  go_router: ^14.0.0

  # Networking
  dio: ^5.4.0
  retrofit: ^4.0.3
  json_annotation: ^4.8.1

  # Local Storage
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  drift: ^2.16.0
  sqlite3_flutter_libs: ^0.5.20

  # Encryption & Security
  flutter_secure_storage: ^9.0.0
  cryptography: ^2.7.0
  encrypt: ^5.0.3

  # Authentication
  local_auth: ^2.2.0
  firebase_auth: ^4.16.0
  google_sign_in: ^6.2.1
  sign_in_with_apple: ^5.0.0

  # Push Notifications
  firebase_messaging: ^14.7.9
  flutter_local_notifications: ^17.0.0

  # UI/UX
  fl_chart: ^0.68.0
  animations: ^2.0.11
  shimmer: ^3.0.0
  lottie: ^3.1.0
  cached_network_image: ^3.3.1

  # Forms & Validation
  formz: ^0.7.0

  # Utils
  intl: ^0.19.0
  shared_preferences: ^2.2.2
  path_provider: ^2.1.2
  image_picker: ^1.0.7
  url_launcher: ^6.2.4
  package_info_plus: ^5.0.1
  device_info_plus: ^9.1.1

  # Date/Time
  timeago: ^3.6.0

  # Analytics & Monitoring
  firebase_analytics: ^10.8.0
  firebase_crashlytics: ^3.4.9
  sentry_flutter: ^7.18.0

  # Development
  flutter_launcher_icons: ^0.13.1
  flutter_native_splash: ^2.3.10

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1

  # Code Generation
  build_runner: ^2.4.8
  retrofit_generator: ^8.0.6
  json_serializable: ^6.7.1
  riverpod_generator: ^2.3.11
  hive_generator: ^2.0.1
  drift_dev: ^2.16.0

  # Testing
  mockito: ^5.4.4
  faker: ^2.1.0
  integration_test:
    sdk: flutter

flutter:
  uses-material-design: true

  assets:
    - assets/images/
    - assets/icons/
    - assets/animations/
    - assets/translations/

  fonts:
    - family: Inter
      fonts:
        - asset: assets/fonts/Inter-Regular.ttf
        - asset: assets/fonts/Inter-Medium.ttf
          weight: 500
        - asset: assets/fonts/Inter-Bold.ttf
          weight: 700
```

### Dependencies installieren
```bash
flutter pub get
```

---

## 7️⃣ Firebase Setup

### Firebase Projekt erstellen
1. Gehe zu [Firebase Console](https://console.firebase.google.com/)
2. Erstelle neues Projekt "MindBridge"
3. Aktiviere Google Analytics (optional)

### Firebase CLI installieren
```bash
# Node.js muss installiert sein
npm install -g firebase-tools

# Firebase Login
firebase login

# FlutterFire CLI installieren
dart pub global activate flutterfire_cli

# Firebase in Flutter-Projekt konfigurieren
flutterfire configure
# Wähle dein Firebase-Projekt
# Wähle Plattformen: iOS, Android
```

### Firebase Services aktivieren
- **Authentication**: Email/Password, Google, Apple
- **Cloud Messaging**: Push Notifications
- **Crashlytics**: Crash Reporting
- **Analytics**: User Analytics

---

## 8️⃣ Code Generation Setup

### build_runner konfigurieren
```bash
# Code generieren (JSON Serialization, Retrofit, Riverpod, etc.)
flutter pub run build_runner build --delete-conflicting-outputs

# Watch mode (auto-regenerate on file changes)
flutter pub run build_runner watch --delete-conflicting-outputs
```

### Makefile erstellen (optional, aber praktisch)
```makefile
# Makefile
.PHONY: help get clean build watch test

help:
	@echo "Available commands:"
	@echo "  make get     - Get dependencies"
	@echo "  make build   - Run code generation"
	@echo "  make watch   - Run code generation in watch mode"
	@echo "  make clean   - Clean build files"
	@echo "  make test    - Run all tests"

get:
	flutter pub get

build:
	flutter pub run build_runner build --delete-conflicting-outputs

watch:
	flutter pub run build_runner watch --delete-conflicting-outputs

clean:
	flutter clean
	flutter pub get

test:
	flutter test --coverage
```

Usage:
```bash
make get    # Dependencies installieren
make build  # Code generieren
make watch  # Watch mode
```

---

## 9️⃣ App Icons & Splash Screen

### App Icon konfigurieren
```yaml
# pubspec.yaml
flutter_launcher_icons:
  android: true
  ios: true
  image_path: "assets/icons/app_icon.png"
  adaptive_icon_background: "#3B82F6"
  adaptive_icon_foreground: "assets/icons/app_icon_foreground.png"
```

```bash
# Icon generieren
flutter pub run flutter_launcher_icons
```

### Splash Screen konfigurieren
```yaml
# pubspec.yaml
flutter_native_splash:
  color: "#3B82F6"
  image: assets/images/splash_logo.png
  android_12:
    image: assets/images/splash_logo_android12.png
    color: "#3B82F6"
  ios: true
  android: true
```

```bash
# Splash Screen generieren
flutter pub run flutter_native_splash:create
```

---

## 🔟 Environment Configuration

### Environment Files erstellen
```bash
# .env.development
API_BASE_URL=http://localhost:8080/api/v1
API_TIMEOUT=30000
ENABLE_LOGGING=true
SENTRY_DSN=your_dev_sentry_dsn

# .env.staging
API_BASE_URL=https://staging-api.mindbridge.com/api/v1
API_TIMEOUT=30000
ENABLE_LOGGING=true
SENTRY_DSN=your_staging_sentry_dsn

# .env.production
API_BASE_URL=https://api.mindbridge.com/api/v1
API_TIMEOUT=30000
ENABLE_LOGGING=false
SENTRY_DSN=your_prod_sentry_dsn
```

### flutter_dotenv Setup
```yaml
# pubspec.yaml
dependencies:
  flutter_dotenv: ^5.1.0

flutter:
  assets:
    - .env.development
    - .env.staging
    - .env.production
```

### Config laden
```dart
// lib/core/config/env.dart
import 'package:flutter_dotenv/flutter_dotenv.dart';

class Env {
  static String get apiBaseUrl => dotenv.env['API_BASE_URL']!;
  static int get apiTimeout => int.parse(dotenv.env['API_TIMEOUT']!);
  static bool get enableLogging => dotenv.env['ENABLE_LOGGING'] == 'true';
  static String get sentryDsn => dotenv.env['SENTRY_DSN']!;
}

// main.dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load environment
  await dotenv.load(fileName: ".env.development");

  runApp(MyApp());
}
```

---

## 1️⃣1️⃣ App starten

### Development Mode
```bash
# Android
flutter run -d android

# iOS
flutter run -d ios

# Emulator auswählen
flutter devices
flutter run -d <device-id>
```

### Build & Release

#### Android APK
```bash
# Debug Build
flutter build apk --debug

# Release Build
flutter build apk --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

#### Android App Bundle (für Google Play)
```bash
flutter build appbundle --release

# Output: build/app/outputs/bundle/release/app-release.aab
```

#### iOS IPA
```bash
# Xcode öffnen
open ios/Runner.xcworkspace

# In Xcode: Product → Archive → Distribute App

# Oder via CLI
flutter build ipa --release
```

---

## 1️⃣2️⃣ Testing

### Unit Tests
```bash
flutter test test/unit/
```

### Widget Tests
```bash
flutter test test/widget/
```

### Integration Tests
```bash
# Android
flutter test integration_test/app_test.dart -d android

# iOS
flutter test integration_test/app_test.dart -d ios
```

### Coverage Report
```bash
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html
```

---

## 1️⃣3️⃣ Troubleshooting

### Häufige Probleme

#### Problem: `flutter doctor` zeigt Fehler
```bash
# Android Licenses
flutter doctor --android-licenses

# iOS Setup
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept
```

#### Problem: CocoaPods-Fehler (iOS)
```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
flutter clean
flutter pub get
```

#### Problem: Gradle Build Fehler (Android)
```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
```

#### Problem: Code Generation funktioniert nicht
```bash
flutter clean
flutter pub get
flutter pub run build_runner clean
flutter pub run build_runner build --delete-conflicting-outputs
```

---

## 🎉 Fertig!

Dein Flutter-Projekt ist jetzt einsatzbereit!

### Nächste Schritte:
1. ✅ Erste Seite implementieren (Splash Screen)
2. ✅ Navigation aufsetzen (GoRouter)
3. ✅ State Management konfigurieren (Riverpod)
4. ✅ API Client implementieren (Dio + Retrofit)
5. ✅ Theme implementieren (Light + Dark Mode)

### Hilfreiche Commands:
```bash
# App starten
flutter run

# Hot Reload
# Drücke 'r' im Terminal

# Hot Restart
# Drücke 'R' im Terminal

# Logs anzeigen
flutter logs

# Performance Profiling
flutter run --profile

# Build Release APK
flutter build apk --release
```

---

**Happy Coding! 🚀**
