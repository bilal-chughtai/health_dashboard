from backend.registry import registry
from backend.models import OuraData, CronometerData, StravaData, GarminData, GSheetData
from .oura import OuraConnector
from .cronometer import CronometerConnector
from .strava import StravaConnector
from .garmin import GarminConnector
from .gsheet import GSheetConnector

# Register all connectors
registry.register(OuraConnector(), OuraData)
registry.register(CronometerConnector(), CronometerData)
# don't use strava for now, as data is available in garmin too
# registry.register(StravaConnector(), StravaData)
registry.register(GarminConnector(), GarminData)
registry.register(GSheetConnector(), GSheetData)

def get_connectors():
    """Get all registered connectors."""
    return registry.get_connectors() 