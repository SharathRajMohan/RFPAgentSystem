#!/usr/bin/env python3
"""Test script for RFP analysis API."""

import os
import requests

BASE_URL = "http://localhost:8000"
DATASET_DIR = os.path.join(os.path.dirname(__file__), "Dataset")
RFP_PDF = os.path.join(DATASET_DIR, "CCAC_RFP.pdf")


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    assert response.status_code == 200
    print("[OK] Health check passed")


def test_analyze_pdf(pdf_path: str, format: str = "markdown"):
    """Test the analyze-pdf endpoint with a real PDF file."""
    print(f"\nTesting PDF analysis with: {os.path.basename(pdf_path)}")
    assert os.path.isfile(pdf_path), f"PDF not found: {pdf_path}"

    with open(pdf_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/v1/analyze-pdf",
            files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
            params={"format": format},
        )

    assert response.status_code == 200, (
        f"Failed with status {response.status_code}: {response.text}"
    )

    result = response.json()
    print(f"[OK] Analysis completed for RFP: {result['rfp_id']}")

    # Verify response structure
    assert "rfp_id" in result
    assert "extracted_data" in result
    assert "solution_mappings" in result
    assert "analysis_timestamp" in result

    print(f"\n  Extracted Company: {result['extracted_data']['company_info']['name']}")
    print(f"  Industry: {result['extracted_data']['company_info']['industry']}")
    print(f"\n  Solution Mappings ({len(result['solution_mappings'])} found):")
    for solution in result["solution_mappings"]:
        print(
            f"    - {solution['solution_name']}: {solution['confidence_level']} confidence"
        )

    return result


def main():
    """Run all tests."""
    print("=" * 60)
    print("RFP Analysis System - API Test (PDF)")
    print("=" * 60)

    try:
        test_health_check()
        result = test_analyze_pdf(RFP_PDF)
        print(f"\n Test passed RFP ID: {result['rfp_id']}")

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Error: Could not connect to API at {BASE_URL}")
        print("  Make sure the server is running: uv run python -m uvicorn main:app --reload")
        return False
    except AssertionError as e:
        print(f"[FAIL] Test failed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
