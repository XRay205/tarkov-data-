#!/usr/bin/env python3
"""
EFT API Client - Live Daten von Escape from Tarkov abfragen

WICHTIG: Du brauchst einen gültigen EFT-Account!

Verwendung:
1. Installiere requests: pip install requests
2. Setze deine Credentials unten ein
3. Führe das Script aus: python eft_api_client.py
"""

import requests
import json
import zlib
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path


class EFTClient:
    """Escape from Tarkov API Client"""
    
    # Offizielle BSG Backend URL
    BACKEND_URL = "https://prod.escapefromtarkov.com"
    
    # Launcher URL für Login
    LAUNCHER_URL = "https://launcher.escapefromtarkov.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session_id: Optional[str] = None
        
        # Standard Headers wie der offizielle Client
        self.session.headers.update({
            "User-Agent": "UnityPlayer/2021.3.16f1 (UnityWebRequest/1.0, libcurl/7.84.0-DEV)",
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "Content-Type": "application/json",
        })
    
    def _compute_password_hash(self, password: str) -> str:
        """Berechnet den MD5-Hash des Passworts (wie BSG es erwartet)"""
        return hashlib.md5(password.encode()).hexdigest()
    
    def _decompress_response(self, data: bytes) -> str:
        """Dekomprimiert zlib-komprimierte Antworten"""
        try:
            return zlib.decompress(data).decode('utf-8')
        except zlib.error:
            return data.decode('utf-8')
    
    def _request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Führt eine API-Anfrage durch"""
        headers = {}
        
        if self.session_id:
            headers["Cookie"] = f"PHPSESSID={self.session_id}"
        
        if method == "POST" and data:
            response = self.session.post(url, json=data, headers=headers)
        else:
            response = self.session.get(url, headers=headers)
        
        # Versuche zu dekomprimieren
        try:
            content = self._decompress_response(response.content)
            return json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"error": "Failed to parse response", "raw": response.text[:500]}
    
    def login(self, email: str, password: str) -> bool:
        """
        Login beim EFT Launcher
        
        HINWEIS: Dies ist der erste Schritt - du erhältst einen Session-Token
        """
        print(f"[*] Versuche Login für: {email}")
        
        # Passwort hashen wie BSG es erwartet
        password_hash = self._compute_password_hash(password)
        
        login_data = {
            "email": email,
            "pass": password_hash,
            "hwCode": "generated_hardware_code",  # Normalerweise Hardware-ID
            "captcha": None
        }
        
        url = f"{self.LAUNCHER_URL}/launcher/login"
        
        try:
            response = self._request("POST", url, login_data)
            
            if response.get("err") == 0:
                # Session ID aus Response oder Cookie extrahieren
                if "data" in response and "session" in response["data"]:
                    self.session_id = response["data"]["session"]
                    print(f"[+] Login erfolgreich! Session: {self.session_id[:20]}...")
                    return True
            
            print(f"[-] Login fehlgeschlagen: {response}")
            return False
            
        except Exception as e:
            print(f"[-] Login Fehler: {e}")
            return False
    
    def get_globals(self) -> Dict[str, Any]:
        """Holt die globale Spielkonfiguration"""
        url = f"{self.BACKEND_URL}/client/globals"
        return self._request("GET", url)
    
    def get_items(self) -> Dict[str, Any]:
        """Holt alle Items"""
        url = f"{self.BACKEND_URL}/client/items"
        return self._request("GET", url)
    
    def get_locations(self) -> Dict[str, Any]:
        """Holt alle Locations/Maps"""
        url = f"{self.BACKEND_URL}/client/locations"
        return self._request("GET", url)
    
    def get_locale(self, language: str = "en") -> Dict[str, Any]:
        """Holt Lokalisierung für eine Sprache"""
        url = f"{self.BACKEND_URL}/client/locale/{language}"
        return self._request("GET", url)
    
    def get_achievements(self) -> Dict[str, Any]:
        """Holt Achievement-Liste"""
        url = f"{self.BACKEND_URL}/client/achievement/list"
        return self._request("GET", url)
    
    def get_achievement_statistics(self) -> Dict[str, Any]:
        """Holt Achievement-Statistiken"""
        url = f"{self.BACKEND_URL}/client/achievement/statistic"
        return self._request("GET", url)
    
    def get_hideout_areas(self) -> Dict[str, Any]:
        """Holt Hideout-Bereiche"""
        url = f"{self.BACKEND_URL}/client/hideout/areas"
        return self._request("GET", url)
    
    def get_hideout_settings(self) -> Dict[str, Any]:
        """Holt Hideout-Einstellungen"""
        url = f"{self.BACKEND_URL}/client/hideout/settings"
        return self._request("GET", url)
    
    def get_hideout_recipes(self) -> Dict[str, Any]:
        """Holt Crafting-Rezepte"""
        url = f"{self.BACKEND_URL}/client/hideout/production/recipes"
        return self._request("GET", url)
    
    def get_trader_settings(self) -> Dict[str, Any]:
        """Holt Händler-Einstellungen"""
        url = f"{self.BACKEND_URL}/client/trading/api/traderSettings"
        return self._request("GET", url)
    
    def get_customization(self) -> Dict[str, Any]:
        """Holt Charakter-Anpassungen"""
        url = f"{self.BACKEND_URL}/client/customization"
        return self._request("GET", url)
    
    def get_survey(self) -> Dict[str, Any]:
        """Holt aktuelle Umfrage (falls vorhanden)"""
        url = f"{self.BACKEND_URL}/client/survey"
        return self._request("GET", url)
    
    def save_to_file(self, data: Dict[str, Any], filename: str):
        """Speichert Daten in eine JSON-Datei"""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[+] Gespeichert: {filepath}")


def main():
    """Hauptfunktion - Beispiel-Verwendung"""
    
    print("=" * 60)
    print("EFT API Client")
    print("=" * 60)
    
    # =====================================================
    # HIER DEINE CREDENTIALS EINTRAGEN!
    # =====================================================
    EMAIL = "deine_email@example.com"
    PASSWORD = "dein_passwort"
    # =====================================================
    
    client = EFTClient()
    
    # Login versuchen
    if not client.login(EMAIL, PASSWORD):
        print("\n[-] Login fehlgeschlagen!")
        print("\nMögliche Gründe:")
        print("  - Falsche Credentials")
        print("  - 2FA aktiviert (wird nicht unterstützt)")
        print("  - Rate-Limiting / IP-Block")
        print("  - API-Änderungen von BSG")
        return
    
    print("\n[*] Lade Daten...")
    
    # Daten abrufen und speichern
    endpoints = [
        ("globals", client.get_globals),
        ("items", client.get_items),
        ("locations", client.get_locations),
        ("locale_en", lambda: client.get_locale("en")),
        ("achievements", client.get_achievements),
        ("achievement_stats", client.get_achievement_statistics),
        ("hideout_areas", client.get_hideout_areas),
        ("hideout_settings", client.get_hideout_settings),
        ("hideout_recipes", client.get_hideout_recipes),
        ("customization", client.get_customization),
        ("survey", client.get_survey),
    ]
    
    for name, func in endpoints:
        try:
            print(f"\n[*] Lade {name}...")
            data = func()
            
            if "err" in data and data["err"] != 0:
                print(f"[-] Fehler bei {name}: {data.get('errmsg', 'Unbekannt')}")
            else:
                client.save_to_file(data, f"{name}.json")
                
        except Exception as e:
            print(f"[-] Fehler bei {name}: {e}")
    
    print("\n" + "=" * 60)
    print("Fertig!")
    print("=" * 60)


if __name__ == "__main__":
    main()
