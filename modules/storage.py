"""
Storage Manager for playlist persistence using SQLite
"""
import sqlite3
import json
from pathlib import Path
import csv
from io import StringIO


class StorageManager:
    """SQLite-based storage for playlists"""

    def __init__(self, db_path='data/playlists.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with playlists table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                tracks TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_playlist(self, name, tracks):
        """
        Save playlist to database

        Args:
            name: Playlist name
            tracks: List of track dictionaries [{'english': '...', 'korean': '...'}, ...]

        Returns:
            bool: True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            tracks_json = json.dumps(tracks, ensure_ascii=False)

            cursor.execute('''
                INSERT OR REPLACE INTO playlists (name, tracks, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (name, tracks_json))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error saving playlist: {e}")
            return False

    def load_playlist(self, name):
        """
        Load playlist from database

        Args:
            name: Playlist name

        Returns:
            list: List of track dictionaries, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT tracks FROM playlists WHERE name = ?', (name,))
            result = cursor.fetchone()

            conn.close()

            if result:
                return json.loads(result[0])
            return None

        except Exception as e:
            print(f"Error loading playlist: {e}")
            return None

    def list_playlists(self):
        """
        List all saved playlists

        Returns:
            list: List of playlist info dictionaries [{'name': '...', 'created_at': '...', 'track_count': N}, ...]
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT name, created_at, tracks FROM playlists ORDER BY updated_at DESC')
            playlists = cursor.fetchall()

            conn.close()

            result = []
            for name, created_at, tracks_json in playlists:
                tracks = json.loads(tracks_json)
                result.append({
                    'name': name,
                    'created_at': created_at,
                    'track_count': len(tracks)
                })

            return result

        except Exception as e:
            print(f"Error listing playlists: {e}")
            return []

    def delete_playlist(self, name):
        """
        Delete playlist from database

        Args:
            name: Playlist name

        Returns:
            bool: True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM playlists WHERE name = ?', (name,))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error deleting playlist: {e}")
            return False

    def export_playlist_csv(self, tracks):
        """
        Export playlist as CSV string

        Args:
            tracks: List of track dictionaries

        Returns:
            str: CSV content
        """
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['english', 'korean'])

        for track in tracks:
            writer.writerow([track.get('english', ''), track.get('korean', '')])

        return output.getvalue()

    def get_playlist_count(self):
        """Get total number of saved playlists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM playlists')
            count = cursor.fetchone()[0]

            conn.close()
            return count

        except Exception as e:
            print(f"Error getting playlist count: {e}")
            return 0
