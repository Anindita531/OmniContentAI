import os
from typing import TypedDict, Optional, Dict, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from schema import ComplianceReport, DistributionOutput
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Initialize Models
# Using Llama 3.3-70b for all nodes to ensure strict adherence to Pydantic schemas
# and high-quality translations.
llm_logic = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

writer_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
compliance_llm = llm_logic.with_structured_output(ComplianceReport)
distributor_llm = llm_logic.with_structured_output(DistributionOutput)

# --- 3. STATE DEFINITION ---
class AgentState(TypedDict):
    task: str
    content: str
    feedback: str
    iterations: int
    is_compliant: bool
    final_assets: Optional[Dict]

# --- 4. AGENT NODES ---

def writer_node(state: AgentState):
    print(f"\n--- WRITER: Round {state.get('iterations', 0) + 1} ---")
    feedback = state.get("feedback", "")
    feedback_text = f"Previous Feedback to fix: {feedback}" if feedback else "This is the initial draft."
    
    prompt = f"""
    Task: {state['task']}
    Context: {feedback_text}
    
    Instruction: Write a professional corporate announcement. 
    Strict Rule: Do not use any emojis. Keep the tone formal and 'Security First'.
    """
    res = writer_llm.invoke(prompt)
    
    return {
        "content": res.content, 
        "iterations": state.get("iterations", 0) + 1
    }

def compliance_node(state: AgentState):
    print("--- COMPLIANCE: Reviewing Content ---")
    rules = "1. Absolutely no emojis. 2. Must mention 'Security First'. 3. Tone must be professional."
    
    # The LLM will fill the ComplianceReport schema
    report = compliance_llm.invoke(f"Rules: {rules}\nContent: {state.get('content', '')}")
    
    print(f"Status: {'PASSED' if report.is_compliant else 'FAILED'}")
    return {
        "is_compliant": report.is_compliant, 
        "feedback": report.feedback if not report.is_compliant else ""
    }

def distribution_node(state: AgentState):
    print("--- DISTRIBUTOR: Generating Multi-Lingual Assets ---")
    content = state.get("content", "")
    
    # You can add or remove languages from this list
    target_langs = ["Bengali", "Spanish", "German"]
    
    prompt = f"""
    Adapt the following content for:
    1. LinkedIn (Professional post)
    2. Twitter (Short, concise)
    3. Newsletter (Detailed summary)
    4. Translations: Provide a 3-sentence professional summary for these languages: {', '.join(target_langs)}.
    
    Content to adapt:
    {content}
    """
    
    assets = distributor_llm.invoke(prompt)
    # Using model_dump() for Pydantic V2 compatibility
    return {"final_assets": assets.model_dump()}

# --- 5. ROUTING LOGIC ---

def routing_logic(state: AgentState):
    if state.get("is_compliant"):
        return "distribute"
    if state.get("iterations", 0) >= 3:
        print("!!! Max iterations reached. Moving to distribution. !!!")
        return "distribute"
    return "writer"

# --- 6. GRAPH CONSTRUCTION ---

memory = MemorySaver()
workflow = StateGraph(AgentState)

workflow.add_node("writer", writer_node)
workflow.add_node("compliance", compliance_node)
workflow.add_node("distribute", distribution_node)

workflow.set_entry_point("writer")
workflow.add_edge("writer", "compliance")
workflow.add_conditional_edges(
    "compliance", 
    routing_logic, 
    {"writer": "writer", "distribute": "distribute"}
)
workflow.add_edge("distribute", END)

# We interrupt BEFORE distribution to allow for Human-in-the-loop approval
app = workflow.compile(checkpointer=memory, interrupt_before=["distribute"])

# --- 7. CLI EXECUTION ---
if __name__ == "__main__":
    # thread_id allows the graph to 'remember' the state between steps
    thread_config = {"configurable": {"thread_id": "enterprise_run_01"}}
    
    initial_input = {
        "task": "Launch of our new Zero-Trust Cloud Security Dashboard.", 
        "iterations": 0, 
        "is_compliant": False,
        "feedback": "",
        "content": ""
    }

    print("Pipeline Started...")
    
    # First Phase: Generate and Validate
    for event in app.stream(initial_input, thread_config, stream_mode="values"):
        if event.get("content"):
            print(f"\n[CURRENT DRAFT]:\n{event['content']}")

    # Human-in-the-loop trigger
    print("\n" + "="*30)
    print("Awaiting Human Approval...")
    user_choice = input("Proceed to Global Distribution? (y/n): ").lower()

    if user_choice == "y":
        # Second Phase: Distribute (Resume from checkpoint)
        for event in app.stream(None, thread_config, stream_mode="values"):
            if event.get("final_assets"):
                assets = event["final_assets"]
                print("\n" + "="*30)
                print("FINAL MULTI-CHANNEL ASSETS")
                print(f"LINKEDIN:\n{assets['linkedin']}\n")
                print(f"TWITTER:\n{assets['twitter']}\n")
                
                print("LOCALIZATIONS:")
                for lang, text in assets['localizations'].items():
                    print(f"[{lang.upper()}]: {text}\n")
    else:
        print("Distribution cancelled by user.")