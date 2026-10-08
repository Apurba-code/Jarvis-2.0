import webbrowser
import wikipedia

def Search(query):
    """Handles real-time search and general knowledge."""
    query = query.lower().replace("jarvis", "").strip()
    
    if "wikipedia" in query:
        query = query.replace("wikipedia", "").strip()
        try:
            results = wikipedia.summary(query, sentences=2)
            return f"According to Wikipedia: {results}"
        except Exception:
            return "I couldn't find a Wikipedia page for that."
            
    # Default to web opening
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Fetching latest information for {query}."
