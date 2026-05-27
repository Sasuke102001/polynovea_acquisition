from pathlib import Path

SEGMENTS = [
    "office_workers", "college_kids", "couples",
    "families", "premium", "solo_diners", "working_women",
]

CHANNELS = [
    "instagram_organic", "instagram_ads", "google_ads",
    "whatsapp", "email", "sms", "zomato_swiggy",
]

ARCHETYPES = [
    "party_seeker", "scene_seeker", "trend_hunter",
    "premium_prioritizer", "habit_former", "lifestyle_regular",
    "quiet_discoverer", "power_regular", "trusted_regular",
    "social_butterfly", "comfort_dweller",
]

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
EXTRACT_MODEL_ENV = "NVIDIA_MODEL_EXTRACTION"
EXTRACT_MODEL_DEFAULT = "meta/llama-3.3-70b-instruct"

ROOT = Path(__file__).parent.parent          # Acquistion System/
RESEARCH_DIR = ROOT / "research"
OUTPUT_DIR = Path(__file__).parent / "output"
CACHE_FILE = OUTPUT_DIR / ".cache.json"

MAX_CHUNK_CHARS = 3500
MIN_SECTION_CHARS = 150
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 2000
