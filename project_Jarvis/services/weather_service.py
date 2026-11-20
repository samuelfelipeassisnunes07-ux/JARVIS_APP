from typing import Any, Dict, Optional

import requests

from config.settings import settings


class WeatherService:
    """Consulta o clima atual sem interferir no fluxo de conversa."""

    def __init__(self):
        self.api_key = settings.get("OPENWEATHER_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def current_weather(self, city: str, country_code: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OPENWEATHER_API_KEY não configurada")

        location = f"{city},{country_code}" if country_code else city
        response = requests.get(
            self.base_url,
            params={"q": location, "appid": self.api_key, "units": "metric", "lang": "pt_br"},
            timeout=10,
        )
        if response.status_code == 404:
            raise ValueError(f"Cidade não encontrada: {city}")
        response.raise_for_status()
        data = response.json()
        return {
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "description": data.get("weather", [{}])[0].get("description", ""),
            "humidity": data.get("main", {}).get("humidity"),
            "wind_speed": data.get("wind", {}).get("speed"),
        }

    def format_current_weather(self, city: str, country_code: Optional[str] = None) -> str:
        weather = self.current_weather(city, country_code)
        return (
            f"Clima em {weather['city']} ({weather['country']}): "
            f"{weather['description']}, {weather['temperature']} °C "
            f"(sensação de {weather['feels_like']} °C), "
            f"umidade de {weather['humidity']}% e vento de {weather['wind_speed']} m/s."
        )
