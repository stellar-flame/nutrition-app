"""Utils package for the nutrition app backend."""

# Import all utility functions to maintain existing import patterns
from .auth import get_firebase_app, verify_firebase_token
from .calculations import extract_number, calculate_bmr, calculate_age
from .secrets import get_secret, get_api_keys
