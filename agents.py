import os

def writer_agent(state):
    """Drafts content based on task and feedback loop."""
    print(f"--- WRITER: Round {state.get('iterations', 0) + 1} ---")
    
    task = state.get('task', '').strip()
    tone = state.get('tone', 'Professional')
    feedback = state.get('feedback', '')
    
    # In a real enterprise app, you'd call an LLM here.
    # We incorporate feedback to show 'Multi-agent coordination'.
    if feedback:
        content = f"REVISED {tone} CONTENT: {task}. (Fixed: {feedback})"
    else:
        content = f"INITIAL {tone} DRAFT: {task}."
        
    return {
        "content": content, 
        "iterations": state.get("iterations", 0) + 1
    }

def compliance_agent(state):
    """Governance Agent checking against brand_rules.txt and safety policies."""
    print("--- COMPLIANCE: Reviewing for Brand Governance ---")
    text = state.get("content", "")
    
    # 1. Load Knowledge from brand_rules.txt
    rules_path = "brand_rules.txt"
    brand_rules = ""
    if os.path.exists(rules_path):
        with open(rules_path, "r") as f:
            brand_rules = f.read().lower()

    violations = []
    
    # Rule A: Check for Emojis (Enterprise Standard)
    if any(emoji in text for emoji in ["🚀", "✨", "😂", "😃"]):
        violations.append("Remove emojis (Not permitted in Corporate Tone)")

    # Rule B: Specific Security Policy check (Knowledge-to-Content)
    # If the task is about IPL, 'security' must be mentioned.
    if "ipl" in state.get('task', '').lower() and "security" not in text.lower():
        violations.append("Missing mandatory 'Security First' mention")

    # Rule C: Check against external brand_rules.txt
    if brand_rules and "no-shouting" in brand_rules and "!" in text:
        violations.append("Rule Violation: No exclamation marks allowed")

    is_compliant = len(violations) == 0
    feedback = "FIX REQUIRED: " + "; ".join(violations) if not is_compliant else ""

    return {
        "is_compliant": is_compliant,
        "feedback": feedback
    }