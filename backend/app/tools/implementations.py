import ast
import math
import operator
from typing import Dict, Any, List, Optional
import httpx
from duckduckgo_search import DDGS

from app.tools.schemas import WebSearchInput, WeatherSearchInput, CalculatorInput


# ==============================================================================
# 1. Web Search Tool
# ==============================================================================
def execute_web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for up-to-date information, articles, and documentation.
    Gracefully catches timeouts, network issues, and throttles.
    """
    try:
        validated = WebSearchInput(query=query, max_results=max_results)
    except Exception as e:
        return f"Input Schema Error: Invalid web search parameters. Details: {str(e)}"

    clean_query = validated.query.strip()
    if not clean_query:
        return "Error: Search query cannot be empty."

    try:
        results = []
        with DDGS(timeout=10) as ddgs:
            raw_results = list(ddgs.text(clean_query, max_results=validated.max_results))
            for item in raw_results:
                results.append(
                    f"• Title: {item.get('title', 'No Title')}\n"
                    f"  Snippet: {item.get('body', 'No summary')}\n"
                    f"  URL: {item.get('href', 'N/A')}"
                )

        if not results:
            return f"No direct web results found for query: '{clean_query}'. Suggest refining search keywords."

        return f"Search Results for '{clean_query}':\n\n" + "\n\n".join(results)

    except Exception as exc:
        # Fallback graceful notification if external DDG is rate-limited
        return (
            f"Notice: Web search service encountered an external issue ({type(exc).__name__}: {str(exc)}). "
            f"The agent should proceed using relevant domain knowledge or try an alternate query."
        )


# ==============================================================================
# 2. Weather API Tool (Open-Meteo with optional OpenWeather fallback)
# ==============================================================================
WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def execute_weather_search(location: str, units: str = "metric") -> str:
    """
    Fetch current weather and 3-day forecast for any global city.
    Uses geocoding and the Open-Meteo meteorological API.
    """
    try:
        validated = WeatherSearchInput(location=location, units=units)
    except Exception as e:
        return f"Input Schema Error: Invalid weather search parameters. Details: {str(e)}"

    city_query = validated.location.split(",")[0].strip()
    is_imperial = validated.units.lower() == "imperial"
    temp_unit = "°F" if is_imperial else "°C"
    speed_unit = "mph" if is_imperial else "km/h"

    try:
        # Step 1: Geocode location
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_query}&count=1&language=en&format=json"
        with httpx.Client(timeout=8.0) as client:
            geo_resp = client.get(geocode_url)
            if geo_resp.status_code != 200:
                return f"Error: Geocoding service returned HTTP {geo_resp.status_code} for location '{validated.location}'."

            geo_data = geo_resp.json()
            results = geo_data.get("results")
            if not results:
                return f"Error: Location '{validated.location}' not found. Please provide a recognized city name."

            loc_info = results[0]
            lat = loc_info.get("latitude")
            lon = loc_info.get("longitude")
            resolved_name = f"{loc_info.get('name')}, {loc_info.get('country', '')}"

            # Step 2: Fetch weather forecast
            temp_param = "&temperature_unit=fahrenheit&wind_speed_unit=mph" if is_imperial else ""
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                f"&timezone=auto{temp_param}"
            )
            weather_resp = client.get(weather_url)
            if weather_resp.status_code != 200:
                return f"Error: Weather service returned HTTP {weather_resp.status_code}."

            w_data = weather_resp.json()
            curr = w_data.get("current_weather", {})
            daily = w_data.get("daily", {})

            curr_temp = curr.get("temperature", "N/A")
            wind_speed = curr.get("windspeed", "N/A")
            weather_code = curr.get("weathercode", 0)
            condition = WEATHER_CODE_MAP.get(weather_code, "Partly cloudy")

            forecast_lines = []
            dates = daily.get("time", [])[:3]
            t_max = daily.get("temperature_2m_max", [])[:3]
            t_min = daily.get("temperature_2m_min", [])[:3]
            precip = daily.get("precipitation_probability_max", [])[:3]

            for i in range(min(len(dates), 3)):
                date_str = dates[i]
                high = t_max[i] if i < len(t_max) else "N/A"
                low = t_min[i] if i < len(t_min) else "N/A"
                rain_prob = f"{precip[i]}%" if i < len(precip) and precip[i] is not None else "N/A"
                forecast_lines.append(f"  - {date_str}: High {high}{temp_unit}, Low {low}{temp_unit}, Precip Chance: {rain_prob}")

            output = (
                f"Weather Report for {resolved_name}:\n"
                f"• Condition: {condition}\n"
                f"• Current Temperature: {curr_temp}{temp_unit}\n"
                f"• Wind Speed: {wind_speed} {speed_unit}\n"
                f"• 3-Day Forecast:\n" + "\n".join(forecast_lines)
            )
            return output

    except httpx.RequestError as req_err:
        return f"Error: Weather network connection failed ({str(req_err)}). Please try again."
    except Exception as exc:
        return f"Error: Failed to retrieve weather data for '{location}': {str(exc)}"


# ==============================================================================
# 3. Calculator / Safe Math Evaluation Tool
# ==============================================================================
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
}

SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval_ast(node):
    if isinstance(node, ast.Expression):
        return _safe_eval_ast(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")
    elif isinstance(node, ast.Name):
        if node.id in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[node.id]
        raise ValueError(f"Undefined variable or constant: '{node.id}'")
    elif isinstance(node, ast.UnaryOp):
        op = type(node.op)
        if op in SAFE_OPERATORS:
            return SAFE_OPERATORS[op](_safe_eval_ast(node.operand))
        raise ValueError(f"Unsupported unary operator: {op.__name__}")
    elif isinstance(node, ast.BinOp):
        op = type(node.op)
        if op in SAFE_OPERATORS:
            left = _safe_eval_ast(node.left)
            right = _safe_eval_ast(node.right)
            if op == ast.Pow and (right > 100 or left > 100000):
                raise ValueError("Exponentiation values too large to evaluate safely.")
            return SAFE_OPERATORS[op](left, right)
        raise ValueError(f"Unsupported binary operator: {op.__name__}")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
            func = SAFE_FUNCTIONS[node.func.id]
            args = [_safe_eval_ast(arg) for arg in node.args]
            return func(*args)
        raise ValueError(f"Function '{getattr(node.func, 'id', 'unknown')}' is not allowed or supported.")
    elif isinstance(node, ast.List):
        return [_safe_eval_ast(elem) for elem in node.elts]
    else:
        raise ValueError(f"Unsupported syntax expression: {type(node).__name__}")


def execute_calculator(expression: str, description: Optional[str] = None) -> str:
    """
    Safely evaluate arithmetic, statistical, and algebraic expressions.
    """
    try:
        validated = CalculatorInput(expression=expression, description=description)
    except Exception as e:
        return f"Input Schema Error: Invalid calculator parameters. Details: {str(e)}"

    expr = validated.expression.strip()
    if not expr:
        return "Error: Expression cannot be empty."

    try:
        parsed = ast.parse(expr, mode="eval")
        result = _safe_eval_ast(parsed)
        desc_str = f" ({validated.description})" if validated.description else ""
        return f"Calculation Result{desc_str}: {expr} = {result}"
    except ZeroDivisionError:
        return f"Math Error: Division by zero encountered in expression '{expr}'."
    except SyntaxError:
        return f"Syntax Error: Could not parse mathematical expression '{expr}'. Please check syntax."
    except Exception as exc:
        return f"Evaluation Error in '{expr}': {str(exc)}"


# Tool Dispatcher
TOOL_REGISTRY = {
    "web_search": execute_web_search,
    "weather_search": execute_weather_search,
    "calculator": execute_calculator,
}


def run_tool_by_name(tool_name: str, kwargs: Dict[str, Any]) -> str:
    """Execute a registered tool by string name with keyword arguments."""
    tool_func = TOOL_REGISTRY.get(tool_name)
    if not tool_func:
        available = ", ".join(TOOL_REGISTRY.keys())
        return f"Error: Unknown tool '{tool_name}'. Available tools: {available}"
    try:
        return tool_func(**kwargs)
    except Exception as exc:
        return f"Execution Error in tool '{tool_name}': {str(exc)}"
