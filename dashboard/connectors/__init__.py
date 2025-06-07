from dashboard.registry import registry
from dashboard.models import OuraData, CronometerData, StravaData, GarminData, ManualData
from .oura import OuraConnector
from .cronometer import CronometerConnector
from .strava import StravaConnector
from .garmin import GarminConnector
from .manual import ManualConnector

# Register all connectors
registry.register(OuraConnector(), OuraData)
registry.register(GarminConnector(), GarminData)
registry.register(ManualConnector(), ManualData)
registry.register(CronometerConnector(), CronometerData)
# don't use strava for now, as data is available in garmin too
# registry.register(StravaConnector(), StravaData)

def get_connectors():
    """Get all registered connectors."""
    return registry.get_connectors() 