import pandas as pd
import re
import json
import warnings

# --- 1. Define Intent Keywords ---
INTENT_KEYWORDS = {
    "fly": ["fly", "move", "go", "climb", "ascend", "descend", "strafe", "advance", "retreat", "lower", "head"],
    "land": ["land", "touchdown", "bring it down"],
    "hover": ["hover", "stay", "hold position", "stay still"],
    "capture": ["take", "capture", "photo", "picture", "image", "snap", "shot"],
    "record": ["record", "video"],
    "scan": ["scan", "survey", "inspect"],
    "return": ["return", "come back", "go home", "base", "launch", "rtl"],
    "start": ["start", "begin", "initiate"],
    "stop": ["stop", "end", "halt", "abort"],
    "takeoff": ["takeoff", "launch", "get in the air"]
}
ALL_INTENTS = list(INTENT_KEYWORDS.keys())

# --- 2. Compile Regex Patterns (Upgraded for new data) ---
PATTERNS = {
    # Added 'ft', 'feet', 'km', 'kilometers'
    "DISTANCE": re.compile(r'\b(?P<value>\d+(\.\d+)?)\s*(?P<unit>m|meters|ft|feet|km|kilometers)\b', re.I),
    
    # *** THIS IS THE KEY UPGRADE ***
    # It now finds "north east" (with a space) as one entity
    "DIRECTION": re.compile(r'\b(north\s+east|north\s+west|south\s+east|south\s+west|north-east|north-west|south-east|south-west|north|south|east|west|up|down|left|right|forward|backward|ne|nw|se|sw)\b', re.I),
    
    # Added 'min', 'minutes'
    "DURATION": re.compile(r'\b(?P<value>\d+)\s*(?P<unit>s|sec|seconds|m|min|minutes)\b', re.I),
    
    # Added more count words
    "COUNT": re.compile(r'\b(?P<value>\d+)\s*(pictures|photos|images|pic|photo|shots)\b', re.I),
    "COUNT_SIMPLE": re.compile(r'\b(take|snap|get|capture)\s+(?P<value>\d+)\b', re.I)
}

# --- 3. The Conversion Function ---
def convert_to_spacy_format(df):
    training_data = []
    
    for _, row in df.iterrows():
        command = str(row['command'])
        if pd.isna(command):
            continue

        command_lower = command.lower()
        
        # --- A. Find Slots (NER Entities) ---
        entities = []
        
        # We must find the LONGEST match first (e.g., "north east" before "east")
        # To do this, we find all matches, sort them by length, and remove overlaps
        all_matches = []
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(command):
                span = (match.start(), match.end(), label)
                
                # Handle simple count pattern (e.g., "take 3")
                if label == "COUNT_SIMPLE":
                    val_start, val_end = match.span('value')
                    span = (val_start, val_end, "COUNT") # Just label the "3"

                all_matches.append(span)

        # Sort matches by start position, then by length (longest first)
        all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

        # Add non-overlapping entities
        current_pos = -1
        for start, end, label in all_matches:
            if start >= current_pos:
                entities.append((start, end, label))
                current_pos = end
            
        # --- B. Find Intents (Text Categories) ---
        cats = {intent: False for intent in ALL_INTENTS}
        found_intent = False
        for intent, keywords in INTENT_KEYWORDS.items():
            for kw in keywords:
                if re.search(rf"\b{kw}\b", command_lower):
                    cats[intent] = True
                    found_intent = True
        
        if not found_intent:
            continue 

        # --- C. Create the final spaCy data tuple ---
        spacy_example = (command, {"entities": entities, "cats": cats})
        training_data.append(spacy_example)
        
    return training_data

# --- 4. Main Execution ---
if __name__ == "__main__":
    try:
        # *** THIS IS THE IMPORTANT CHANGE ***
        df = pd.read_csv("drone_commands_1000.csv")
        print(f"Loaded {len(df)} commands from drone_commands_1000.csv.")
        
        warnings.filterwarnings("ignore", message=r".*overlapping spans.*")

        spacy_data = convert_to_spacy_format(df)
        
        print(f"Converted {len(spacy_data)} commands to spaCy format.")

        # Save to a new JSON file
        with open("spacy_training_data_1000.json", "w") as f:
            json.dump(spacy_data, f, indent=2)
            
        print(f"Saved training data to spacy_training_data_1000.json")

        # --- Show a sample of what we created ---
        print("\n--- Example of Training Data ---")
        # Find a good example to show
        sample = None
        for ex in spacy_data:
            if "north east" in ex[0]:
                 sample = ex
                 break
        if not sample:
            sample = spacy_data[0] # Fallback
            
        print(f"Text: {sample[0]}")
        print("Annotations: {")
        print(f"  \"entities\": {sample[1]['entities']},")
        print(f"  \"cats\": {{k: v for k, v in sample[1]['cats'].items() if v}}") # Only show True cats
        print("}")

    except FileNotFoundError:
        print("ERROR: drone_commands_1000.csv not found.")
        print("Please make sure you ran data_generator_1000.py first!")
    except Exception as e:
        print(f"An error occurred: {e}")