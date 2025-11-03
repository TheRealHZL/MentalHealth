# 💻 Flutter Code Examples - MindBridge

## Core Architecture

### 1. API Client (Dio + Retrofit)

```dart
// lib/core/network/api_client.dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient({required String baseUrl}) {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    _dio.interceptors.addAll([
      AuthInterceptor(_storage),
      LoggingInterceptor(),
      ErrorInterceptor(),
    ]);
  }

  Dio get dio => _dio;
}

// Auth Interceptor für JWT Tokens
class AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;

  AuthInterceptor(this._storage);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      // Token expired - refresh token
      final refreshed = await _refreshToken();
      if (refreshed) {
        // Retry original request
        final opts = err.requestOptions;
        final token = await _storage.read(key: 'access_token');
        opts.headers['Authorization'] = 'Bearer $token';
        final response = await Dio().fetch(opts);
        return handler.resolve(response);
      }
    }
    handler.next(err);
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken == null) return false;

      final response = await Dio().post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      await _storage.write(
        key: 'access_token',
        value: response.data['access_token'],
      );
      return true;
    } catch (e) {
      return false;
    }
  }
}
```

### 2. Retrofit API Service

```dart
// lib/core/network/api_service.dart
import 'package:retrofit/retrofit.dart';
import 'package:dio/dio.dart';

part 'api_service.g.dart';

@RestApi()
abstract class ApiService {
  factory ApiService(Dio dio, {String baseUrl}) = _ApiService;

  // Auth
  @POST('/auth/login')
  Future<LoginResponse> login(@Body() LoginRequest request);

  @POST('/auth/register')
  Future<RegisterResponse> register(@Body() RegisterRequest request);

  @POST('/auth/logout')
  Future<void> logout();

  // Mood Entries
  @GET('/mood')
  Future<PaginatedResponse<MoodEntry>> getMoodEntries(
    @Query('page') int page,
    @Query('page_size') int pageSize,
  );

  @POST('/mood')
  Future<MoodEntry> createMoodEntry(@Body() MoodEntryCreate data);

  @GET('/mood/{id}')
  Future<MoodEntry> getMoodEntry(@Path('id') String id);

  @PUT('/mood/{id}')
  Future<MoodEntry> updateMoodEntry(
    @Path('id') String id,
    @Body() MoodEntryUpdate data,
  );

  @DELETE('/mood/{id}')
  Future<void> deleteMoodEntry(@Path('id') String id);

  // Dreams
  @GET('/dreams')
  Future<PaginatedResponse<DreamEntry>> getDreamEntries(
    @Query('page') int page,
    @Query('page_size') int pageSize,
  );

  @POST('/dreams')
  Future<DreamEntry> createDreamEntry(@Body() DreamEntryCreate data);

  @POST('/dreams/{id}/interpret')
  Future<DreamInterpretation> interpretDream(@Path('id') String id);

  // Analytics
  @GET('/analytics/wellness-score')
  Future<WellnessScore> getWellnessScore();

  @GET('/analytics/mood-trends')
  Future<MoodTrends> getMoodTrends(
    @Query('days') int days,
  );
}
```

### 3. Encryption Service

```dart
// lib/core/services/encryption_service.dart
import 'dart:convert';
import 'dart:typed_data';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto/crypto.dart';

class EncryptionService {
  static const _storage = FlutterSecureStorage();
  static const _keyName = 'encryption_key';
  static const _algorithm = AesGcm.with256bits();

  // Derive encryption key from password
  static Future<SecretKey> deriveKeyFromPassword(
    String password,
    String salt,
  ) async {
    final pbkdf2 = Pbkdf2(
      macAlgorithm: Hmac.sha256(),
      iterations: 100000,
      bits: 256,
    );

    final secretKey = await pbkdf2.deriveKey(
      secretKey: SecretKey(utf8.encode(password)),
      nonce: utf8.encode(salt),
    );

    return secretKey;
  }

  // Store encryption key securely
  static Future<void> storeKey(SecretKey key) async {
    final keyBytes = await key.extractBytes();
    final keyBase64 = base64Encode(keyBytes);
    await _storage.write(key: _keyName, value: keyBase64);
  }

  // Retrieve encryption key
  static Future<SecretKey?> getKey() async {
    final keyBase64 = await _storage.read(key: _keyName);
    if (keyBase64 == null) return null;

    final keyBytes = base64Decode(keyBase64);
    return SecretKey(keyBytes);
  }

  // Encrypt data
  static Future<Map<String, String>> encrypt(String plaintext) async {
    final key = await getKey();
    if (key == null) throw Exception('Encryption key not found');

    final algorithm = _algorithm;
    final nonce = algorithm.newNonce();

    final secretBox = await algorithm.encrypt(
      utf8.encode(plaintext),
      secretKey: key,
      nonce: nonce,
    );

    return {
      'ciphertext': base64Encode(secretBox.cipherText),
      'nonce': base64Encode(secretBox.nonce),
      'version': '1',
    };
  }

  // Decrypt data
  static Future<String> decrypt(Map<String, String> encryptedData) async {
    final key = await getKey();
    if (key == null) throw Exception('Encryption key not found');

    final algorithm = _algorithm;
    final ciphertext = base64Decode(encryptedData['ciphertext']!);
    final nonce = base64Decode(encryptedData['nonce']!);
    final mac = ciphertext.sublist(ciphertext.length - 16);

    final secretBox = SecretBox(
      ciphertext.sublist(0, ciphertext.length - 16),
      nonce: nonce,
      mac: Mac(mac),
    );

    final decrypted = await algorithm.decrypt(secretBox, secretKey: key);
    return utf8.decode(decrypted);
  }

  // Clear encryption key (logout)
  static Future<void> clearKey() async {
    await _storage.delete(key: _keyName);
  }

  // Generate recovery key
  static String generateRecoveryKey() {
    final random = List<int>.generate(32, (i) => DateTime.now().millisecondsSinceEpoch % 256);
    return base64Url.encode(random);
  }
}
```

### 4. Local Database (Drift/SQLite)

```dart
// lib/core/database/app_database.dart
import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

part 'app_database.g.dart';

// Mood Entries Table
class MoodEntries extends Table {
  TextColumn get id => text()();
  TextColumn get userId => text()();
  IntColumn get moodScore => integer()();
  IntColumn get energyLevel => integer()();
  IntColumn get stressLevel => integer()();
  TextColumn get activities => text().map(const StringListConverter())();
  TextColumn get notes => text().nullable()();
  TextColumn get encryptedData => text().nullable()();
  BoolColumn get isSynced => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

// Database
@DriftDatabase(tables: [MoodEntries])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  static QueryExecutor _openConnection() {
    return driftDatabase(name: 'mindbridge_db');
  }

  // CRUD Operations
  Future<List<MoodEntry>> getAllMoodEntries() => select(moodEntries).get();

  Future<MoodEntry?> getMoodEntryById(String id) =>
      (select(moodEntries)..where((t) => t.id.equals(id))).getSingleOrNull();

  Future<int> insertMoodEntry(MoodEntry entry) =>
      into(moodEntries).insert(entry);

  Future<bool> updateMoodEntry(MoodEntry entry) =>
      update(moodEntries).replace(entry);

  Future<int> deleteMoodEntry(String id) =>
      (delete(moodEntries)..where((t) => t.id.equals(id))).go();

  // Unsynchronized entries
  Future<List<MoodEntry>> getUnsyncedMoodEntries() =>
      (select(moodEntries)..where((t) => t.isSynced.equals(false))).get();
}

// String List Converter
class StringListConverter extends TypeConverter<List<String>, String> {
  const StringListConverter();

  @override
  List<String> fromSql(String fromDb) {
    return fromDb.split(',').where((s) => s.isNotEmpty).toList();
  }

  @override
  String toSql(List<String> value) {
    return value.join(',');
  }
}
```

### 5. State Management (Riverpod)

```dart
// lib/features/auth/presentation/providers/auth_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'auth_provider.g.dart';

// Auth State
class AuthState {
  final User? user;
  final bool isLoading;
  final String? error;
  final bool isAuthenticated;

  const AuthState({
    this.user,
    this.isLoading = false,
    this.error,
    this.isAuthenticated = false,
  });

  AuthState copyWith({
    User? user,
    bool? isLoading,
    String? error,
    bool? isAuthenticated,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
    );
  }
}

// Auth Provider
@riverpod
class Auth extends _$Auth {
  @override
  AuthState build() {
    _checkAuth();
    return const AuthState();
  }

  Future<void> _checkAuth() async {
    state = state.copyWith(isLoading: true);

    try {
      final user = await ref.read(authRepositoryProvider).getCurrentUser();
      state = state.copyWith(
        user: user,
        isAuthenticated: user != null,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final user = await ref
          .read(authRepositoryProvider)
          .login(email, password);

      // Derive encryption key from password
      await ref
          .read(encryptionServiceProvider)
          .initializeEncryption(password);

      state = state.copyWith(
        user: user,
        isAuthenticated: true,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<void> register(String email, String password, String firstName) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final user = await ref
          .read(authRepositoryProvider)
          .register(email, password, firstName);

      // Initialize encryption
      await ref
          .read(encryptionServiceProvider)
          .initializeEncryption(password);

      state = state.copyWith(
        user: user,
        isAuthenticated: true,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    await ref.read(encryptionServiceProvider).clearEncryption();
    state = const AuthState();
  }
}
```

### 6. Navigation (GoRouter)

```dart
// lib/core/router/app_router.dart
import 'package:go_router/go_router.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/auth');

      // Redirect to login if not authenticated
      if (!isAuthenticated && !isAuthRoute) {
        return '/auth/login';
      }

      // Redirect to home if authenticated and on auth page
      if (isAuthenticated && isAuthRoute) {
        return '/';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: '/auth/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/auth/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (context, state) => const DashboardScreen(),
        routes: [
          GoRoute(
            path: 'mood/new',
            builder: (context, state) => const MoodEntryScreen(),
          ),
          GoRoute(
            path: 'mood/:id',
            builder: (context, state) {
              final id = state.pathParameters['id']!;
              return MoodDetailScreen(id: id);
            },
          ),
        ],
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('Page not found: ${state.uri}'),
      ),
    ),
  );
});
```

### 7. Theme Configuration

```dart
// lib/core/config/themes/app_theme.dart
import 'package:flutter/material.dart';

class AppTheme {
  // Colors
  static const Color primaryColor = Color(0xFF3B82F6);
  static const Color secondaryColor = Color(0xFF10B981);
  static const Color errorColor = Color(0xFFEF4444);
  static const Color warningColor = Color(0xFFF59E0B);

  // Light Theme
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: const ColorScheme.light(
      primary: primaryColor,
      secondary: secondaryColor,
      error: errorColor,
      surface: Colors.white,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      onError: Colors.white,
      onSurface: Color(0xFF1F2937),
    ),
    scaffoldBackgroundColor: const Color(0xFFF9FAFB),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.white,
      foregroundColor: Color(0xFF1F2937),
      elevation: 0,
      centerTitle: true,
    ),
    cardTheme: CardTheme(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade200),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        elevation: 0,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    ),
    textTheme: const TextTheme(
      displayLarge: TextStyle(
        fontSize: 32,
        fontWeight: FontWeight.bold,
        color: Color(0xFF1F2937),
      ),
      headlineMedium: TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.bold,
        color: Color(0xFF1F2937),
      ),
      bodyLarge: TextStyle(
        fontSize: 16,
        color: Color(0xFF374151),
      ),
      bodyMedium: TextStyle(
        fontSize: 14,
        color: Color(0xFF6B7280),
      ),
    ),
  );

  // Dark Theme
  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: const ColorScheme.dark(
      primary: primaryColor,
      secondary: secondaryColor,
      error: errorColor,
      surface: Color(0xFF1F2937),
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      onError: Colors.white,
      onSurface: Color(0xFFF9FAFB),
    ),
    scaffoldBackgroundColor: const Color(0xFF111827),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF1F2937),
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: true,
    ),
    cardTheme: CardTheme(
      elevation: 0,
      color: const Color(0xFF1F2937),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade800),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        elevation: 0,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    ),
    textTheme: const TextTheme(
      displayLarge: TextStyle(
        fontSize: 32,
        fontWeight: FontWeight.bold,
        color: Colors.white,
      ),
      headlineMedium: TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.bold,
        color: Colors.white,
      ),
      bodyLarge: TextStyle(
        fontSize: 16,
        color: Color(0xFFE5E7EB),
      ),
      bodyMedium: TextStyle(
        fontSize: 14,
        color: Color(0xFF9CA3AF),
      ),
    ),
  );
}
```

### 8. Main App Entry

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import 'core/config/themes/app_theme.dart';
import 'core/router/app_router.dart';
import 'core/services/encryption_service.dart';
import 'firebase_options.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load environment variables
  await dotenv.load(fileName: '.env.development');

  // Initialize Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  // Initialize Sentry for crash reporting
  await SentryFlutter.init(
    (options) {
      options.dsn = dotenv.env['SENTRY_DSN'];
      options.tracesSampleRate = 1.0;
      options.environment = dotenv.env['ENVIRONMENT'] ?? 'development';
    },
    appRunner: () => runApp(
      const ProviderScope(
        child: MyApp(),
      ),
    ),
  );
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'MindBridge',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routerConfig: router,
      builder: (context, child) {
        return MediaQuery(
          data: MediaQuery.of(context).copyWith(textScaleFactor: 1.0),
          child: child!,
        );
      },
    );
  }
}
```

---

## UI Components

### 9. Custom Widgets

```dart
// lib/shared/widgets/mood_card.dart
import 'package:flutter/material.dart';

class MoodCard extends StatelessWidget {
  final int moodScore;
  final String notes;
  final DateTime createdAt;
  final VoidCallback? onTap;

  const MoodCard({
    super.key,
    required this.moodScore,
    required this.notes,
    required this.createdAt,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Mood Emoji
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: _getMoodColor().withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    _getMoodEmoji(),
                    style: const TextStyle(fontSize: 32),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              // Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          '$moodScore/10',
                          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            color: _getMoodColor(),
                          ),
                        ),
                        const Spacer(),
                        Text(
                          _formatDate(createdAt),
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      notes.isEmpty ? 'Keine Notizen' : notes,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _getMoodEmoji() {
    if (moodScore >= 8) return '😄';
    if (moodScore >= 6) return '🙂';
    if (moodScore >= 4) return '😐';
    if (moodScore >= 2) return '😕';
    return '😢';
  }

  Color _getMoodColor() {
    if (moodScore >= 7) return Colors.green;
    if (moodScore >= 5) return Colors.orange;
    return Colors.red;
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inDays == 0) return 'Heute';
    if (diff.inDays == 1) return 'Gestern';
    if (diff.inDays < 7) return '${diff.inDays} Tage';
    return '${date.day}.${date.month}.${date.year}';
  }
}
```

### 10. Loading & Error States

```dart
// lib/shared/widgets/loading_widget.dart
import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';

class LoadingWidget extends StatelessWidget {
  final String? message;

  const LoadingWidget({super.key, this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Lottie.asset(
            'assets/animations/loading.json',
            width: 120,
            height: 120,
          ),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(
              message!,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
          ],
        ],
      ),
    );
  }
}

// lib/shared/widgets/error_widget.dart
class ErrorDisplayWidget extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const ErrorDisplayWidget({
    super.key,
    required this.message,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              'Oops!',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Erneut versuchen'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

---

## Testing Examples

### 11. Unit Test

```dart
// test/unit/encryption_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mindbridge_flutter/core/services/encryption_service.dart';

void main() {
  group('EncryptionService', () {
    test('should encrypt and decrypt successfully', () async {
      // Arrange
      const plaintext = 'Sensitive data';
      final password = 'test_password';
      final salt = 'test_salt';

      // Derive key
      final key = await EncryptionService.deriveKeyFromPassword(password, salt);
      await EncryptionService.storeKey(key);

      // Act - Encrypt
      final encrypted = await EncryptionService.encrypt(plaintext);

      // Assert - Check encrypted data structure
      expect(encrypted['ciphertext'], isNotNull);
      expect(encrypted['nonce'], isNotNull);
      expect(encrypted['version'], equals('1'));

      // Act - Decrypt
      final decrypted = await EncryptionService.decrypt(encrypted);

      // Assert - Check decrypted matches original
      expect(decrypted, equals(plaintext));
    });
  });
}
```

### 12. Widget Test

```dart
// test/widget/mood_card_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindbridge_flutter/shared/widgets/mood_card.dart';

void main() {
  testWidgets('MoodCard displays mood information correctly', (tester) async {
    // Arrange
    final moodScore = 8;
    final notes = 'Feeling great today!';
    final createdAt = DateTime.now();

    // Act
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MoodCard(
            moodScore: moodScore,
            notes: notes,
            createdAt: createdAt,
          ),
        ),
      ),
    );

    // Assert
    expect(find.text('$moodScore/10'), findsOneWidget);
    expect(find.text(notes), findsOneWidget);
    expect(find.text('😄'), findsOneWidget); // Happy emoji for score 8
  });
}
```

---

Damit hast du eine solide Code-Basis für den Start! 🚀
