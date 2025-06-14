# Health Dashboard

Aggregates and visualizes data from a bunch of apps / wearables in one place.

## Deployment

### Backend Deployment

- `git clone https://github.com/bilal-chughtai/health_dashboard`.
- `poetry install`.
- Set up an AWS bucket to store the data in a place both the backend and frontend can access.
- Configure secrets via `cp .secrets.template.json .secrets.json`.
- Add `script.sh` to crontab to run on a regular interval.

### Frontend Deployment

- Deployed on [streamlit community cloud](https://streamlit.io/cloud).
- Configure secrets via `cp .streamlit.secrets.template.toml .streamlit.secrets.toml` and copy `secrets.toml` into the streamlit secrets field.

## Development

### Backend Development

The main entry point is `poetry run python -m dashboard.main`.

- For updating data on AWS use the `--online` flag, this is what is used in deployment. By omitting we only read and write from local data.
- `--apps` allows fetching of data from only certain apps.
- `--past_days n` fetches data from the past `n` days.

### Adding a new app

1. `.secrets.template.json` and `.secrets.json`: Add API keys for the new app.
2. `dashboard/secret.py`: Load the new API keys.
3. `dashboard/models.py`: Add a new class inheriting from `BaseData` with fields and metadata that specifies the data model.
4. `dashboard/connectors/`: Create a new connector class inheriting from `BaseConnector` that implements the logic to fetch the data.
5. `dashboard/registry.py`: Add the new connector to `get_connectors()`.
6. `dashboard/dashboard.py`: Import the model and update the source order if needed.

### Frontend Development

- Autoupdate the frontend via running `poetry run streamlit run dashboard/dashboard.py`