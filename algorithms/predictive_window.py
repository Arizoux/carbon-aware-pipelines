import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from helpers.zones import CarbonAwareRegion


def get_forecast_for_zone(zone_id):
    """Fetches the forecast with 15-minute resolution."""
    api_key = os.environ.get("ELECTRICITY_MAPS_API_KEY")
    url = f"https://api.electricitymap.org/v3/carbon-intensity/forecast?zone={zone_id}&temporalGranularity=15_minutes"

    headers = {"auth-token": api_key}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("forecast", [])


def evaluate(params):
    """
    Uses the params passed from main.py to find the optimal
    time slot for a contiguous workload.
    """
    # 1. Access data passed from main.py
    # These keys must match the user_config.json exactly
    target_region = params.get("target_region")
    run_duration = params.get("run_duration")
    forecast_window_hours = params.get("forecast_window_hours")

    if not all([target_region, run_duration, forecast_window_hours]):
        print(f"Error: Missing required parameters for Predictive Window. Got: {params}", file=sys.stderr)
        return {"should_run": False, "region": None}

    try:
        region_enum = CarbonAwareRegion[target_region]
    except KeyError:
        print(f"Error: {target_region} not found in CarbonAwareRegion enum.", file=sys.stderr)
        return {"should_run": False, "region": None}

    try:
        forecast_data = get_forecast_for_zone(region_enum.em_id)
        print(f"forecast data: {forecast_data}")
        now = datetime.now(timezone.utc)
        limit_time = now + timedelta(hours=forecast_window_hours)

        # Filter forecast for the search window
        relevant_points = [
            p for p in forecast_data
            if now <= datetime.fromisoformat(p["datetime"].replace('Z', '+00:00')) <= limit_time
        ]

        # Calculate K (number of 15-min intervals in the build)
        # 2 hours = 8 points
        k_points = int((run_duration * 60) / 15)

        if len(relevant_points) < k_points:
            print(f"Error: Not enough data points ({len(relevant_points)}) for {run_duration}h build.",
                  file=sys.stderr)
            return {"should_run": False, "region": None}

        # Sliding Window Implementation
        best_avg_ci = float('inf')
        best_start_time = None

        for i in range(len(relevant_points) - k_points + 1):
            window = relevant_points[i: i + k_points]
            avg_ci = sum(p["carbonIntensity"] for p in window) / k_points

            if avg_ci < best_avg_ci:
                best_avg_ci = avg_ci
                best_start_time = datetime.fromisoformat(window[0]["datetime"].replace('Z', '+00:00'))

        time_until_start = (best_start_time - now).total_seconds() / 3600

        print(f"[Predictive Window] Target: {target_region} | Best Start: {best_start_time} | Avg CI: {best_avg_ci:.1f}",
              file=sys.stderr)

        # If best start is within 15 mins (0.25h): run
        if time_until_start <= 0.25:
            return {"should_run": True, "region": region_enum.gcp_id}
        else:
            return {
                "should_run": False,
                "region": region_enum.gcp_id,
                "planned_time": best_start_time["start_time"].isoformat()
            }

    except Exception as e:
        print(f"Algorithm Error: {e}", file=sys.stderr)
        return {"should_run": False, "region": None}