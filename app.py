import streamlit as st
import spacy
import json
import re
import matplotlib.pyplot as plt
import os

# --- 1. Smart Model Loader ---
@st.cache_resource
def load_model():
    # Get the absolute path of the directory this script is in
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path 1: The expected path from our project
    model_path_standard = os.path.join(script_dir, "model_output_1000", "model-best")
    
    # Path 2: Just the model-best folder in the root
    model_path_flat = os.path.join(script_dir, "model-best")
    
    # Path 3: The root directory itself
    model_path_root = script_dir

    if os.path.exists(model_path_standard):
        return spacy.load(model_path_standard)
    elif os.path.exists(model_path_flat):
        return spacy.load(model_path_flat)
    elif os.path.exists(os.path.join(model_path_root, "config.cfg")):
        return spacy.load(model_path_root)
    else:
        st.error("ERROR: Could not find model files.")
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
    intent = None
    slots = parsed_json["slots"]
    
    if parsed_json["intents"]:
        intent = parsed_json["intents"][0]
    else:
        # Fallback: If no intent, but we have slots, guess 'fly'
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
            # Bug fix: check distance slot if count is missing
            count = clean_value(slots.get("distance")) 
        if not count:
            count = 1
        final_command = {"command": "CAPTURE_IMAGE", "count": int(count)}
    
    elif intent == "scan":
         final_command = {"command": "SCAN_AREA"}

    elif intent == "return":
        # Special move command to go home
        final_command = {"command": "MOVE", "direction": "home", "distance_meters": 0}
        
    elif intent == "takeoff":
        final_command = {"command": "TAKEOFF"}

    else:
        final_command = {"command": intent.upper()}

    return final_command

# --- 3. Initialize Drone State (Session Memory) ---
if 'x_pos' not in st.session_state:
    st.session_state.x_pos = 0
if 'y_pos' not in st.session_state:
    st.session_state.y_pos = 0

# --- 4. Plotting Function ---
def plot_drone_position():
    x = st.session_state.x_pos
    y = st.session_state.y_pos
    
    fig, ax = plt.subplots()
    ax.scatter([x], [y], marker='o', s=200, label='Drone', zorder=10)
    ax.scatter([0], [0], marker='x', s=100, color='red', label='Home')
    
    # Set plot limits
    ax.set_xlim(-300, 300)
    ax.set_ylim(-300, 300)
    ax.set_xlabel("West <---> East")
    ax.set_ylabel("South <---> North")
    ax.grid(True)
    ax.legend()
    
    st.pyplot(fig)

# --- 5. Build the Streamlit App UI ---
st.set_page_config(page_title="DroneTalk", layout="wide")

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
        # --- Run Full Pipeline ---
        doc = nlp(user_command)
        spacy_intents = {k: v for k, v in doc.cats.items() if v > 0.5}
        spacy_slots = {ent.label_.lower(): ent.text for ent in doc.ents}
        
        spacy_output_json = {
            "command": user_command,
            "intents": list(spacy_intents.keys()),
            "slots": spacy_slots
        }
        
        final_command_json = generate_command(spacy_output_json)
        
        # --- Update Movement Logic (with Diagonal Support) ---
        if final_command_json.get("command") == "MOVE":
            dist = final_command_json.get("distance_meters", 0)
            direction = final_command_json.get("direction", "").lower()
            
            # Clean direction string for matching
            direction = direction.replace("-", " ")
            
            # Check for keywords to handle diagonals
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

            # Redraw the plot
            with plot_container:
                plot_drone_position()

        # --- Display Results ---
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
else:
    st.error("Model is not loaded. Please check the logs.")