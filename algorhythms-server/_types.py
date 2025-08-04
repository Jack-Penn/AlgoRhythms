from typing import Any
from pydantic import GetCoreSchemaHandler
from pydantic_core.core_schema import CoreSchema, no_info_plain_validator_function, to_string_ser_schema

class PydanticStringID(str):
    """
    A base class for string-based IDs that teaches Pydantic how to handle them.
    It automatically validates from a string and serializes back to a string.
    """
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """
        Defines how Pydantic should handle this type.
        
        We are telling Pydantic that to validate this type, it should simply
        call the class's constructor (e.g., ReccoTrackID(some_string)).
        
        We also provide a serialization rule to convert it back to a plain string.
        """
        return no_info_plain_validator_function(
            cls, # The validation function is the constructor itself.
            serialization=to_string_ser_schema()
        )

class NamedStringType(PydanticStringID):
    """Explicit type representing a specific, named string."""
    pass

class SpotifyTrackURI (NamedStringType):
    def __new__(cls, value: str) -> "SpotifyTrackURI":
        if not isinstance(value, str) or not value.startswith("spotify:track:"):
            raise ValueError("SpotifyTrackURI must start with 'spotify:track:'")
        return str.__new__(cls, value)
        

class SpotifyTrackID (NamedStringType):
    """Explicit type representing a Spotify Track ID."""
    def get_uri(self):
        return SpotifyTrackURI(f"spotify:track:{self}")
