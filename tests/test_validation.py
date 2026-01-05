import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(app_dir))

import app.service as service
from app.service import InputRow, PredictRequest

import pytest
from pydantic import ValidationError


def test_valid_row_passes():
    row = InputRow(
        BuildingType="NonResidential",
        NumberofBuildings=1,
        NumberofFloors=10,
        PropertyGFATotal=1000.0,
        Neighborhood_EAST=0,
        source_of_energy=2,
        Building_Age=15,
        ComplianceStatus="Compliant",
        Outlier="",
        PropertyUseDetails={"Office": 200.0},
    )
    assert row.Building_Age == 15


def test_property_use_details_must_not_be_empty():
    with pytest.raises(ValidationError):
        InputRow(
            BuildingType="NonResidential",
            NumberofBuildings=1,
            NumberofFloors=10,
            PropertyGFATotal=1000.0,
            Neighborhood_EAST=0,
            source_of_energy=2,
            Building_Age=15,
            ComplianceStatus="Compliant",
            Outlier="",
            PropertyUseDetails={},  # invalid
        )


def test_sum_of_areas_cannot_exceed_gfa_by_more_than_1_percent():
    with pytest.raises(ValidationError):
        InputRow(
            BuildingType="NonResidential",
            NumberofBuildings=1,
            NumberofFloors=10,
            PropertyGFATotal=1000.0,
            Neighborhood_EAST=0,
            source_of_energy=2,
            Building_Age=15,
            ComplianceStatus="Compliant",
            Outlier="",
            PropertyUseDetails={"Office": 1020.0},  # > 1010
        )


def test_number_of_buildings_must_be_at_least_one():
    with pytest.raises(ValidationError):
        InputRow(
            BuildingType="NonResidential",
            NumberofBuildings=0,  # invalid: must be >= 1
            NumberofFloors=10,
            PropertyGFATotal=1000.0,
            Neighborhood_EAST=0,
            source_of_energy=2,
            Building_Age=15,
            ComplianceStatus="Compliant",
            Outlier="",
            PropertyUseDetails={"Office": 200.0},
        )

