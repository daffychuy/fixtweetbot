"""Lock Model"""

from masoniteorm.models import Model
import datetime as dt
import logging

_log = logging.getLogger(__name__)


class Lock(Model):
    """Lock Model"""

    __table__ = "locks"

    @classmethod
    def acquire(cls, key: str, owner: str, ttl_seconds: int = 30) -> bool:
        """Try to acquire a lock for `key` with `owner` id and TTL.

        Returns True if the lock was acquired, False otherwise.
        """
        # Use timezone-aware UTC datetimes
        now = dt.datetime.now(dt.timezone.utc)
        expires_at = now + dt.timedelta(seconds=ttl_seconds)

        # Try to create the lock first (fast path)
        try:
            cls.create({'lock_key': key, 'owner': owner, 'expires_at': expires_at})
            _log.debug(f"Lock acquired (created) for key={key} owner={owner} ttl={ttl_seconds}")
            return True
        except Exception as e:
            _log.warning(f"Failed to create lock for key={key}: {e}")

        # If creation failed, check existing lock
        try:
            existing = cls.where('lock_key', key).first()
        except Exception as e:
            _log.exception(f"Error querying existing lock for key={key}: {e}")
            return False

        if existing:
            # If expired, remove it then try to create again
            try:
                existing_expires = existing.expires_at
            except Exception:
                existing_expires = None

            if existing_expires:
                # normalize to timezone-aware if naive
                if existing_expires.tzinfo is None:
                    existing_expires = existing_expires.replace(tzinfo=dt.timezone.utc)

            if existing_expires and existing_expires <= now:
                _log.debug(f"Found expired lock for key={key}, attempting to remove and retry")
                try:
                    existing.delete()
                except Exception as e:
                    _log.exception(f"Failed to delete expired lock for key={key}: {e}")
                    return False

                # Retry creating
                try:
                    cls.create({'lock_key': key, 'owner': owner, 'expires_at': expires_at})
                    _log.debug(f"Lock acquired (recreated) for key={key} owner={owner}")
                    return True
                except Exception as e:
                    _log.debug(f"Failed to recreate lock for key={key} after deleting expired: {e}")
                    return False

        # Lock is held by someone else and not expired
        _log.debug(f"Lock for key={key} is currently held by another owner")
        return False

    @classmethod
    def release(cls, key: str, owner: str) -> bool:
        """Release the lock if owned by `owner`. Returns True if released."""
        existing = cls.where('lock_key', key).first()
        if not existing:
            return True
        if existing.owner != owner:
            return False
        try:
            existing.delete()
            return True
        except Exception:
            return False
