from agent.state import update_form_state, get_form_state
from agent.llm import call_llm
import json
from db.database import SessionLocal
from db.models import Interaction


# 🔧 helper to clean LLM JSON output
def parse_llm_json(response: str):
    try:
        clean = response.strip()

        # remove ```json ... ```
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]

        return json.loads(clean)
    except:
        return None



from datetime import datetime, timedelta
import re

def log_interaction(user_input: str):
    current_state = get_form_state()

    response = call_llm(
        f"""
Extract structured CRM data as JSON only.

Text:
{user_input}
"""
    )

    extracted_data = parse_llm_json(response) or {}
    text = user_input.lower()

    # =========================
    # 🔥 RULE-BASED CORE FIELDS (LOCKED)
    # =========================

    # 👨‍⚕️ Doctor
    match = re.search(r"dr\.?\s+\w+", user_input, re.IGNORECASE)
    if match:
        extracted_data["hcp_name"] = match.group()

    # 📅 Date
    if "today" in text:
        extracted_data["date"] = datetime.today().strftime("%Y-%m-%d")
    elif "yesterday" in text:
        extracted_data["date"] = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    # ⏰ Time
    time_match = re.search(r"\b(\d{1,2})(?::\d{2})?\s?(am|pm)\b", text, re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(1))
        period = time_match.group(2).lower()

        if period == "pm" and hour != 12:
            hour += 12
        if period == "am" and hour == 12:
            hour = 0

        extracted_data["time"] = f"{hour:02d}:00"

    # 📄 Materials
    if "brochure" in text:
        extracted_data["materials_shared"] = "brochures"

    # 💊 Samples
    if "sample" in text:
        extracted_data["samples_distributed"] = "samples"

    # 😊 Sentiment
    if "positive" in text:
        extracted_data["sentiment"] = "positive"
    elif "negative" in text:
        extracted_data["sentiment"] = "negative"
    elif "neutral" in text:
        extracted_data["sentiment"] = "neutral"

    # =========================
    # 🟡 OPTIONAL FIELDS (BEST-EFFORT ONLY)
    # =========================

    # 👥 Attendees
    if "with" in text:
        extracted_data["attendees"] = user_input

    # 🧠 Topics (append, not replace)
    # 🧠 Topics (SAFE + NO CRASH + NO DUPLICATE)
    if "discuss" in text:
       prev = current_state.get("discussion_topics", "")
       match = re.search(r"discuss(?:ed)? (.+)", text)
       new_topic = match.group(1).strip() if match else user_input.strip()
       if prev:
          if new_topic.lower() not in prev.lower():
            extracted_data["discussion_topics"] = prev + " | " + new_topic
          else:
            extracted_data["discussion_topics"] = prev
       else:
         extracted_data["discussion_topics"] = new_topic
    # 🎯 Outcomes
    if "outcome" in text or "result" in text:
        extracted_data["outcomes"] = user_input

    # 🔁 Follow-up
    if "follow" in text or "will" in text:
        prev = current_state.get("follow_up_actions", "")
        extracted_data["follow_up_actions"] = (prev + " | " + user_input).strip(" |")

    # =========================
    # 🚫 CLEAN FILTER
    # =========================
    allowed_fields = {
        "hcp_name", "interaction_type", "date", "time",
        "attendees", "discussion_topics", "materials_shared",
        "samples_distributed", "sentiment", "outcomes", "follow_up_actions"
    }

    cleaned_data = {
        k: v for k, v in extracted_data.items()
        if k in allowed_fields and v not in ["", None, "unknown"]
    }

    if not cleaned_data:
        return {
            "message": "❌ Could not extract meaningful data",
            "form_state": current_state
        }

    updated_state = update_form_state(cleaned_data)

    print("DEBUG extracted_data:", extracted_data)
    print("DEBUG cleaned_data:", cleaned_data)
    print("DEBUG current_state BEFORE:", current_state)

    return {
        "message": f"✅ Interaction logged for {updated_state.get('hcp_name', 'HCP')}",
        "form_state": updated_state
    }
# 2. EDIT INTERACTION (AI updates only fields)
def edit_interaction(user_input: str):
    current_state = get_form_state()

    response = call_llm(
        f"""
You are updating a CRM form.

Current form:
{current_state}

User correction:
{user_input}

Return ONLY JSON with changed fields.

Rules:
- ONLY include fields that change
- NEVER return empty fields
"""
    )

    updates = parse_llm_json(response)

    if not updates:
        return {
            "message": "❌ I couldn’t understand what to update. Try rephrasing.",
            "form_state": current_state
        }

    #  merge safely
    safe_updates = {}
    for k, v in updates.items():
        if v not in ["", None, "unknown"]:
            safe_updates[k] = v

    updated_state = update_form_state(safe_updates)

    if not updates:
       text = user_input.lower()

       if "sentiment" in text:
          if "positive" in text:
            updates = {"sentiment": "positive"}
          elif "negative" in text:
            updates = {"sentiment": "negative"}
          elif "neutral" in text:
            updates = {"sentiment": "neutral"}

    return {
        "message": " Updated the interaction details",
        "form_state": updated_state
    }

# 3. GET CURRENT FORM STATE
def get_form():
    return {
        "message": "Here is the current form ",
        "form_state": get_form_state()
    }

# 4. VALIDATE FORM
def validate_form():
    state = get_form_state()

    required_fields = ["hcp_name", "date", "time"]
    optional_fields = [
        "interaction_type",
        "attendees",
        "discussion_topics",
        "materials_shared",
        "samples_distributed",
        "sentiment",
        "outcomes",
        "follow_up_actions"
    ]

    missing_required = [f for f in required_fields if not state.get(f)]
    missing_optional = [f for f in optional_fields if not state.get(f)]

    # 🔥 STRONG MESSAGE LOGIC
    if missing_required:
        message = "❗ Please fill required fields before saving : "
    else:
        message = "✅ All required fields are filled"

    return {
        "message": message,
        "is_valid": len(missing_required) == 0,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "form_state": state
    }
# 5. SUBMIT INTERACTION (later we connect DB)
def submit_interaction():
    db = SessionLocal()
    state = get_form_state()

    try:
        new = Interaction(
            hcp_name=state["hcp_name"],
            interaction_type=state["interaction_type"],
            date=state["date"],
            time=state["time"],
            attendees=state["attendees"],
            discussion_topics=state["discussion_topics"],
            materials_shared=state["materials_shared"],
            samples_distributed=state["samples_distributed"],
            sentiment=state["sentiment"],
            outcomes=state["outcomes"],
            follow_up_actions=state["follow_up_actions"]
        )

        db.add(new)
        db.commit()
        db.refresh(new)

        return {
            "message": "Saved to database",
            "id": new.id
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()



def delete_field(user_input: str):
    current_state = get_form_state()
    text = user_input.lower()

    field_map = {
        "sentiment": "sentiment",
        "sample": "samples_distributed",
        "samples": "samples_distributed",
        "material": "materials_shared",
        "brochure": "materials_shared",
        "attendee": "attendees",
        "doctor": "hcp_name",
        "name": "hcp_name",
        "topic": "discussion_topics",
        "discussion": "discussion_topics",
        "outcome": "outcomes",
        "follow": "follow_up_actions",
    }

    fields_to_clear = set()

    for keyword, field in field_map.items():
        if keyword in text:
            fields_to_clear.add(field)

    if not fields_to_clear:
        return {
            "message": "❌ Could not understand what to remove",
            "form_state": current_state
        }

    updates = {field: "" for field in fields_to_clear}
    updated_state = update_form_state(updates)

    return {
        "message": f"Cleared: {', '.join(fields_to_clear)}",
        "form_state": updated_state
    }