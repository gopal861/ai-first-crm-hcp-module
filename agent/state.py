# agent/state.py

FORM_STATE = {
    "hcp_name": "",
    "interaction_type": "",
    "date": "",
    "time": "",
    "attendees": "",
    "discussion_topics": "",
    "materials_shared": "",
    "samples_distributed": "",
    "sentiment": "",
    "outcomes": "",
    "follow_up_actions": ""
}


def get_form_state():
    return FORM_STATE

def update_form_state(new_data: dict):
    for key, value in new_data.items():

        if key not in FORM_STATE:
            continue

        # 🗑️ delete case
        if value == "":
            FORM_STATE[key] = ""
            continue

        # 🚫 ignore weak values
        if value in [None, "", "unknown"]:
            continue

        current_value = FORM_STATE.get(key)

        # 🔁 append fields
        if key in ["discussion_topics", "follow_up_actions"]:
            if current_value:
                if value not in current_value:
                    FORM_STATE[key] = current_value + " | " + value
            else:
                FORM_STATE[key] = value

        # 🔒 protect important fields
        elif key in ["hcp_name", "date", "time"]:
            if not current_value:
                FORM_STATE[key] = value

        # 🟢 normal fields
        else:
            FORM_STATE[key] = value

    return FORM_STATE


def reset_form_state():
    for key in FORM_STATE:
        FORM_STATE[key] = ""
    return FORM_STATE