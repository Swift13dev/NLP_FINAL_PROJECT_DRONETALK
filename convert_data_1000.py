import json
import random
import warnings
from spacy.tokens import DocBin, Doc
from spacy.training import Example
import spacy

def convert_to_docbin(data, nlp):
    """
    Converts our JSON data into a spaCy DocBin object.
    This is the official format for spaCy 3+ training.
    """
    db = DocBin()
    
    for text, annots in data:
        doc = nlp.make_doc(text)
        ents = []
        
        # Handle Slots (Entities)
        spans = []
        for start, end, label in annots.get("entities", []):
            span = doc.char_span(start, end, label=label)
            if span is None:
                # print(f"Skipping entity: {text[start:end]} in '{text}'")
                pass
            else:
                spans.append(span)
        
        try:
            doc.ents = spans
        except Exception as e:
            # Catches overlapping entity errors
            # print(f"Warning: {e} in text '{text}'")
            pass
        
        # Handle Intents (Categories)
        doc.cats = annots.get("cats", {})
        
        db.add(doc)
    return db

# --- Main Execution ---
if __name__ == "__main__":
    # Load the same base model we'll use for training
    nlp = spacy.load("en_core_web_sm") 
    print("Loaded base model 'en_core_web_sm'.")
    
    # 1. Load our NEW JSON data
    try:
        with open("spacy_training_data_1000.json", "r") as f:
            TRAIN_DATA = json.load(f)
        print(f"Loaded {len(TRAIN_DATA)} examples from spacy_training_data_1000.json.")
    except FileNotFoundError:
        print("ERROR: spacy_training_data_1000.json not found!")
        print("Please make sure you ran spacy_training_data_1000.py first!")
        exit()

    # 2. Shuffle and split the data (80% train, 20% dev)
    random.shuffle(TRAIN_DATA)
    split_point = int(len(TRAIN_DATA) * 0.8)
    train_data = TRAIN_DATA[:split_point]
    dev_data = TRAIN_DATA[split_point:]

    print(f"Splitting data: {len(train_data)} training, {len(dev_data)} development.")

    # 3. Suppress spaCy warnings
    warnings.filterwarnings("ignore", message=r".*\[W111\].*")
    
    # 4. Create and save the .spacy files with new names
    db_train = convert_to_docbin(train_data, nlp)
    db_train.to_disk("./train_1000.spacy")
    print("Created and saved train_1000.spacy")

    db_dev = convert_to_docbin(dev_data, nlp)
    db_dev.to_disk("./dev_1000.spacy")
    print("Created and saved dev_1000.spacy")