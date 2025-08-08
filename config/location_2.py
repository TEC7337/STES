"""
Configuration for Location 2: Branch Office
"""

# Location-specific settings
LOCATION_ID = 2
LOCATION_NAME = "Branch Office"
LOCATION_TIMEZONE = "America/Chicago"

# Database settings for this location
DATABASE_URL = "sqlite:///stes_location_2.db"

# Optional: Location-specific settings
FACE_RECOGNITION_TOLERANCE = 0.6
COOLDOWN_MINUTES = 10 