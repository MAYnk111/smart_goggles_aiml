import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/app_config.dart';
import '../constants.dart';
import '../providers/app_state.dart';
import '../services/ble_service.dart';

class BleDeviceScreen extends StatefulWidget {
  const BleDeviceScreen({super.key});

  @override
  State<BleDeviceScreen> createState() => _BleDeviceScreenState();
}

class _BleDeviceScreenState extends State<BleDeviceScreen> {
  bool _isScanning = false;
  bool _isTestingBackend = false;

  void _triggerScan() async {
    setState(() => _isScanning = true);
    await bleService.startScan(timeout: const Duration(seconds: 8));
    if (mounted) {
      setState(() => _isScanning = false);
    }
  }

  void _showBackendConfigDialog(BuildContext context, AppState appState) {
    final controller = TextEditingController(text: appState.backendUrl);
    String? dialogFeedback;
    bool isDialogTesting = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.dns_rounded, color: AppColors.primaryLight),
              SizedBox(width: 8),
              Text("Backend API Endpoint", style: TextStyle(fontSize: 16)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "Configure FastAPI host URL. Physical Android phones cannot reach localhost or 127.0.0.1.",
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: controller,
                  decoration: InputDecoration(
                    labelText: "API Base URL",
                    hintText: "http://10.49.187.65:8000",
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  ),
                  style: const TextStyle(fontSize: 13, fontFamily: 'monospace'),
                ),
                const SizedBox(height: 12),
                const Text(
                  "QUICK PRESETS:",
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: Colors.grey),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: AppConfig.presets.map((preset) {
                    final label = preset['label']!;
                    final url = preset['url']!;
                    final isSelected = controller.text.trim() == url;
                    return ActionChip(
                      label: Text(label, style: const TextStyle(fontSize: 10)),
                      avatar: isSelected ? const Icon(Icons.check, size: 12) : null,
                      backgroundColor: isSelected ? AppColors.primary.withValues(alpha: 0.3) : null,
                      onPressed: () {
                        setDialogState(() {
                          controller.text = url;
                          dialogFeedback = null;
                        });
                      },
                    );
                  }).toList(),
                ),
                if (dialogFeedback != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: dialogFeedback!.contains("SUCCESS")
                          ? Colors.green.withValues(alpha: 0.15)
                          : Colors.red.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      dialogFeedback!,
                      style: TextStyle(
                        fontSize: 11,
                        color: dialogFeedback!.contains("SUCCESS") ? Colors.green : Colors.redAccent,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text("Cancel"),
            ),
            ElevatedButton(
              onPressed: isDialogTesting
                  ? null
                  : () async {
                      setDialogState(() => isDialogTesting = true);
                      final testUrl = controller.text.trim();
                      final ok = await appState.updateBackendUrl(testUrl);
                      setDialogState(() {
                        isDialogTesting = false;
                        dialogFeedback = ok
                            ? "SUCCESS: Connected to $testUrl/api/health"
                            : "FAILED: ${appState.backendLastError ?? 'Unreachable'}";
                      });
                      if (ok) {
                        await Future.delayed(const Duration(milliseconds: 600));
                        if (context.mounted) Navigator.of(ctx).pop();
                      }
                    },
              child: isDialogTesting
                  ? const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text("Test & Save"),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final bleStatus = bleService.status;
    final isConnected = bleService.isConnected;
    final isReceiving = bleStatus == BleConnectionState.connectedReceiving;
    final isConnectedNoData = bleStatus == BleConnectionState.connectedNoData;
    final connectedDev = bleService.connectedDevice;
    final scanResults = bleService.scanResults;
    final vitals = appState.currentVitals;

    Color statusColor;
    if (bleService.isSimulating) {
      statusColor = Colors.orange;
    } else if (isReceiving) {
      statusColor = AppColors.riskLow;
    } else if (isConnectedNoData) {
      statusColor = Colors.amber;
    } else if (bleStatus == BleConnectionState.connecting) {
      statusColor = Colors.blueAccent;
    } else {
      statusColor = Colors.grey;
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text("ESP32 BLE Management"),
        actions: [
          IconButton(
            icon: _isTestingBackend
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.refresh_rounded),
            tooltip: "Test Backend Connection",
            onPressed: () async {
              setState(() => _isTestingBackend = true);
              await appState.refreshBackendState();
              if (mounted) setState(() => _isTestingBackend = false);
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings_ethernet_rounded),
            tooltip: "Configure Backend IP",
            onPressed: () => _showBackendConfigDialog(context, appState),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // 1. Connection Status Hero Card
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E293B) : Colors.white,
              borderRadius: BorderRadius.circular(22),
              border: Border.all(
                color: statusColor.withValues(alpha: 0.6),
                width: 1.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: statusColor.withValues(alpha: 0.08),
                  blurRadius: 14,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Row(
                        children: [
                          Icon(
                            Icons.bluetooth_rounded,
                            size: 26,
                            color: statusColor,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  "BLUETOOTH STATUS",
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 1.0,
                                    color: Colors.grey,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  bleService.statusDisplayLabel,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w700,
                                    color: statusColor,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (isConnected || bleService.isSimulating)
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.redAccent.withValues(alpha: 0.15),
                          foregroundColor: Colors.redAccent,
                          elevation: 0,
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        icon: const Icon(Icons.link_off_rounded, size: 14),
                        label: const Text("Disconnect", style: TextStyle(fontSize: 11)),
                        onPressed: () {
                          if (bleService.isSimulating) {
                            bleService.stopSimulation();
                          } else {
                            bleService.disconnect();
                          }
                        },
                      ),
                  ],
                ),
                if (connectedDev != null) ...[
                  const SizedBox(height: 12),
                  const Divider(),
                  const SizedBox(height: 6),
                  Text(
                    "Connected Device: ${connectedDev.platformName.isNotEmpty ? connectedDev.platformName : 'JATAYU_BAND'}",
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    "ID: ${connectedDev.remoteId}",
                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 14),

          // 2. Error Alerts (Task 7: DO NOT HIDE ERRORS)
          if (bleService.lastError != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.redAccent.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.redAccent.withValues(alpha: 0.4)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.error_outline_rounded, color: Colors.redAccent, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      bleService.lastError!,
                      style: const TextStyle(color: Colors.redAccent, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
          ],

          if (!appState.isBackendConnected && appState.backendLastError != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.amber.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.amber.withValues(alpha: 0.4)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.wifi_off_rounded, color: Colors.amber, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "FastAPI Unreachable",
                          style: TextStyle(color: Colors.amber, fontSize: 11, fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          appState.backendLastError!,
                          style: const TextStyle(color: Colors.amber, fontSize: 10),
                        ),
                        const SizedBox(height: 4),
                        GestureDetector(
                          onTap: () => _showBackendConfigDialog(context, appState),
                          child: const Text(
                            "Tap to change host IP / URL",
                            style: TextStyle(
                              color: AppColors.primaryLight,
                              fontSize: 10,
                              decoration: TextDecoration.underline,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
          ],

          // 3. Action Buttons: Scan, Simulate & Change IP
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  icon: _isScanning
                      ? const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.search_rounded, size: 18),
                  label: Text(_isScanning ? "Scanning..." : "Scan for ${AppConstants.bleDeviceName}"),
                  onPressed: _isScanning ? null : _triggerScan,
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: bleService.isSimulating ? Colors.orange : AppColors.secondary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                icon: Icon(bleService.isSimulating ? Icons.stop_rounded : Icons.play_arrow_rounded, size: 18),
                label: Text(bleService.isSimulating ? "Stop Sim" : "Simulate"),
                onPressed: () {
                  if (bleService.isSimulating) {
                    bleService.stopSimulation();
                  } else {
                    bleService.startSimulation();
                  }
                },
              ),
            ],
          ),
          const SizedBox(height: 20),

          // 4. Developer / Integration Debug Panel (Task 6)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "INTEGRATION DEBUG PANEL",
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.1,
                  color: Colors.grey,
                ),
              ),
              InkWell(
                onTap: () => _showBackendConfigDialog(context, appState),
                child: const Row(
                  children: [
                    Icon(Icons.edit_rounded, size: 12, color: AppColors.primaryLight),
                    SizedBox(width: 4),
                    Text(
                      "Configure IP",
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.primaryLight),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isDark ? AppColors.darkCard : Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildDebugRow(
                  "BLE Connection",
                  bleService.status.name.toUpperCase(),
                  isReceiving
                      ? AppColors.riskLow
                      : (isConnectedNoData ? Colors.amber : Colors.grey),
                ),
                _buildDebugRow(
                  "GATT Notifications",
                  bleService.gattNotificationStatus,
                  bleService.gattNotificationStatus == "RECEIVING"
                      ? AppColors.riskLow
                      : (bleService.gattNotificationStatus == "WAITING" ? Colors.amber : Colors.redAccent),
                ),
                _buildDebugRow("Packets Received", "${bleService.packetCount}", Colors.white),
                _buildDebugRow(
                  "Last Packet",
                  bleService.lastPacketTime != null
                      ? bleService.lastPacketTime!.toIso8601String().substring(11, 19)
                      : "never",
                  Colors.white70,
                ),
                _buildDebugRow(
                  "Connected Device",
                  connectedDev != null
                      ? "${connectedDev.platformName.isNotEmpty ? connectedDev.platformName : 'JATAYU_BAND'} (${connectedDev.remoteId})"
                      : "None",
                  AppColors.primaryLight,
                ),
                _buildDebugRow("Service UUID", AppConstants.bleServiceUuid, Colors.grey),
                _buildDebugRow("Char UUID", AppConstants.bleCharacteristicUuid, Colors.grey),
                const Divider(height: 14),
                _buildDebugRow(
                  "Backend API",
                  appState.isBackendConnected ? "CONNECTED" : "DISCONNECTED",
                  appState.isBackendConnected ? AppColors.riskLow : Colors.redAccent,
                ),
                _buildDebugRow(
                  "Backend URL",
                  appState.backendUrl,
                  AppColors.primaryLight,
                ),
                _buildDebugRow(
                  "Tested URL",
                  appState.backendTestedUrl,
                  Colors.grey,
                ),
                _buildDebugRow(
                  "Last API Upload",
                  appState.lastBackendUploadTime != null
                      ? appState.lastBackendUploadTime!.toIso8601String().substring(11, 19)
                      : "never",
                  Colors.white70,
                ),
                _buildDebugRow(
                  "Data Source",
                  vitals.source,
                  vitals.source == "REAL ESP32" ? AppColors.riskLow : Colors.orange,
                ),
                _buildDebugRow(
                  "Hardware Flags",
                  "Finger: ${vitals.finger} • Fall: ${vitals.fall} • Emergency: ${vitals.emergency}",
                  Colors.amber,
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // 5. Live Incoming ESP32 Payload (Raw JSON)
          const Text(
            "LIVE INCOMING ESP32 PAYLOAD (RAW JSON)",
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.1,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF0F172A) : Colors.grey[900],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isReceiving
                    ? Colors.greenAccent.withValues(alpha: 0.4)
                    : Colors.grey.withValues(alpha: 0.3),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      isReceiving
                          ? "GATT Notification Stream [ACTIVE]"
                          : (isConnectedNoData
                              ? "Waiting for ESP32 BLE stream..."
                              : "Stream Idle"),
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: isReceiving
                            ? Colors.greenAccent
                            : (isConnectedNoData ? Colors.amber : Colors.grey),
                      ),
                    ),
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isReceiving
                            ? Colors.greenAccent
                            : (isConnectedNoData ? Colors.amber : Colors.grey),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                SelectableText(
                  bleService.lastRawJson.isNotEmpty
                      ? bleService.lastRawJson
                      : (appState.lastRawBleJson.isNotEmpty
                          ? appState.lastRawBleJson
                          : "Waiting for ESP32 BLE stream..."),
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 12,
                    color: Colors.white,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // 6. Available Discovered Devices List
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "DISCOVERED BLE DEVICES",
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.1,
                  color: Colors.grey,
                ),
              ),
              Text(
                "${scanResults.length} found",
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ),
          const SizedBox(height: 10),

          if (scanResults.isEmpty)
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkCard : Colors.grey[100],
                borderRadius: BorderRadius.circular(16),
              ),
              child: Center(
                child: Text(
                  _isScanning
                      ? "Scanning for nearby BLE devices (${AppConstants.bleDeviceName})..."
                      : "No BLE devices discovered.\nTap 'Scan for ${AppConstants.bleDeviceName}' or 'Simulate' to test.",
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
              ),
            )
          else
            ...scanResults.map((r) {
              final name = r.device.platformName.isNotEmpty
                  ? r.device.platformName
                  : "Unnamed Peripheral";
              final isTarget = name.toUpperCase() == AppConstants.bleDeviceName.toUpperCase() ||
                  name.toLowerCase().contains("jatayu") ||
                  name.toLowerCase().contains("goggle");

              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCard : Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isTarget ? AppColors.primary : Colors.grey.withValues(alpha: 0.15),
                    width: isTarget ? 2.0 : 1,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: (isTarget ? AppColors.primary : Colors.grey).withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        isTarget ? Icons.verified_rounded : Icons.bluetooth_searching_rounded,
                        color: isTarget ? AppColors.primary : Colors.grey,
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  name,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    fontWeight: isTarget ? FontWeight.w900 : FontWeight.w600,
                                    fontSize: 13,
                                    color: isTarget ? AppColors.primaryLight : null,
                                  ),
                                ),
                              ),
                              if (isTarget) ...[
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: AppColors.primary.withValues(alpha: 0.2),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: const Text(
                                    "TARGET GOGGLE",
                                    style: TextStyle(
                                      fontSize: 8,
                                      fontWeight: FontWeight.w800,
                                      color: AppColors.primaryLight,
                                    ),
                                  ),
                                ),
                              ],
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(
                            "ID: ${r.device.remoteId} • RSSI: ${r.rssi} dBm",
                            style: const TextStyle(fontSize: 10, color: Colors.grey),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: isTarget ? AppColors.primary : Colors.grey[700],
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      child: const Text("Connect", style: TextStyle(fontSize: 11)),
                      onPressed: () => bleService.connect(r.device),
                    ),
                  ],
                ),
              );
            }),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildDebugRow(String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color),
            ),
          ),
        ],
      ),
    );
  }
}
