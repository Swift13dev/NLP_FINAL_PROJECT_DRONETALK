import streamlit as st
import spacy
import json
import re
import matplotlib.pyplot as plt

# --- 1. Load our NEW 1000-Command Model ---
@st.cache_resource
def load_model():
    try:
        # POINTING TO THE NEW MODEL FOLDER
        return spacy.load("./model_output_1000/model-best")
    except IOError:
        st.error("ERROR: Trained model not found in './model_output_1000/model-best'")
        return None

nlp = load_model()

# --- 2. Command Generator Logic ---
def clean_value(value_str):
    if not value_str:
        return None
    match = re.search(r"(\d+(\.\d+)?)", str(value_str))
    if match:
        return float(match.group(1))
    return None

def generate_command(parsed_json):
    # Fallback Logic
    intent = None
    slots = parsed_json["slots"]
    
    if parsed_json["intents"]:
        intent = parsed_json["intents"][0]
    else:
        if "distance" in slots and "direction" in slots:
            intent = "fly"
            st.info("No intent found, but slots detected. Assuming 'fly'.")

    if not intent:
        return {"command": "REJECT", "reason": "No intent recognized."}

    final_command = {}

    if intent == "fly":
        dist = clean_value(slots.get("distance"))
        direction = slots.get("direction")
        if not dist or not direction:
            return {"command": "REJECT", "reason": "Fly command needs distance AND direction."}
        final_command = {
            "command": "MOVE", 
            "direction": direction, 
            "distance_meters": dist
        }
    
    elif intent == "hover":
        dur = clean_value(slots.get("duration"))
        if not dur:
            return {"command": "REJECT", "reason": "Hover command needs duration."}
        final_command = {"command": "HOVER", "duration_seconds": dur}

    elif intent == "land":
        final_command = {"command": "LAND"}

    elif intent == "capture":
        count = clean_value(slots.get("count"))
        if not count:
            count = clean_value(slots.get("distance")) 
        if not count:
            count = 1
        final_command = {"command": "CAPTURE_IMAGE", "count": int(count)}
    
    elif intent == "scan":
         final_command = {"command": "SCAN_AREA"}

    elif intent == "return":
        final_command = {"command": "MOVE", "direction": "home", "distance_meters": 0}
        
    elif intent == "takeoff":
        final_command = {"command": "TAKEOFF"}

    else:
        final_command = {"command": intent.upper()}

    return final_command

# --- Section 1: Initialize Drone State ---
if 'x_pos' not in st.session_state:
    st.session_state.x_pos = 0
if 'y_pos' not in st.session_state:
    st.session_state.y_pos = 0

# --- Section 2: Function to Plot the Visual ---
def plot_drone_position():
    x = st.session_state.x_pos
    y = st.session_state.y_pos
    
    fig, ax = plt.subplots()
    ax.scatter([x], [y], marker='o', s=200, label='Drone', zorder=10)
    ax.scatter([0], [0], marker='x', s=100, color='red', label='Home')
    
    # Make the grid look nice
    ax.set_xlim(-300, 300)
    ax.set_ylim(-300, 300)
    ax.set_xlabel("West <---> East")
    ax.set_ylabel("South <---> North")
    ax.grid(True)
    ax.legend()
    
    st.pyplot(fig)

# --- 3. Streamlit App UI ---
st.set_page_config(page_title="DroneTalk", page_icon="🛰️", layout="wide")

if nlp:
    st.title("DroneTalk: Voice Pilots Interface")
    st.markdown("### Natural Language Drone Control System")

    user_command = st.text_input("Enter command:", placeholder="Try 'fly 75m north east' or 'take 5 photos'...")

    col1, col2, col3 = st.columns([1.2, 1, 1])

    with col1:
        st.subheader("Live Drone Map")
        plot_container = st.empty()
        with plot_container:
            plot_drone_position()

    if user_command:
        # Run Pipeline
        doc = nlp(user_command)
        spacy_intents = {k: v for k, v in doc.cats.items() if v > 0.5}
        spacy_slots = {ent.label_.lower(): ent.text for ent in doc.ents}
        
        spacy_output_json = {
            "command": user_command,
            "intents": list(spacy_intents.keys()),
            "slots": spacy_slots
        }
        
        final_command_json = generate_command(spacy_output_json)
        
        # --- UPDATED MOVEMENT LOGIC (DIAGONAL SUPPORT) ---
        if final_command_json.get("command") == "MOVE":
            dist = final_command_json.get("distance_meters", 0)
            direction = final_command_json.get("direction", "").lower()
            
            # Clean direction string for matching
            direction = direction.replace("-", " ")
            
            # Check for keywords to handle diagonals (e.g., "north east")
            if "north" in direction:
                st.session_state.y_pos += dist
            if "south" in direction:
                st.session_state.y_pos -= dist
            if "east" in direction:
                st.session_state.x_pos += dist
            if "west" in direction:
                st.session_state.x_pos -= dist
            
            if direction == "home":
                st.session_state.x_pos = 0
                st.session_state.y_pos = 0
                st.success("Returned to Home Base!")

            with plot_container:
                plot_drone_position()

        # Display Results
        with col2:
            st.subheader("AI Brain (spaCy)")
            st.json(spacy_output_json)
            
        with col3:
            st.subheader("Flight Controller")
            if final_command_json.get("command") == "REJECT":
                st.error("Command Rejected")
                st.json(final_command_json)
            else:
                st.success("Command Executed")
                st.json(final_command_json)