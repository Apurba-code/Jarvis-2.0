from Backend.Automation import OpenApp, CloseApp, WebSearch, SystemControl, handle_chrome_command
from Backend.RealtimeSearchEngine import Search
from Backend.Chatbot import Chat
from Backend.ImageGeneration import GenerateImage

def Router(query):
    query = query.lower().strip()
    
    # Chrome commands
    if any(kw in query for kw in ["new tab", "close tab", "switch to", "go back", "go forward", "refresh tab", "list tabs"]):
        return handle_chrome_command(query)

    # App Open / Close
    elif "open" in query:
        app = query.replace("open", "").strip()
        return OpenApp(app)
    
    elif "close" in query:
        app = query.replace("close", "").strip()
        return CloseApp(app)
    
    elif "search" in query or "google" in query:
        search_query = query.replace("search", "").replace("google", "").strip()
        return Search(search_query)
        
    elif any(kw in query for kw in ["shutdown", "restart", "sleep", "volume", "mute", "brightness"]):
        return SystemControl(query)
    
    elif "wikipedia" in query:
        return Search(query)
        
    elif "generate" in query or "image" in query or "visualize" in query:
        return GenerateImage(query)
        
    # Default to chatbot
    return Chat(query)
