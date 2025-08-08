"""
Configuration for Location 1: Main Office
"""

# Location-specific settings
LOCATION_ID = 1
LOCATION_NAME = "Main Office"
LOCATION_TIMEZONE = "America/New_York"

# Database settings for this location
DATABASE_URL = "sqlite:///stes_location_1.db"

# Optional: Location-specific settings
FACE_RECOGNITION_TOLERANCE = 0.6
COOLDOWN_MINUTES = 10 