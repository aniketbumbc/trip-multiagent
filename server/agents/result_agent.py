from base import TravelState
from langchain_core.messages import SystemMessage,HumanMessage,AIMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

openai_llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"),model="gpt-4o-mini")


def result_agent(state:TravelState) -> TravelState:
    """
    Result agent is responsible for displaying the results to the user.
    """

    final_prompt = f"""
    Generate final response for the user based on the itinerary and the flight and hotel and other data provided.

    User Request: {state.get("user_query","")}
    Itinerary: {state.get("itinerary","")}
    Flight Results: {state.get("flight_results","")}
    Hotel Results: {state.get("hotel_results","")}
    Format the response in a friendly and engaging manner with section wise details.
    1. Trip Summary
    2. Flight Details
    3. Hotel Details
    4. Itinerary Day by Day Details
    5. Estimate budget Details
    6. Final reommendations point wise short and concise.

    Important:
    - Be clear and practical.
    - If flight data is not available, suggest alternative options.
    - Keep the response concise real travel experience.
    
    """

    response = openai_llm.invoke([
        SystemMessage(content="You are a helpful assistant that displays the results to the user."),
        HumanMessage(content=final_prompt)
    ])
    return {
        'final_response':response.content,
        'messages':[
            AIMessage(content=response.content)
        ],
        'llm_calls':state.get('llm_calls',0) + 1
    }