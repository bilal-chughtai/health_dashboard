from dashboard.registry import registry
from dashboard.models import OuraData, CronometerData, StravaData, GarminData, GSheetData
from .oura import OuraConnector
from .cronometer import CronometerConnector
from .strava import StravaConnector
from .garmin import GarminConnector
from .gsheet import GSheetConnector

# Register all connectors
registry.register(OuraConnector(), OuraData)
registry.register(GarminConnector(), GarminData)
registry.register(GSheetConnector(), GSheetData)
registry.register(CronometerConnector(), CronometerData)
# don't use strava for now, as data is available in garmin too
# registry.register(StravaConnector(), StravaData)

def get_connectors():
    """Get all registered connectors."""
    return registry.get_connectors() 