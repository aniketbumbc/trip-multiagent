from typing import TypedDict,Annotated
from tools.tavily_tool import search_tavily
from base import TravelState
from langchain_core.messages import AIMessage




def hotel_agent(state:TravelState) -> TravelState:
    """
    Hotel agent is responsible for finding the best hotel for the user.
    """
    query = state.get("user_query","")
    if not query:
        return {"messages":[
            AIMessage(content="No hotel query provided")
        ],
        "llm_calls":state.get("llm_calls",0) + 1
        }
    hotel_dict = search_tavily(query)
    return {"hotel_results":hotel_dict,
    "messages":[
        AIMessage(content="Hotel results are fetched successfully")
    ],
    "llm_calls":state.get("llm_calls",0) + 1
    }