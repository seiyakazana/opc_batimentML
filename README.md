# opc_batimentML

This project is used to calculate and predict the annual energy consumption of buildings using machine learning.

It includes code and a notebook to prepare data, train a model, and save the trained model so an API can serve predictions.

For details, see the repository files and the notebook.
## 🚀 Project Overview

**opc_batimentML** provides a small, production-ready example of an energy regression model for (mostly) non-residential buildings. The repository contains:

- A BentoML service (`app/service.py`) that validates inputs with **Pydantic**, performs feature engineering, and returns annual energy predictions.
- A lightweight client example (`app/client.py`) to call the service.
- Jupyter notebook for exploration under `notebook/`.

---

## ✨ Features

- Input validation using `pydantic` models
- Feature engineering helpers (area ratios, age categories)
- Model serving via **BentoML** with a well-defined API
- Unit tests validating request schemas (`tests/test_validation.py`)

---

## 📁 Repository Structure

- `app/` – BentoML service and example client
- `data/` – raw and processed dataset CSVs
- `notebook/` – exploratory notebook
- `tests/` – unit tests
- `env/python/requirements.txt` – pinned runtime dependencies

---

## ⚙️ Installation

Requirements: Python 3.10+ (recommended), git, and a virtual environment tool.

Windows example (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r env\python\requirements.txt
pip install pytest requests
```

Linux / macOS example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r env/python/requirements.txt
pip install pytest requests
```

---

## 🧪 Running Tests

Run the unit tests with pytest:

```bash
pytest -q
```

The tests cover the `InputRow` validation behaviour (see `tests/test_validation.py`).

---

## 🔌 Running the Service Locally

Important: the service expects a BentoML model to be available and referenced by the environment variable `ENERGY_MODEL_TAG` (default: `energy_regressor:latest`). The saved model must include the following `custom_objects` keys:

- `use_categories`
- `ratio_cols`
- `raw_required_numeric`
- `raw_required_categorical`
- `raw_required_columns`

Example of saving a trained scikit-learn model:

```python
import bentoml
bentoml.sklearn.save_model(
    "energy_regressor:latest",
    trained_model,
    custom_objects={
        "use_categories": use_categories,
        "ratio_cols": ratio_cols,
        "raw_required_numeric": raw_num_cols,
        "raw_required_categorical": raw_cat_cols,
        "raw_required_columns": required_columns,
    },
)
```

To serve the service locally (after saving the BentoML model):

```bash
# Set the model tag (PowerShell)
$Env:ENERGY_MODEL_TAG = "energy_regressor:latest"

# Use BentoML to serve the Python service module (example)
bentoml serve app.service:energy_regressor --reload
```

Or build and serve a Bento with `bentoml build` / `bentoml serve <bento-name>:latest` if you prefer packaging.

---

## 🧾 API / Client Example

The service accepts a JSON body mapping to `PredictRequest` → `{ "rows": [ InputRow, ... ] }`.

Minimal `InputRow` fields (see `app/service.py` for full schema and validation rules):

- `BuildingType` (str)
- `NumberofBuildings` (int, >=1)
- `NumberofFloors` (int)
- `PropertyGFATotal` (float > 0)
- `PropertyUseDetails` (object mapping building uses to area in m², at least one > 0)
- `source_of_energy` (int enum 0..3)
- `Building_Age` (int)
- `Neighborhood_EAST` (0 or 1)

Example Python request using `requests`:

```python
import requests

URL = "http://localhost:3000/predict"
payload = {
    "rows": [
        {
            "BuildingType": "NonResidential",
            "NumberofBuildings": 1,
            "NumberofFloors": 12,
            "PropertyGFATotal": 88434,
            "Neighborhood_EAST": 0,
            "source_of_energy": 3,
            "Building_Age": 100,
            "PropertyUseDetails": {"Lodging": 88434},
        }
    ]
}

r = requests.post(URL, json=payload, timeout=30)
print(r.status_code)
print(r.json())
```

Example curl:

```bash
curl -X POST "http://localhost:3000/predict" \
  -H "Content-Type: application/json" \
  -d '{"rows":[{"BuildingType":"NonResidential","NumberofBuildings":1,"NumberofFloors":12,"PropertyGFATotal":88434,"Neighborhood_EAST":0,"source_of_energy":3,"Building_Age":100,"PropertyUseDetails":{"Lodging":88434}}]}'
```

Response format:

```json
{
  "predictions": [123456.78]
}
```

---

## 🧭 Data

- `data/2016_Building_Energy_Benchmarking.csv` — source dataset
- `data/processed_features.csv` — preprocessed features used for training

---

## 🤝 Contributing

- Please open issues for bugs or feature requests.
- For code changes, open a pull request and add tests where appropriate.

---

## 📜 License

No license file is included in this repository. Add a `LICENSE` file (e.g., MIT) to clarify terms.

---

## 📫 Contact

If you have questions, open an issue or contact the maintainer in the repository.

---

Thank you for using **opc_batimentML**! ✅
