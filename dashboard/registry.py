from typing import Type, TypeVar, Generic, Iterator
from dashboard.connectors.base import Connector
from dashboard.models import BaseData

T = TypeVar('T', bound=BaseData)

class ConnectorModelPair(Generic[T]):
    def __init__(self, connector: Connector[T], model: Type[T]):
        self.connector = connector
        self.model = model
        self.source_name = connector.source_name

class ConnectorRegistry:
    def __init__(self):
        self._connectors: list[ConnectorModelPair] = []
    
    def register(self, connector: Connector[T], model: Type[T]) -> None:
        """Register a connector and its corresponding data model."""
        self._connectors.append(ConnectorModelPair(connector, model))
    
    def get_connectors(self) -> list[Connector]:
        """Get all registered connectors."""
        return [pair.connector for pair in self._connectors]
    
    def get_sources(self) -> list[str]:
        """Get all registered source names."""
        return [pair.source_name for pair in self._connectors]

# Create a global registry instance
registry = ConnectorRegistry() 