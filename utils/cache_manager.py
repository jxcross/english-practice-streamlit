"""
Cache Manager with LRU eviction and TTL support
Stores audio files with metadata for efficient retrieval
"""
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import shutil


class CacheManager:
    """Disk-based cache with LRU eviction and TTL"""

    def __init__(self, cache_dir='data/cache', max_size_mb=100, ttl_days=30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self.ttl_days = ttl_days

        # Index file for metadata
        self.index_file = self.cache_dir / 'index.pkl'
        self.index = self._load_index()

        # Clean expired entries on init
        self._clean_expired()

    def _load_index(self):
        """Load cache index from disk"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self):
        """Save cache index to disk"""
        with open(self.index_file, 'wb') as f:
            pickle.dump(self.index, f)

    def get(self, key):
        """Get item from cache"""
        if key not in self.index:
            return None

        metadata = self.index[key]

        # Check expiry
        if datetime.now() - metadata['created_at'] > timedelta(days=self.ttl_days):
            self.delete(key)
            return None

        # Load from disk
        cache_file = self.cache_dir / f"{key}.pkl"
        if not cache_file.exists():
            del self.index[key]
            self._save_index()
            return None

        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)

            # Update last accessed
            metadata['last_accessed'] = datetime.now()
            self._save_index()

            return data
        except Exception:
            self.delete(key)
            return None

    def set(self, key, value):
        """Set item in cache with LRU eviction"""
        # Enforce size limit before adding
        self._enforce_size_limit(value)

        # Save to disk
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)

            # Update index
            self.index[key] = {
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'size': cache_file.stat().st_size
            }
            self._save_index()
        except Exception as e:
            print(f"Cache write error: {e}")
            if cache_file.exists():
                cache_file.unlink()

    def delete(self, key):
        """Delete item from cache"""
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            cache_file.unlink()

        if key in self.index:
            del self.index[key]
            self._save_index()

    def _enforce_size_limit(self, new_value):
        """Enforce cache size limit using LRU eviction"""
        # Calculate current size
        total_size = sum(meta['size'] for meta in self.index.values())

        # Estimate new item size (rough approximation)
        try:
            new_size = len(pickle.dumps(new_value))
        except Exception:
            new_size = 0

        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size + new_size > max_size_bytes:
            # Sort by last accessed (oldest first)
            sorted_keys = sorted(
                self.index.keys(),
                key=lambda k: self.index[k]['last_accessed']
            )

            # Delete oldest items until under limit
            for key in sorted_keys:
                if total_size + new_size <= max_size_bytes:
                    break

                total_size -= self.index[key]['size']
                self.delete(key)

    def _clean_expired(self):
        """Remove expired entries"""
        expired_keys = []
        for key, metadata in self.index.items():
            if datetime.now() - metadata['created_at'] > timedelta(days=self.ttl_days):
                expired_keys.append(key)

        for key in expired_keys:
            self.delete(key)

    def get_stats(self):
        """Get cache statistics"""
        total_size = sum(meta['size'] for meta in self.index.values())

        return {
            'items': len(self.index),
            'size_mb': total_size / (1024 * 1024),
            'max_size_mb': self.max_size_mb,
            'usage_percent': (total_size / (self.max_size_mb * 1024 * 1024)) * 100 if self.max_size_mb > 0 else 0
        }

    def clear(self):
        """Clear all cache"""
        for key in list(self.index.keys()):
            self.delete(key)
