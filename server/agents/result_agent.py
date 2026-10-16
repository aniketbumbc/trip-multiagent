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

    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set")
        response = openai_llm.invoke([
            SystemMessage(content="You are a helpful assistant that displays the results to the user."),
            HumanMessage(content=final_prompt)
        ])
        answer = response.content
    except Exception as exc:
        answer = (
            "Final summary could not be generated.\n\n"
            f"Reason: {exc}\n\n"
            f"Flight results:\n{state.get('flight_results', '')}\n\n"
            f"Hotel results:\n{state.get('hotel_results', '')}\n\n"
            f"Itinerary:\n{state.get('itinerary', '')}"
        )
    return {
        'final_response':answer,
        'messages':[
            AIMessage(content=answer)
        ],
        'llm_calls':state.get('llm_calls',0) + 1
    }