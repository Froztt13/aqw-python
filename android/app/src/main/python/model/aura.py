from datetime import datetime, timedelta
from typing import Optional
from core.utils import normalize

class Aura:
    def __init__(self, aura):
        duration: int = aura.get('dur', 0)
        timestamp: datetime = datetime.now()
        expiration_time: datetime = timestamp + timedelta(seconds=duration)

        self.name: str = normalize(aura.get('nam'))
        self.aura_type: str = aura.get('t')
        self.duration: int = duration
        self.source_spell: Optional[str] = aura.get('spellOn', None)
        self.icon: str = aura.get('icon')
        self.applied_time: datetime = timestamp
        self.expires_at: datetime = expiration_time
        self.aura_val: int = 1

    def refresh(self, duration: Optional[int] = None):
        """Refresh the aura's applied_time and expiration."""
        self.applied_time = datetime.now()
        if duration is not None:
            self.duration = duration
        self.expires_at = self.applied_time + timedelta(seconds=self.duration)
        self.aura_val += 1

    def is_expired(self) -> bool:
        """Check if the aura is expired."""
        return datetime.now() >= self.expires_at
    
    def get_val(self) -> int:
        return self.aura_val
    
    def formatted_times(self) -> dict:
        """Optional helper to get formatted time strings for display."""
        return {
            "applied_time": self.applied_time.strftime('%Y-%m-%d %H:%M:%S'),
            "expires_at": self.expires_at.strftime('%Y-%m-%d %H:%M:%S')
        }