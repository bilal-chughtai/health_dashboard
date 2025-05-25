from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar, Generic, List
from backend.models import BaseData

T = TypeVar('T', bound=BaseData)

class Connector(Generic[T], ABC):
    """Base class for all data connectors."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source."""
        pass

    @abstractmethod
    def get_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[T]:
        """Fetch data for the given date range."""
        pass 