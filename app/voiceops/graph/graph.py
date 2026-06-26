from langgraph.graph import END, START, StateGraph

from app.voiceops.graph.nodes import build_report, load_input, match_known_fingerprints
from app.voiceops.graph.state import RCAState


def build_rca_graph():
    graph = StateGraph(RCAState)
    graph.add_node("load_input", load_input)
    graph.add_node("match_fingerprints", match_known_fingerprints)
    graph.add_node("build_rca_report", build_report)

    graph.add_edge(START, "load_input")
    graph.add_edge("load_input", "match_fingerprints")
    graph.add_edge("match_fingerprints", "build_rca_report")
    graph.add_edge("build_rca_report", END)

    return graph.compile()


RCA_GRAPH = build_rca_graph()


def run_rca_graph(state: RCAState) -> RCAState:
    result = RCA_GRAPH.invoke(state)
    return RCAState(**result)
