"""
JARVIS Chatbot with LiveKit LLM Integration
Supports both LiveKit (preferred) and REST API (fallback)
"""

import json
import os
import asyncio
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Check LiveKit availability
try:
    from livekit.agents import llm
    from livekit.plugins import openai, google
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False

# Check Cohere availability
try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "Data", "ChatLog.json")

def GetHistory():
    """Load conversation history from JSON file."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def SaveHistory(user_input, bot_response):
    """Save conversation to history."""
    history = GetHistory()
    history.append({"user": user_input, "jarvis": bot_response})
    if len(history) > 20:
        history = history[-20:]
    with open(LOG_FILE, 'w') as f:
        json.dump(history, f, indent=4)

# ============================================================================
# LiveKit LLM Implementation (Preferred)
# ============================================================================

async def ChatLiveKit(query: str) -> str:
    """Chat using LiveKit LLM inference."""
    history = GetHistory()
    context = llm.ChatContext()
    
    # System message
    context.append(
        text="You are JARVIS, a highly intelligent and helpful AI assistant. Responses must be concise, professional, and natural.",
        role=llm.ChatRole.SYSTEM
    )
    
    # Add history
    for entry in history[-10:]:
        context.append(text=entry["user"], role=llm.ChatRole.USER)
        context.append(text=entry["jarvis"], role=llm.ChatRole.ASSISTANT)
    
    # Add current query
    context.append(text=query, role=llm.ChatRole.USER)
    
    # Select LLM provider
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_key_here":
        model = openai.LLM(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    elif GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
        model = google.LLM(model="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY)
    else:
        return "No LLM API key configured. Add OPENAI_API_KEY or GOOGLE_API_KEY to .env"
    
    # Stream response
    response_text = ""
    stream = model.chat(chat_ctx=context)
    
    async for chunk in stream:
        if isinstance(chunk, llm.ChatChunk):
            response_text += chunk.choices[0].delta.content
    
    SaveHistory(query, response_text.strip())
    return response_text.strip()

# ============================================================================
# REST API Fallback (Gemini)
# ============================================================================

def ChatREST(query: str) -> str:
    """Fallback chat using Google Gemini REST API."""
    if not GOOGLE_API_KEY:
        return "I need a Google API Key. Please add it to your .env file."
    
    history = GetHistory()
    context = "You are JARVIS, a highly intelligent and helpful AI assistant. Responses must be concise and professional.\\n"
    for entry in history:
        context += f"User: {entry['user']}\\nJarvis: {entry['jarvis']}\\n"
    
    prompt = f"{context}User: {query}\\nJarvis:"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            bot_response = data['candidates'][0]['content']['parts'][0]['text'].strip()
            SaveHistory(query, bot_response)
            return bot_response
        else:
            return f"Brain Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"Neural Link Failure: {e}"

# ============================================================================
# Cohere API (Free Tier Alternative)
# ============================================================================

def ChatCohere(query: str) -> str:
    """Chat using Cohere's free tier API."""
    if not COHERE_AVAILABLE:
        return "Cohere not installed. Run: pip install cohere"
    
    if not COHERE_API_KEY or COHERE_API_KEY == "your_cohere_key_here":
        return "Cohere API key not configured. Add COHERE_API_KEY to .env"
    
    try:
        co = cohere.Client(COHERE_API_KEY)
        
        # Build conversation history
        history = GetHistory()
        chat_history = []
        for entry in history[-10:]:  # Last 10 exchanges
            chat_history.append({"role": "USER", "message": entry["user"]})
            chat_history.append({"role": "CHATBOT", "message": entry["jarvis"]})
        
        # Send message
        response = co.chat(
            message=query,
            chat_history=chat_history,
            model="command-r7b-12-2024",  # Free tier model
            preamble="You are JARVIS, a highly intelligent and helpful AI assistant. Responses must be concise, professional, and natural.",
            temperature=0.7,
            max_tokens=2048
        )
        
        bot_response = response.text.strip()
        SaveHistory(query, bot_response)
        return bot_response
        
    except Exception as e:
        return f"Cohere Error: {str(e)}"

# ============================================================================
# Main Chat Function (Auto-selects LiveKit or REST)
# ============================================================================

def Chat(query: str) -> str:
    """
    Main chat function with automatic provider selection.
    Priority: LiveKit > Cohere > Gemini REST
    """
    try:
        # Priority 1: LiveKit (if installed and 64-bit Python)
        if LIVEKIT_AVAILABLE:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(ChatLiveKit(query))
            loop.close()
            return result
        
        # Priority 2: Cohere (free tier, works on 32-bit)
        elif COHERE_AVAILABLE and COHERE_API_KEY and COHERE_API_KEY != "your_cohere_key_here":
            return ChatCohere(query)
        
        # Priority 3: Gemini REST (fallback)
        else:
            return ChatREST(query)
            
    except Exception as e:
        # Ultimate fallback chain
        if LIVEKIT_AVAILABLE:
            print(f"LiveKit failed, trying Cohere: {e}")
            if COHERE_AVAILABLE:
                return ChatCohere(query)
            return ChatREST(query)
        elif COHERE_AVAILABLE:
            print(f"Cohere failed, trying Gemini: {e}")
            return ChatREST(query)
        return f"All chat providers failed: {e}"

if __name__ == "__main__":
    print(Chat("How do you make bangladeshi chicken curry?"))
