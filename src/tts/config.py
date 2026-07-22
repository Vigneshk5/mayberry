"""
Configuration and constants for TTS.
"""

SAMPLE_RATE = 24000

VOICES = {
    "american_female": ["af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky"],
    "american_male": ["am_adam", "am_michael"],
    "british_female": ["bf_emma", "bf_isabella"],
    "british_male": ["bm_george", "bm_lewis"],
}

LANGUAGES = {
    "a": "American English",
    "b": "British English",
    "e": "Spanish",
    "f": "French",
    "h": "Hindi",
    "i": "Italian",
    "j": "Japanese",
    "p": "Brazilian Portuguese",
    "z": "Mandarin Chinese",
}

DEFAULT_VOICE = "af_heart"
DEFAULT_LANG = "a"
DEFAULT_SPEED = 1.0
