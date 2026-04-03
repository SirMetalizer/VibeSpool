# core/colors.py

# Eine zentrale, mächtige Zuordnung von Hex-Codes zu schönen deutschen Namen.
# Speziell optimiert für typische 3D-Druck Filament-Farben!
HEX_TO_NAME = {
    # --- Schwarz, Weiß & Grautöne ---
    "#000000": "Schwarz",
    "#1C1C1C": "Anthrazit",
    "#2F4F4F": "Schiefergrau",
    "#696969": "Dunkelgrau",
    "#808080": "Grau",
    "#A9A9A9": "Mittelgrau",
    "#D3D3D3": "Hellgrau",
    "#FFFFFF": "Weiß",
    "#F5F5F5": "Rauchweiß",

    # --- Metall- & Spezialtöne ---
    "#C0C0C0": "Silber",
    "#FFD700": "Gold",
    "#B87333": "Kupfer",
    "#CD7F32": "Bronze",
    "#E5E4E2": "Platin",
    "#B7410E": "Rost",

    # --- Natur, Beige & Braun ---
    "#F5F5DC": "Beige",
    "#FFFFF0": "Elfenbein",
    "#E3DAC9": "Knochenweiß",
    "#D2B48C": "Hellbraun (Tan)",
    "#DEB887": "Holz / Sand",
    "#A52A2A": "Braun",
    "#8B4513": "Sattelbraun",
    "#3D0C02": "Dunkelbraun",
    "#7B3F00": "Schokobraun",

    # --- Rot & Orange ---
    "#FF0000": "Rot",
    "#DC143C": "Karmesinrot",
    "#B22222": "Ziegelrot",
    "#8B0000": "Dunkelrot",
    "#800000": "Weinrot",
    "#E2725B": "Terracotta",
    "#FF4500": "Orangerot",
    "#FFA500": "Orange",
    "#FF8C00": "Dunkelorange",

    # --- Gelb ---
    "#FFFF00": "Gelb",
    "#FFD700": "Sonnengelb",
    "#FFDB58": "Senfgelb",
    "#FFF700": "Zitronengelb",

    # --- Grün ---
    "#008000": "Grün",
    "#00FF00": "Limette",
    "#32CD32": "Hellgrün",
    "#228B22": "Waldgrün",
    "#006400": "Dunkelgrün",
    "#808000": "Olivgrün",
    "#556B2F": "Dunkeloliv",
    "#98FF98": "Mintgrün",
    "#00A86B": "Jade",
    "#50C878": "Smaragdgrün",

    # --- Blau & Cyan ---
    "#0000FF": "Blau",
    "#000080": "Marineblau",
    "#00008B": "Dunkelblau",
    "#4169E1": "Königsblau",
    "#1E90FF": "Dodgerblau",
    "#87CEEB": "Himmelblau",
    "#B0E0E6": "Eisblau",
    "#00FFFF": "Cyan",
    "#40E0D0": "Türkis",
    "#008080": "Krickente (Teal)",
    "#0F52BA": "Saphirblau",

    # --- Pink, Lila & Violett ---
    "#FFC0CB": "Pink",
    "#FF69B4": "Hot Pink",
    "#FF1493": "Tiefpink",
    "#FF00FF": "Magenta",
    "#800080": "Lila",
    "#8A2BE2": "Blauviolett",
    "#9932CC": "Dunkel-Orchidee",
    "#4B0082": "Indigo",
    "#E6E6FA": "Lavendel",
    "#C8A2C8": "Flieder",
    "#8E4585": "Pflaume",
    "#9966CC": "Amethyst"
}

def get_color_name_from_hex(hex_code):
    """
    Sucht den passenden Namen zu einem Hex-Code.
    Gibt einen leeren String zurück, wenn der Code nicht bekannt ist.
    """
    if not hex_code:
        return ""
    
    # Wir machen den Hex-Code groß, damit #ff0000 und #FF0000 gleich behandelt werden
    return HEX_TO_NAME.get(hex_code.upper(), "")