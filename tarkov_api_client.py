#!/usr/bin/env python3
"""
Tarkov API Client - Funktionierender Client für EFT-Daten

Nutzt die öffentliche tarkov.dev GraphQL API.
KEIN LOGIN ERFORDERLICH!

Verwendung:
    pip install requests
    python tarkov_api_client.py
"""

import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class TarkovDevClient:
    """Client für die tarkov.dev GraphQL API"""
    
    API_URL = "https://api.tarkov.dev/graphql"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
    
    def _query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Führt eine GraphQL-Query aus"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = self.session.post(self.API_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # ITEMS
    # =========================================================================
    
    def get_all_items(self, lang: str = "en") -> List[Dict]:
        """Holt alle Items"""
        query = """
        query GetItems($lang: LanguageCode) {
            items(lang: $lang) {
                id
                name
                shortName
                description
                basePrice
                width
                height
                weight
                types
                categories {
                    id
                    name
                }
                wikiLink
                iconLink
                gridImageLink
                image512pxLink
            }
        }
        """
        result = self._query(query, {"lang": lang})
        return result.get("data", {}).get("items", [])
    
    def get_item_by_id(self, item_id: str, lang: str = "en") -> Optional[Dict]:
        """Holt ein Item nach ID"""
        query = """
        query GetItem($id: ID!, $lang: LanguageCode) {
            item(id: $id, lang: $lang) {
                id
                name
                shortName
                description
                basePrice
                width
                height
                weight
                types
                wikiLink
                iconLink
            }
        }
        """
        result = self._query(query, {"id": item_id, "lang": lang})
        return result.get("data", {}).get("item")
    
    def search_items(self, name: str, lang: str = "en") -> List[Dict]:
        """Sucht Items nach Name"""
        query = """
        query SearchItems($name: String!, $lang: LanguageCode) {
            items(name: $name, lang: $lang) {
                id
                name
                shortName
                basePrice
                iconLink
            }
        }
        """
        result = self._query(query, {"name": name, "lang": lang})
        return result.get("data", {}).get("items", [])
    
    # =========================================================================
    # MAPS / LOCATIONS
    # =========================================================================
    
    def get_all_maps(self, lang: str = "en") -> List[Dict]:
        """Holt alle Maps"""
        query = """
        query GetMaps($lang: LanguageCode) {
            maps(lang: $lang) {
                id
                name
                normalizedName
                description
                wiki
                enemies
                raidDuration
                players
                bosses {
                    name
                    normalizedName
                    spawnChance
                    spawnLocations {
                        name
                        chance
                    }
                }
                spawns {
                    zoneName
                    position {
                        x
                        y
                        z
                    }
                    sides
                    categories
                }
                extracts {
                    id
                    name
                    faction
                    switches {
                        id
                        name
                    }
                }
            }
        }
        """
        result = self._query(query, {"lang": lang})
        return result.get("data", {}).get("maps", [])
    
    # =========================================================================
    # TRADERS / HÄNDLER
    # =========================================================================
    
    def get_all_traders(self, lang: str = "en") -> List[Dict]:
        """Holt alle Händler"""
        query = """
        query GetTraders($lang: LanguageCode) {
            traders(lang: $lang) {
                id
                name
                normalizedName
                description
                imageLink
                currency {
                    id
                    name
                }
                resetTime
                levels {
                    id
                    level
                    requiredPlayerLevel
                    requiredReputation
                    requiredCommerce
                }
            }
        }
        """
        result = self._query(query, {"lang": lang})
        return result.get("data", {}).get("traders", [])
    
    # =========================================================================
    # TASKS / QUESTS
    # =========================================================================
    
    def get_all_tasks(self, lang: str = "en") -> List[Dict]:
        """Holt alle Aufgaben"""
        query = """
        query GetTasks($lang: LanguageCode) {
            tasks(lang: $lang) {
                id
                name
                trader {
                    id
                    name
                }
                map {
                    id
                    name
                }
                experience
                minPlayerLevel
                wikiLink
                objectives {
                    id
                    type
                    description
                    optional
                }
            }
        }
        """
        result = self._query(query, {"lang": lang})
        return result.get("data", {}).get("tasks", [])
    
    # =========================================================================
    # HIDEOUT
    # =========================================================================
    
    def get_hideout_stations(self, lang: str = "en") -> List[Dict]:
        """Holt alle Hideout-Stationen"""
        query = """
        query GetHideout($lang: LanguageCode) {
            hideoutStations(lang: $lang) {
                id
                name
                normalizedName
                levels {
                    id
                    level
                    constructionTime
                    itemRequirements {
                        item {
                            id
                            name
                        }
                        count
                    }
                    crafts {
                        id
                        duration
                        rewardItems {
                            item {
                                id
                                name
                            }
                            count
                        }
                        requiredItems {
                            item {
                                id
                                name
                            }
                            count
                        }
                    }
                }
            }
        }
        """
        result = self._query(query, {"lang": lang})
        return result.get("data", {}).get("hideoutStations", [])
    
    # =========================================================================
    # BOSSES
    # =========================================================================
    
    def get_all_bosses(self, lang: str = "en") -> List[Dict]:
        """Holt alle Bosse"""
        query = """
        query GetBosses($lang: LanguageCode) {
            bosses(lang: $lang) {
                name
                normalizedName
                health {
                    id
                    max
                }
                equipment {
                    item {
                        id
                        name
                    }
                }
            }
        }
        """
        result = self._query(query, {"lang": lang})
        return result.get("data", {}).get("bosses", [])
    
    # =========================================================================
    # AMMO / MUNITION
    # =========================================================================
    
    def get_all_ammo(self, lang: str = "en") -> List[Dict]:
        """Holt alle Munitionstypen"""
        query = """
        query GetAmmo($lang: LanguageCode) {
            ammo(lang: $lang) {
                item {
                    id
                    name
                    shortName
                }
                caliber
                damage
                armorDamage
                penetrationPower
                penetrationChance
                ricochetChance
                fragmentationChance
                projectileCount
                tracer
                tracerColor
            }
        }
        """
        result = self._query(query, {"lang": lang})
        return result.get("data", {}).get("ammo", [])
    
    # =========================================================================
    # BARTER TRADES
    # =========================================================================
    
    def get_barters(self, lang: str = "en") -> List[Dict]:
        """Holt alle Barter-Trades"""
        query = """
        query GetBarters($lang: LanguageCode) {
            barters(lang: $lang) {
                id
                trader {
                    id
                    name
                }
                level
                rewardItems {
                    item {
                        id
                        name
                    }
                    count
                }
                requiredItems {
                    item {
                        id
                        name
                    }
                    count
                }
            }
        }
        """
        result = self._query(query, {"lang": lang})
        return result.get("data", {}).get("barters", [])
    
    # =========================================================================
    # FLEA MARKET PREISE
    # =========================================================================
    
    def get_flea_prices(self, item_ids: List[str] = None) -> List[Dict]:
        """Holt aktuelle Flohmarkt-Preise"""
        if item_ids:
            query = """
            query GetPrices($ids: [ID!]) {
                items(ids: $ids) {
                    id
                    name
                    avg24hPrice
                    low24hPrice
                    high24hPrice
                    lastLowPrice
                    changeLast48h
                    changeLast48hPercent
                }
            }
            """
            result = self._query(query, {"ids": item_ids})
        else:
            query = """
            {
                items {
                    id
                    name
                    avg24hPrice
                    low24hPrice
                    high24hPrice
                    lastLowPrice
                }
            }
            """
            result = self._query(query)
        return result.get("data", {}).get("items", [])
    
    # =========================================================================
    # HILFSMETHODEN
    # =========================================================================
    
    def save_to_file(self, data: Any, filename: str):
        """Speichert Daten in JSON-Datei"""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[+] Gespeichert: {filepath} ({len(json.dumps(data))} bytes)")
        return filepath


def main():
    """Beispiel-Verwendung"""
    
    print("=" * 60)
    print("Tarkov.dev API Client")
    print("=" * 60)
    
    client = TarkovDevClient()
    
    # Sprache wählen (en, de, ru, fr, etc.)
    LANG = "en"
    
    print(f"\n[*] Sprache: {LANG}")
    print("[*] Lade Daten von tarkov.dev...\n")
    
    # Alle Daten abrufen
    datasets = [
        ("items", lambda: client.get_all_items(LANG)),
        ("maps", lambda: client.get_all_maps(LANG)),
        ("traders", lambda: client.get_all_traders(LANG)),
        ("tasks", lambda: client.get_all_tasks(LANG)),
        ("hideout", lambda: client.get_hideout_stations(LANG)),
        ("bosses", lambda: client.get_all_bosses(LANG)),
        ("ammo", lambda: client.get_all_ammo(LANG)),
        ("barters", lambda: client.get_barters(LANG)),
    ]
    
    for name, func in datasets:
        try:
            print(f"[*] Lade {name}...")
            data = func()
            client.save_to_file(data, f"{name}_{LANG}.json")
            print(f"    → {len(data)} Einträge")
        except Exception as e:
            print(f"[-] Fehler bei {name}: {e}")
    
    print("\n" + "=" * 60)
    
    # Beispiel: Item-Suche
    print("\n[*] Beispiel: Suche nach 'AK-47'")
    results = client.search_items("AK-47", LANG)
    for item in results[:5]:
        print(f"    - {item['name']} ({item['shortName']}) - {item['basePrice']} ₽")
    
    # Beispiel: Flohmarkt-Preise
    print("\n[*] Beispiel: Aktuelle Preise für erste 3 Items")
    if results:
        prices = client.get_flea_prices([r['id'] for r in results[:3]])
        for p in prices:
            print(f"    - {p['name']}: Ø {p['avg24hPrice']} ₽ (24h)")
    
    print("\n" + "=" * 60)
    print("Fertig! Daten in ./output/ gespeichert.")
    print("=" * 60)


if __name__ == "__main__":
    main()
