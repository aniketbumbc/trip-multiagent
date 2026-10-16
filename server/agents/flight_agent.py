from typing import TypedDict,Annotated
from tools.flight_tools import search_flights
from base import TravelState

def flight_agent(state:TravelState) -> TravelState:
    """
    Flight agent is responsible for finding the best flight for the user.
    """
    query = state.get("user_query","")
    if not query:
        return {"messages":[
            AIMessage(content="No flight query provided")
        ],
        "llm_calls":state.get("llm_calls",0) + 1
        }
    flights_data = search_flights(query)
    return {"flight_results":flights_dict,
    "messages":[
        AIMessage(content="Flight results are fetched successfully")
    ],
    "llm_calls":state.get("llm_calls",0) + 1
    }