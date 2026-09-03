from typing import Optional
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    """Input schema for the Web Search Tool."""
    query: str = Field(
        description="The precise search query to search across the web (e.g., 'Tokyo cherry blossom season 2025 tips', 'latest advancements in quantum computing')."
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of search results to return (between 1 and 10)."
    )


class WeatherSearchInput(BaseModel):
    """Input schema for the Weather Search Tool."""
    location: str = Field(
        description="The city name and optional country code (e.g., 'Tokyo, Japan', 'San Francisco, US', 'London, UK')."
    )
    units: str = Field(
        default="metric",
        description="Temperature and speed measurement units: 'metric' (Celsius, km/h) or 'imperial' (Fahrenheit, mph)."
    )


class CalculatorInput(BaseModel):
    """Input schema for the Mathematical & Financial Calculator Tool."""
    expression: str = Field(
        description="A mathematical or statistical expression to safely evaluate (e.g., '1500 * (1 + 0.08)**5', 'sqrt(144) + 25 * 3', 'sum([120, 145, 160]) / 3')."
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional brief context of what this calculation represents (e.g., '5-year compound growth at 8%')."
    )
