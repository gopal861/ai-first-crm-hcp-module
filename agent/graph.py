from langgraph.graph import StateGraph, END
from typing import TypedDict
from agent.tools import submit_interaction

from agent.tools import (
    log_interaction,
    edit_interaction,
    get_form,
    validate_form,
    delete_field,
    parse_llm_json
)

from agent.llm import call_llm


# ==============================
# STATE
# ==============================
class AgentState(TypedDict):
    input: str
    output: dict


# ==============================
# 🧠 ROUTER (FINAL STABLE VERSION)
# ==============================
def route_with_llm(user_input: str):
    
    text = user_input.lower()
    if "save" in text or "submit" in text:
      return "save"

    # ==============================
    # 🔴 DELETE (HIGH PRIORITY)
    # ==============================
    if any(word in text for word in ["remove", "delete", "clear"]):
        return "delete"

    # ==============================
    # 🟡 EDIT (STRONG DETECTION)
    # ==============================
    if any(word in text for word in ["actually", "correction", "update", "change"]):
        if any(field in text for field in ["sentiment", "name", "date", "time"]):
            return "edit"

    # ==============================
    # 🟢 ADD / LOG (SAFE CONDITION)
    # ==============================
    if "also" in text or "add" in text:
        return "log"

    # ==============================
    # 🔵 GET FORM
    # ==============================
    if "show" in text or "display" in text:
        return "get"

    # ==============================
    # 🟣 VALIDATE (STRICT ONLY)
    # ==============================
    if "validate" in text or "check form" in text:
        return "validate"

    # ==============================
    # 🤖 LLM (CONTROLLED USE)
    # ==============================
    try:
        response = call_llm(
            f"""
Classify the user's intent for a CRM assistant.

Return ONLY JSON:
{{"intent": "log" | "edit" | "delete" | "get" | "validate"}}

Text:
{user_input}
"""
        )

        data = parse_llm_json(response)

        if data and "intent" in data:
            intent = data["intent"]

            # 🔒 BLOCK BAD LLM DECISIONS
            if intent == "get" and not any(w in text for w in ["show", "display"]):
                pass  # ignore wrong LLM output
            elif intent in ["log", "edit", "delete", "get", "validate"]:
             return intent
    except Exception:
        pass

    # ==============================
    # 🔥 FINAL DEFAULT
    # ==============================
    return "log"


# ==============================
# 🤖 MAIN NODE
# ==============================
def agent_node(state: AgentState):
    user_input = state["input"]

    intent = route_with_llm(user_input)

    if intent == "delete":
      result = delete_field(user_input)

    elif intent == "edit":
     result = edit_interaction(user_input)

    elif intent == "get":
      result = get_form()

    elif intent == "validate":
      result = validate_form()

    elif intent == "save":   
      result = submit_interaction()

    else:
      result = log_interaction(user_input)

    return {"output": result}


# ==============================
# GRAPH BUILD
# ==============================
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)

builder.set_entry_point("agent")
builder.add_edge("agent", END)

graph = builder.compile()