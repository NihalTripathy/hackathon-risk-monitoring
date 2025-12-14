"""
Dependency Injection Container
Implements Dependency Inversion Principle (SOLID)
"""
from typing import Dict, Type, TypeVar, Callable, Any, Optional
from functools import lru_cache

T = TypeVar('T')


class Container:
    """
    Simple dependency injection container following SOLID principles.
    Supports singleton and transient registrations.
    """
    
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._transient_factories: Dict[Type, Callable] = {}
    
    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Register a singleton instance"""
        self._singletons[interface] = implementation
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], singleton: bool = True) -> None:
        """Register a factory function"""
        if singleton:
            self._factories[interface] = factory
        else:
            self._transient_factories[interface] = factory
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve dependency by interface"""
        # Check singletons
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check singleton factories
        if interface in self._factories:
            instance = self._factories[interface]()
            self._singletons[interface] = instance  # Cache as singleton
            return instance
        
        # Check transient factories
        if interface in self._transient_factories:
            return self._transient_factories[interface]()
        
        raise ValueError(f"No registration found for {interface}")
    
    def is_registered(self, interface: Type[T]) -> bool:
        """Check if interface is registered"""
        return (interface in self._singletons or 
                interface in self._factories or 
                interface in self._transient_factories)


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global dependency injection container"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """Reset the container (useful for testing)"""
    global _container
    _container = None

