class UserError(ValueError):
    """Raise whenever user makes a mistake (config) or malformed input data"""

class TTDConfigError(UserError):
    """Wrong config"""

class TTDInternalError(Exception):
    """Raise when I made a mistake"""
