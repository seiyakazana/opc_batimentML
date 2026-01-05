# service.py
from __future__ import annotations

import os
from typing import Dict, List, Literal

import bentoml
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, conint, confloat, model_validator


# Pydantic literals
UseName = Literal[
    "Lodging",
    "Recreation",
    "Other",
    "Education",
    "Retail",
    "Office",
    "Warehouse",
    "Parking",
    "Restaurant",
    "Laboratory",
    "Grocery",
]

BUILDING_TYPE = Literal[
    "NonResidential",
    "Nonresidential COS",
    "Nonresidential WA",
    "SPS-District K-12",
]

OUTLIER = Literal["", "High outlier", "Low outlier"]
AGE_CAT = Literal["0-20", "20-50", "50-80", "80+"]


# Pydantic request schema 
class InputRow(BaseModel):
    NumberofBuildings: conint(ge=1, le=1000)
    NumberofFloors: conint(ge=0, le=300)
    PropertyGFATotal: confloat(gt=0, le=5e7)

    PropertyUseDetails: Dict[UseName, confloat(ge=0)] = Field(
        default_factory=dict,
        description=(
            "Surfaces (m²) par usage. "
            "Usages autorisés: Lodging, Recreation, Other, Education, Retail, "
            "Office, Warehouse, Parking, Restaurant, Laboratory, Grocery."
        ),
        json_schema_extra={"example": {"Office": 70000, "Parking": 18434}},
    )    

    source_of_energy: conint(ge=0, le=3) = Field(
        ...,
        description="0=ni gaz ni vapeur, 1=vapeur uniquement, 2=gaz uniquement, 3=gaz+vapeur",
    )

    Building_Age: conint(ge=0, le=300)

    BuildingType: BUILDING_TYPE
    Neighborhood_EAST: conint(ge=0, le=1)

    ComplianceStatus: str = Field(
        ...,
        description="Valeur brute de ComplianceStatus (le pipeline gère le one-hot, unknown ignoré).",
    )

    Outlier: OUTLIER = ""

    #Pydantic validator
    @model_validator(mode="after")
    def validate_coherence(self) -> "InputRow":
        total_area = float(sum(self.PropertyUseDetails.values()))
        if total_area <= 0:
            raise ValueError(
                "PropertyUseDetails doit contenir au moins un usage avec une surface > 0."
            )

        gfa = float(self.PropertyGFATotal)
        if total_area > gfa * 1.01:
            raise ValueError(
                f"La somme des PropertyUseDetails ({total_area}) dépasse "
                f"PropertyGFATotal ({gfa}) (tolérance 1%)."
            )

        return self


class PredictRequest(BaseModel):
    rows: List[InputRow] = Field(..., min_length=1)


# Feature engineering 
def compute_building_age_category(age: int) -> AGE_CAT:
    if age < 20:
        return "0-20"
    elif age < 50:
        return "20-50"
    elif age < 80:
        return "50-80"
    else:
        return "80+"

def areas_to_ratios(
    areas: Dict[str, float],
    gfa: float,
    ratio_cols: List[str],
) -> Dict[str, float]:
    ratios = {c: 0.0 for c in ratio_cols}
    gfa = float(gfa)
    if gfa <= 0:
        return ratios

    for use, area in areas.items():
        col = f"PropertyUseRatio_{use}"
        if col in ratios:
            ratios[col] = float(area) / gfa

    return ratios


def build_feature_row(inp: InputRow, ratio_cols: List[str]) -> Dict[str, object]:
    row: Dict[str, object] = {}

    # numeric
    row["NumberofBuildings"] = float(inp.NumberofBuildings)
    row["NumberofFloors"] = float(inp.NumberofFloors)
    row["PropertyGFATotal"] = float(inp.PropertyGFATotal)
    row["Neighborhood_EAST"] = int(inp.Neighborhood_EAST)
    row["source_of_energy"] = float(inp.source_of_energy)
    row["Building_Age"] = float(inp.Building_Age)

    # ratios (ensure all ratio cols exist, default 0.0)
    row.update(areas_to_ratios(inp.PropertyUseDetails, inp.PropertyGFATotal, ratio_cols))

    # categorical
    row["BuildingType"] = inp.BuildingType
    row["Building_Age_Category"] = compute_building_age_category(inp.Building_Age)
    row["ComplianceStatus"] = inp.ComplianceStatus
    row["Outlier"] = inp.Outlier

    return row


# BentoML Service 
@bentoml.service(name="energy_regressor")
class EnergyRegressorService:
    def __init__(self) -> None:
        model_tag = os.getenv("ENERGY_MODEL_TAG", "energy_regressor:latest")

        model_ref = bentoml.sklearn.get(model_tag)
        self.model = model_ref.load_model()

        co = model_ref.custom_objects or {}

        required_keys = {
            "use_categories",
            "ratio_cols",
            "raw_required_numeric",
            "raw_required_categorical",
            "raw_required_columns",
        }
        missing = required_keys - set(co.keys())
        if missing:
            raise RuntimeError(
                f"Model '{model_tag}' is missing required custom_objects keys: {sorted(missing)}. "
                "Rebuild/export the model with these custom objects."
            )

        self.USE_CATEGORIES = list(co["use_categories"])
        self.RATIO_COLS = list(co["ratio_cols"])
        self.RAW_REQUIRED_NUMERIC = list(co["raw_required_numeric"])
        self.RAW_REQUIRED_CATEGORICAL = list(co["raw_required_categorical"])
        self.RAW_REQUIRED_COLUMNS = list(co["raw_required_columns"])

    @bentoml.api()
    def predict(self, request: PredictRequest) -> dict:
        # Build dataframe
        rows = [build_feature_row(r, self.RATIO_COLS) for r in request.rows]
        X = pd.DataFrame(rows)

        # Enforce strict schema: add missing columns and order columns
        for col in self.RAW_REQUIRED_COLUMNS:
            if col not in X.columns:
                if col in self.RAW_REQUIRED_CATEGORICAL:
                    X[col] = "Unknown"
                else:
                    X[col] = 0.0

        X = X[self.RAW_REQUIRED_COLUMNS]

        # Predict: model outputs log1p(target) -> invert with expm1
        preds_log = self.model.predict(X)
        preds = np.expm1(preds_log)

        return {"predictions": np.asarray(preds).tolist()}
