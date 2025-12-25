"""
Cache Inspector UI for debugging and validation
Provides tools to view, inspect, and manage cached TTS audio
"""
import streamlit as st
from datetime import datetime


def render_cache_inspector(tts_engine):
    """Render cache inspection and management UI"""
    st.markdown("### 🔍 Cache Inspector")

    # Get cache index
    cache_index = tts_engine.cache.index

    if not cache_index:
        st.info("Cache is empty")
        return

    st.markdown(f"**Total cached items**: {len(cache_index)}")

    # Sort by last accessed (most recent first)
    sorted_items = sorted(
        cache_index.items(),
        key=lambda x: x[1]['last_accessed'],
        reverse=True
    )

    # Display cached items (top 20)
    st.markdown("**Recently accessed cache entries** (showing top 20):")

    for cache_key, metadata in sorted_items[:20]:
        # Load cache data to get text preview (don't track in stats)
        cached_data = tts_engine.cache.get(cache_key, track_stats=False)

        if cached_data:
            text_preview = cached_data.get('text_preview', 'N/A')
            voice = cached_data.get('voice', 'N/A')
            size_kb = metadata['size'] / 1024
            created = metadata['created_at'].strftime('%Y-%m-%d %H:%M')
            accessed = metadata['last_accessed'].strftime('%Y-%m-%d %H:%M')

            with st.expander(f"📝 {text_preview[:50]}..."):
                st.text(f"Text: {text_preview}")
                st.text(f"Voice: {voice}")
                st.text(f"Size: {size_kb:.1f} KB")
                st.text(f"Created: {created}")
                st.text(f"Last accessed: {accessed}")
                st.text(f"Cache key: {cache_key[:16]}...")

                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{cache_key}"):
                    tts_engine.cache.delete(cache_key)
                    st.success("Deleted from cache")
                    st.rerun()

    # Clear all cache button
    st.markdown("---")
    st.markdown("**Danger Zone**")

    if st.button("🗑️ Clear All Cache", type="secondary"):
        if st.session_state.get('confirm_clear_cache'):
            tts_engine.cache.clear()
            st.session_state['confirm_clear_cache'] = False
            st.success("All cache cleared")
            st.rerun()
        else:
            st.session_state['confirm_clear_cache'] = True
            st.warning("⚠️ Click again to confirm")
