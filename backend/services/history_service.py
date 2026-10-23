"""
History Service
Stores real-time sensor streams and computed risk evaluations.
Maintains rolling buffer for physiological stats and historical records for time-series visualization.
"""

import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.models_schema import SensorInput, SensorTelemetryResponse

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "smart_goggle.db")

class HistoryService:
    def __init__(self):
        self.rolling_sensor_buffer: List[SensorInput] = []
        self.latest_telemetry: Optional[SensorTelemetryResponse] = None
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    heart_rate REAL,
                    spo2 REAL,
                    temperature REAL,
                    finger INTEGER,
                    fall INTEGER,
                    emergency INTEGER,
                    aqi_bucket TEXT,
                    stress_class TEXT,
                    risk_score REAL,
                    risk_level TEXT,
                    payload_json TEXT
                )
            """)
            conn.commit()

            # Ensure newly added columns exist in older DB files
            cursor.execute("PRAGMA table_info(telemetry_history)")
            existing_cols = [row[1] for row in cursor.fetchall()]
            for col, col_type in [("finger", "INTEGER DEFAULT 1"), ("fall", "INTEGER DEFAULT 0"), ("emergency", "INTEGER DEFAULT 0")]:
                if col not in existing_cols:
                    cursor.execute(f"ALTER TABLE telemetry_history ADD COLUMN {col} {col_type}")
            conn.commit()

    def record_telemetry(self, telemetry: SensorTelemetryResponse):
        self.latest_telemetry = telemetry
        self.rolling_sensor_buffer.append(telemetry.sensor_data)
        if len(self.rolling_sensor_buffer) > 15:
            self.rolling_sensor_buffer.pop(0)

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO telemetry_history (
                        timestamp, heart_rate, spo2, temperature,
                        finger, fall, emergency,
                        aqi_bucket, stress_class, risk_score, risk_level, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    telemetry.timestamp,
                    telemetry.sensor_data.get_effective_hr(),
                    telemetry.sensor_data.spo2,
                    telemetry.sensor_data.temperature,
                    1 if telemetry.sensor_data.finger else 0,
                    1 if telemetry.sensor_data.fall else 0,
                    1 if telemetry.sensor_data.emergency else 0,
                    telemetry.aqi_prediction.predicted_bucket,
                    telemetry.physiological_prediction.predicted_stress,
                    telemetry.personalized_risk.risk_score,
                    telemetry.personalized_risk.risk_level,
                    telemetry.model_dump_json()
                ))
                conn.commit()
        except Exception as e:
            print(f"HistoryService DB error: {e}")

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        records = []
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, heart_rate, spo2, temperature,
                           finger, fall, emergency,
                           aqi_bucket, stress_class, risk_score, risk_level
                    FROM telemetry_history
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                for r in reversed(rows):
                    records.append({
                        "timestamp": r[0],
                        "heart_rate": r[1],
                        "spo2": r[2],
                        "temperature": r[3],
                        "finger": bool(r[4]),
                        "fall": bool(r[5]),
                        "emergency": bool(r[6]),
                        "aqi_bucket": r[7],
                        "stress_class": r[8],
                        "risk_score": r[9],
                        "risk_level": r[10]
                    })
        except Exception as e:
            print(f"History fetch error: {e}")
        return records

    def get_latest(self) -> Optional[SensorTelemetryResponse]:
        return self.latest_telemetry

history_service = HistoryService()
