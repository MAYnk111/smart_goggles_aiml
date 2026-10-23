import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';

class GpsService {
  double _latitude = 28.6139; // Default New Delhi fallback
  double _longitude = 77.2090;
  bool _isRealGps = false;
  String _statusMessage = "Using default coordinates (New Delhi)";

  double get latitude => _latitude;
  double get longitude => _longitude;
  bool get isRealGps => _isRealGps;
  String get statusMessage => _statusMessage;

  /// Request permissions and obtain real phone GPS coordinates
  Future<Position?> getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _isRealGps = false;
        _statusMessage = "Location services disabled on device. Using fallback.";
        debugPrint(_statusMessage);
        return null;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          _isRealGps = false;
          _statusMessage = "Location permissions denied by user. Using fallback.";
          debugPrint(_statusMessage);
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        _isRealGps = false;
        _statusMessage = "Location permissions permanently denied. Using fallback.";
        debugPrint(_statusMessage);
        return null;
      }

      Position position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
          timeLimit: Duration(seconds: 8),
        ),
      );

      _latitude = position.latitude;
      _longitude = position.longitude;
      _isRealGps = true;
      _statusMessage = "Live Phone GPS acquired (±${position.accuracy.toStringAsFixed(0)}m)";
      debugPrint("GPS Acquired: lat=$_latitude, lon=$_longitude");
      return position;
    } catch (e) {
      _isRealGps = false;
      _statusMessage = "GPS lookup exception: $e. Using fallback.";
      debugPrint(_statusMessage);
      return null;
    }
  }
}

final gpsService = GpsService();
