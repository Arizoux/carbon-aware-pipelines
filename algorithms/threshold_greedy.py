import os
import sys
import requests
from helpers.zones import CarbonAwareRegion

def get_current_intensity(zone_id):
    """
    Fetches the latest carbon intensity from Electricity Maps.
    """
    api_key = os.environ.get("ELECTRICITY_MAPS_API_KEY")
    if not api_key:
        raise ValueError("ELECTRICITY_MAPS_API_KEY is missing.")

    url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone_id}"
    headers = {"auth-token": api_key}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json().get("carbonIntensity")


def evaluate(params):
    """
    Greedy Strategy: Runs immediately if the current intensity
    is below the user-defined threshold.
    """
    target_region = params.get("target_region")
    threshold_gco2_kwh = params.get("threshold_gco2_kwh")

    if not target_region or threshold_gco2_kwh is None:
        print(f"Error: Missing parameters. Got: {params}", file=sys.stderr)
        return {"should_run": False, "region": None}

    try:
        region_enum = CarbonAwareRegion[target_region]
    except KeyError:
        print(f"Error: {target_region} is not a valid Enum member.", file=sys.stderr)
        return {"should_run": False, "region": None}

    try:
        # Fetch data
        current_ci = get_current_intensity(region_enum.em_id)
        print(f"[Threshold] Current CI in {target_region} ({region_enum.em_id}): {current_ci} g", file=sys.stderr)

        # Compare and Return
        if current_ci <= threshold_gco2_kwh:
            print(f"Target met: {current_ci} <= {threshold_gco2_kwh}. Starting build...", file=sys.stderr)
            return {
                "should_run": True,
                "region": region_enum.gcp_id
            }
        else:
            print(f"Target NOT met: {current_ci} > {threshold_gco2_kwh}. Waiting for next cron check...", file=sys.stderr)
            return {"should_run": False, "region": None}

    except Exception as e:
        print(f"Threshold Error: {e}", file=sys.stderr)
        return {"should_run": False, "region": None}