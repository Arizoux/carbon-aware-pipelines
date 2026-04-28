import os
import sys
import requests
from helpers.zones import CarbonAwareRegion


def get_current_intensity(zone_id):
    """
    Fetches the latest carbon intensity.
    """
    api_key = os.environ.get("ELECTRICITY_MAPS_API_KEY")
    if not api_key:
        raise ValueError("ELECTRICITY_MAPS_API_KEY is missing.")

    url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone_id}&temporalGranularity=15_minutes"
    headers = {"auth-token": api_key}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json().get("carbonIntensity")


def evaluate(params):
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
        current_ci = get_current_intensity(region_enum.em_id)
        print(f"[Threshold] Current CI in {target_region} ({region_enum.em_id}): {current_ci}", file=sys.stderr)

        if current_ci <= threshold_gco2_kwh:
            print(f"Target met: {current_ci} <= {threshold_gco2_kwh}", file=sys.stderr)
            return {
                "should_run": True,
                "region": region_enum.aws_id
            }
        else:
            print(f"Target NOT met: {current_ci} > {threshold_gco2_kwh}", file=sys.stderr)
            return {"should_run": False, "region": None}

    except Exception as e:
        print(f"Threshold Error: {e}", file=sys.stderr)
        return {"should_run": False, "region": None}