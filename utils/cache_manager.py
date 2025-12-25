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

        # Index file for metadata and stats
        self.index_file = self.cache_dir / 'index.pkl'
        self.index, self.stats = self._load_index()

        # Clean expired entries on init
        self._clean_expired()

    def _load_index(self):
        """Load cache index and stats from disk"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'rb') as f:
                    data = pickle.load(f)

                # Handle new format with stats
                if isinstance(data, dict) and 'index' in data and 'stats' in data:
                    return data['index'], data['stats']
                # Handle old format (backward compatibility)
                else:
                    return data, {
                        'total_requests': 0,
                        'cache_hits': 0,
                        'cache_misses': 0
                    }
            except Exception:
                return {}, {
                    'total_requests': 0,
                    'cache_hits': 0,
                    'cache_misses': 0
                }
        return {}, {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def _save_index(self):
        """Save cache index and stats to disk"""
        with open(self.index_file, 'wb') as f:
            pickle.dump({
                'index': self.index,
                'stats': self.stats
            }, f)

    def get(self, key, track_stats=True):
        """Get item from cache

        Args:
            key: Cache key
            track_stats: Whether to track this request in stats (default: True)
        """
        # Track total requests (only if tracking is enabled)
        if track_stats:
            self.stats['total_requests'] += 1

        if key not in self.index:
            if track_stats:
                self.stats['cache_misses'] += 1
            return None

        metadata = self.index[key]

        # Check expiry
        if datetime.now() - metadata['created_at'] > timedelta(days=self.ttl_days):
            self.delete(key)
            if track_stats:
                self.stats['cache_misses'] += 1
            return None

        # Load from disk
        cache_file = self.cache_dir / f"{key}.pkl"
        if not cache_file.exists():
            del self.index[key]
            self._save_index()
            if track_stats:
                self.stats['cache_misses'] += 1
            return None

        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)

            # Update last accessed
            metadata['last_accessed'] = datetime.now()
            self._save_index()

            # Track cache hit (only if tracking is enabled)
            if track_stats:
                self.stats['cache_hits'] += 1
            return data
        except Exception:
            self.delete(key)
            if track_stats:
                self.stats['cache_misses'] += 1
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
            'usage_percent': (total_size / (self.max_size_mb * 1024 * 1024)) * 100 if self.max_size_mb > 0 else 0,
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'total_requests': self.stats['total_requests']
        }

    def clear(self):
        """Clear all cache"""
        for key in list(self.index.keys()):
            self.delete(key)
