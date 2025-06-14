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

### Frontend Development

- Autoupdate the frontend via running `poetry run streamlit run dashboard/dashboard.py`