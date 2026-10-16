from langgraph.graph import StateGraph,START,END
from agents.flight_agent import flight_agent
from agents.tavily_agent import hotel_agent
from agents.itinerary_agent import itinerary_agent
from agents.result_agent import result_agent
from base import TravelState


graph = StateGraph(TravelState)

graph.add_node("flight_agent",flight_agent)
graph.add_node("hotel_agent",hotel_agent)
graph.add_node("itinerary_agent",itinerary_agent)
graph.add_node("result_agent",result_agent)

graph.add_edge(START,"flight_agent")
graph.add_edge("flight_agent","hotel_agent")
graph.add_edge("hotel_agent","itinerary_agent")
graph.add_edge("itinerary_agent","result_agent")
graph.add_edge("result_agent",END)

# compiled_graph = graph.compile()




