from base import TravelState
import os
from langchain_core.messages import SystemMessage,HumanMessage,AIMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_llm = ChatOpenAI(api_key=OPENAI_API_KEY,model="gpt-5.6-luna") if OPENAI_API_KEY else None

def itinerary_agent(state:TravelState) -> TravelState:
    """
    Itinerary agent is responsible for creating an itinerary for the user.
    """
    
    prompt = f"""
    The user has provided the following flight and hotel results:
    {state.get("flight_results","")}
    {state.get("hotel_results","")}
    user query: {state.get("user_query","")}
    Create an itinerary for the user cost friendly and time efficient.
    """
    try:
        if openai_llm is None:
            raise ValueError("OPENAI_API_KEY is not set")
        response = openai_llm.invoke([
            SystemMessage(content="You are a helpful assistant that creates an itinerary for the user."),
            HumanMessage(content=prompt)
        ])
        itinerary = response.content
    except Exception as exc:
        itinerary = f"Itinerary generation failed: {exc}"

    return {
        'itinerary':itinerary,
        'messages':[
            AIMessage(content=itinerary)
        ],
        'llm_calls':state.get('llm_calls',0) + 1
    }