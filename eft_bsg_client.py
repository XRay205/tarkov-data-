#!/usr/bin/env python3
"""
EFT BSG API Client - Direkter Zugriff auf BSG Server

Basiert auf: https://github.com/matthewlilley/escape-from-tarkov

WICHTIG: 
- Du brauchst einen gültigen EFT-Account
- Bei erstmaliger Nutzung auf neuem Gerät: 2FA-Code per Email
- Nutze auf eigene Gefahr!

Verwendung:
    pip install requests
    python eft_bsg_client.py
"""

import os
import json
import zlib
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Any, Optional
import requests


class EFTLauncher:
    """BSG Launcher API Client"""
    
    LAUNCHER_URL = "https://launcher.escapefromtarkov.com"
    PROD_URL = "https://prod.escapefromtarkov.com"
    
    def __init__(self, email: str, password: str, 
                 launcher_version: str = "14.7.2.4271",
                 client_version: str = "1.0.1.0.42625",
                 unity_version: str = "2021.3.16f1"):
        
        self.email = email
        self.password = password
        self.launcher_version = launcher_version
        self.client_version = client_version
        self.unity_version = unity_version
        
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.game_session: Optional[str] = None
        
        # Storage für Hardware-Code
        self.storage_path = Path(".eft_storage") / self._safe_email()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.hw_code = self._get_or_create_hw_code()
    
    def _safe_email(self) -> str:
        """Email für Dateinamen sicher machen"""
        return hashlib.md5(self.email.encode()).hexdigest()[:12]
    
    def _get_or_create_hw_code(self) -> str:
        """Hardware-Code laden oder neu generieren"""
        hw_file = self.storage_path / "hwcode.txt"
        
        if hw_file.exists():
            return hw_file.read_text().strip()
        
        # Generiere neuen Hardware-Code im BSG-Format
        hw_code = self._generate_hw_code()
        hw_file.write_text(hw_code)
        return hw_code
    
    def _generate_hw_code(self) -> str:
        """
        Generiert Hardware-Code im BSG-Format:
        #1-{md5}:{md5}:{md5}-{md5}-{md5}-{md5}-{md5}-{md5[:24]}
        """
        def random_md5():
            return hashlib.md5(secrets.token_bytes(16)).hexdigest()
        
        part1 = ":".join([random_md5() for _ in range(3)])
        part2 = "-".join([random_md5() for _ in range(4)])
        part3 = random_md5()[:24]
        
        return f"#1-{part1}-{part2}-{part3}"
    
    def _md5_password(self) -> str:
        """Passwort MD5 hashen (wie BSG es erwartet)"""
        return hashlib.md5(self.password.encode()).hexdigest()
    
    def _launcher_headers(self) -> Dict[str, str]:
        """Headers für Launcher-Requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"BSG Launcher {self.launcher_version}",
        }
        if self.token:
            headers["Authorization"] = self.token
        return headers
    
    def _client_headers(self) -> Dict[str, str]:
        """Headers für Client-Requests"""
        return {
            "Content-Type": "application/json",
            "User-Agent": f"UnityPlayer/{self.unity_version} (UnityWebRequest/1.0, libcurl/7.52.0-DEV)",
            "App-Version": f"EFT Client {self.client_version}",
            "X-Unity-Version": self.unity_version,
            "Cookie": f"PHPSESSID={self.game_session}",
        }
    
    def _request(self, url: str, data: Optional[Dict] = None, 
                 use_client_headers: bool = False) -> Dict[str, Any]:
        """Führt Request durch und dekomprimiert Response"""
        
        headers = self._client_headers() if use_client_headers else self._launcher_headers()
        
        if data:
            response = self.session.post(url, json=data, headers=headers, timeout=30)
        else:
            response = self.session.get(url, headers=headers, timeout=30)
        
        # Response dekomprimieren (BSG nutzt zlib)
        try:
            content = zlib.decompress(response.content)
            return json.loads(content.decode('utf-8'))
        except zlib.error:
            try:
                return response.json()
            except:
                return {"error": "Parse error", "raw": response.text[:500], "status": response.status_code}
    
    def login(self) -> bool:
        """
        Login beim BSG Launcher
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        print(f"[*] Login für: {self.email}")
        print(f"[*] Hardware-Code: {self.hw_code[:30]}...")
        
        url = f"{self.LAUNCHER_URL}/launcher/login?launcherVersion={self.launcher_version}&branch=live"
        
        data = {
            "email": self.email,
            "pass": self._md5_password(),
            "hwCode": self.hw_code,
        }
        
        response = self._request(url, data)
        
        if response.get("err") == 0 and "data" in response:
            self.token = response["data"].get("access_token")
            print(f"[+] Login erfolgreich!")
            print(f"[+] Token: {self.token[:30]}..." if self.token else "[-] Kein Token erhalten")
            return True
        
        # Fehlerbehandlung
        err_code = response.get("err")
        err_msg = response.get("errmsg", "Unbekannt")
        
        if err_code == 209:
            print(f"\n[!] Hardware-Aktivierung erforderlich!")
            print(f"[!] Prüfe deine Email für den Aktivierungscode.")
            print(f"[!] Nutze activate_hardware('CODE') um fortzufahren.")
        elif err_code == 206:
            print(f"[-] Captcha erforderlich - kann nicht automatisiert werden")
        elif err_code == 211:
            print(f"[-] Falsches Passwort")
        else:
            print(f"[-] Login fehlgeschlagen: {err_code} - {err_msg}")
            print(f"[-] Response: {response}")
        
        return False
    
    def activate_hardware(self, code: str) -> bool:
        """
        Hardware-Code aktivieren (für neue Geräte)
        
        Args:
            code: Aktivierungscode aus Email
        """
        print(f"[*] Aktiviere Hardware mit Code: {code}")
        
        url = f"{self.LAUNCHER_URL}/launcher/hardwareCode/activate?launcherVersion={self.launcher_version}"
        
        data = {
            "email": self.email,
            "hwCode": self.hw_code,
            "activateCode": code,
        }
        
        response = self._request(url, data)
        
        if response.get("err") == 0:
            print("[+] Hardware aktiviert!")
            return True
        
        print(f"[-] Aktivierung fehlgeschlagen: {response}")
        return False
    
    def start_game(self) -> bool:
        """
        Startet Game-Session (nach Login)
        
        Returns:
            True wenn Session erhalten, False sonst
        """
        if not self.token:
            print("[-] Kein Token - bitte erst einloggen!")
            return False
        
        print("[*] Starte Game-Session...")
        
        url = f"{self.PROD_URL}/launcher/game/start?launcherVersion={self.launcher_version}&branch=live"
        
        data = {
            "version": {
                "major": self.client_version,
                "game": "live",
                "backend": "6",
            },
            "hwCode": self.hw_code,
        }
        
        response = self._request(url, data)
        
        if response.get("err") == 0 and "data" in response:
            self.game_session = response["data"].get("session")
            print(f"[+] Game-Session erhalten!")
            print(f"[+] Session: {self.game_session[:30]}..." if self.game_session else "")
            return True
        
        print(f"[-] Game-Start fehlgeschlagen: {response}")
        return False


class EFTClient:
    """BSG Game Client API"""
    
    PROD_URL = "https://prod.escapefromtarkov.com"
    
    def __init__(self, launcher: EFTLauncher):
        self.launcher = launcher
        self.request_id = 0
    
    def _headers(self) -> Dict[str, str]:
        """Client Headers mit Request-ID"""
        self.request_id += 1
        headers = self.launcher._client_headers()
        headers["GClient-RequestId"] = str(self.request_id)
        return headers
    
    def _request(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Client-Request durchführen"""
        url = f"{self.PROD_URL}{endpoint}"
        headers = self._headers()
        
        try:
            if data:
                response = requests.post(url, json=data, headers=headers, timeout=60)
            else:
                response = requests.get(url, headers=headers, timeout=60)
            
            # Dekomprimieren
            try:
                content = zlib.decompress(response.content)
                return json.loads(content.decode('utf-8'))
            except zlib.error:
                return response.json()
                
        except Exception as e:
            return {"error": str(e)}
    
    # =========================================================================
    # DIE ENDPUNKTE DIE DU BRAUCHST
    # =========================================================================
    
    def get_globals(self) -> Dict[str, Any]:
        """client/globals - Globale Spielkonfiguration"""
        return self._request("/client/globals")
    
    def get_items(self) -> Dict[str, Any]:
        """client/items - Alle Items"""
        return self._request("/client/items")
    
    def get_locale(self, lang: str = "en") -> Dict[str, Any]:
        """client/locale/{lang} - Lokalisierung"""
        return self._request(f"/client/locale/{lang}")
    
    def get_achievements(self) -> Dict[str, Any]:
        """client/achievement/list - Achievement-Liste"""
        return self._request("/client/achievement/list")
    
    def get_achievement_statistics(self) -> Dict[str, Any]:
        """client/achievement/statistic - Achievement-Statistiken"""
        return self._request("/client/achievement/statistic")
    
    def get_survey(self) -> Dict[str, Any]:
        """client/survey - Aktuelle Umfrage"""
        return self._request("/client/survey")
    
    # =========================================================================
    # WEITERE ENDPUNKTE
    # =========================================================================
    
    def get_locations(self) -> Dict[str, Any]:
        """client/locations - Alle Maps"""
        return self._request("/client/locations")
    
    def get_profiles(self) -> Dict[str, Any]:
        """client/game/profile/list - Spieler-Profile"""
        return self._request("/client/game/profile/list")
    
    def get_hideout_areas(self) -> Dict[str, Any]:
        """client/hideout/areas - Hideout-Bereiche"""
        return self._request("/client/hideout/areas")
    
    def get_hideout_settings(self) -> Dict[str, Any]:
        """client/hideout/settings - Hideout-Einstellungen"""
        return self._request("/client/hideout/settings")
    
    def get_hideout_recipes(self) -> Dict[str, Any]:
        """client/hideout/production/recipes - Crafting-Rezepte"""
        return self._request("/client/hideout/production/recipes")
    
    def get_trader_settings(self) -> Dict[str, Any]:
        """client/trading/api/traderSettings - Händler-Einstellungen"""
        return self._request("/client/trading/api/traderSettings")
    
    def get_customization(self) -> Dict[str, Any]:
        """client/customization - Charakter-Anpassungen"""
        return self._request("/client/customization")
    
    def get_weather(self) -> Dict[str, Any]:
        """client/weather - Wetter"""
        return self._request("/client/weather")
    
    def get_handbook(self) -> Dict[str, Any]:
        """client/handbook/templates - Handbuch"""
        return self._request("/client/handbook/templates")
    
    # =========================================================================
    # HILFSMETHODEN
    # =========================================================================
    
    def save_response(self, data: Dict[str, Any], filename: str):
        """Speichert Response in Datei"""
        output_dir = Path("bsg_output")
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        size = filepath.stat().st_size
        print(f"[+] Gespeichert: {filepath} ({size:,} bytes)")


def main():
    """Hauptfunktion"""
    
    print("=" * 70)
    print("EFT BSG API Client")
    print("=" * 70)
    
    # =========================================================================
    # KONFIGURATION - HIER ANPASSEN!
    # =========================================================================
    
    EMAIL = os.environ.get("EFT_EMAIL", "deine_email@example.com")
    PASSWORD = os.environ.get("EFT_PASSWORD", "dein_passwort")
    
    # Versionen aus dem Repository
    LAUNCHER_VERSION = "14.7.2.4271"  # Aus launcher_version.txt
    CLIENT_VERSION = "1.0.1.0.42625"  # Aus game_version.txt
    UNITY_VERSION = "2021.3.16f1"
    
    # =========================================================================
    
    if EMAIL == "deine_email@example.com":
        print("\n[!] Bitte konfiguriere deine Credentials!")
        print("[!] Entweder im Script oder via Umgebungsvariablen:")
        print("    export EFT_EMAIL='deine@email.com'")
        print("    export EFT_PASSWORD='dein_passwort'")
        return
    
    # Launcher initialisieren
    launcher = EFTLauncher(
        email=EMAIL,
        password=PASSWORD,
        launcher_version=LAUNCHER_VERSION,
        client_version=CLIENT_VERSION,
        unity_version=UNITY_VERSION,
    )
    
    # Login
    print("\n" + "-" * 70)
    print("SCHRITT 1: Login")
    print("-" * 70)
    
    if not launcher.login():
        print("\n[!] Falls Hardware-Aktivierung nötig:")
        print("    1. Prüfe deine Email für den Code")
        print("    2. Führe aus: launcher.activate_hardware('DEIN_CODE')")
        print("    3. Versuche erneut: launcher.login()")
        return
    
    # Game Session starten
    print("\n" + "-" * 70)
    print("SCHRITT 2: Game Session")
    print("-" * 70)
    
    if not launcher.start_game():
        return
    
    # Client erstellen
    client = EFTClient(launcher)
    
    # Daten abrufen
    print("\n" + "-" * 70)
    print("SCHRITT 3: Daten abrufen")
    print("-" * 70)
    
    endpoints = [
        ("globals", client.get_globals),
        ("items", client.get_items),
        ("locale_en", lambda: client.get_locale("en")),
        ("achievements", client.get_achievements),
        ("achievement_stats", client.get_achievement_statistics),
        ("survey", client.get_survey),
        ("locations", client.get_locations),
        ("hideout_areas", client.get_hideout_areas),
        ("hideout_settings", client.get_hideout_settings),
        ("hideout_recipes", client.get_hideout_recipes),
        ("customization", client.get_customization),
    ]
    
    for name, func in endpoints:
        print(f"\n[*] Lade {name}...")
        try:
            data = func()
            
            if data.get("err") == 0:
                client.save_response(data, f"{name}.json")
            else:
                print(f"[-] Fehler: {data.get('errmsg', data)}")
                
        except Exception as e:
            print(f"[-] Exception: {e}")
    
    print("\n" + "=" * 70)
    print("Fertig! Daten in ./bsg_output/ gespeichert.")
    print("=" * 70)


if __name__ == "__main__":
    main()
