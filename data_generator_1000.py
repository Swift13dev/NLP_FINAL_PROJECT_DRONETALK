import pandas as pd
import random

data = []
columns = ["command", "intent", "direction", "distance", "duration", "task", "count"]

print("Generating 1000+ drone commands...")

# --- 1. Define our "ingredients" ---
simple_directions = ["north", "south", "east", "west", "up", "down", "forward", "backward", "left", "right"]
diag_directions = ["north-east", "north-west", "south-east", "south-west", "NE", "NW", "SE", "SW", "north east", "north west", "south east", "south west"]
all_directions = simple_directions + diag_directions

distances = [f"{random.randint(5, 300)}m" for _ in range(20)] + \
            [f"{random.randint(20, 500)}ft" for _ in range(10)] + \
            [f"{random.uniform(0.5, 3.0):.1f}km" for _ in range(5)]

durations = [f"{random.randint(5, 60)}s" for _ in range(10)] + \
            [f"{random.randint(1, 10)}m" for _ in range(5)] + \
            [f"{random.randint(2, 20)} seconds" for _ in range(5)] + \
            [f"{random.randint(1, 5)} minutes" for _ in range(5)]

counts = [str(random.randint(1, 20)) for _ in range(15)]
count_words = ["pictures", "photos", "images", "shots", "pics"]

# --- 2. Generate FLY Commands (approx. 400) ---
fly_templates = [
    ("fly {dist} {dir}", "fly", "{dir}", "{dist}", "-", "-", "-"),
    ("go {dist} {dir}", "fly", "{dir}", "{dist}", "-", "-", "-"),
    ("move {dist} {dir}", "fly", "{dir}", "{dist}", "-", "-", "-"),
    ("head {dir} for {dist}", "fly", "{dir}", "{dist}", "-", "-", "-"),
    ("fly {dir}", "fly", "{dir}", "-", "-", "-", "-"),
    ("ascend {dist}", "fly", "up", "{dist}", "-", "-", "-"),
    ("descend {dist}", "fly", "down", "{dist}", "-", "-", "-"),
    ("climb {dist}", "fly", "up", "{dist}", "-", "-", "-"),
    ("lower {dist}", "fly", "down", "{dist}", "-", "-", "-"),
    ("move up by {dist}", "fly", "up", "{dist}", "-", "-", "-"),
    ("fly {dist}", "fly", "-", "{dist}", "-", "-", "-"),
    ("go {dist}", "fly", "-", "{dist}", "-", "-", "-"),
]
for _ in range(400):
    tpl, intent, dir_val, dist_val, dur_val, task_val, count_val = random.choice(fly_templates)
    d = random.choice(all_directions)
    dist = random.choice(distances)
    
    cmd_str = tpl.format(dist=dist, dir=d)
    dir_val = dir_val.format(dir=d) if "{dir}" in dir_val else dir_val
    dist_val = dist_val.format(dist=dist) if "{dist}" in dist_val else dist_val
    
    data.append([cmd_str, intent, dir_val, dist_val, dur_val, task_val, count_val])

# --- 3. Generate CAPTURE Commands (approx. 150) ---
capture_templates = [
    ("take {count} {c_word}", "capture", "-", "-", "-", "capture", "{count}"),
    ("snap {count} {c_word}", "capture", "-", "-", "-", "capture", "{count}"),
    ("capture {count} {c_word}", "capture", "-", "-", "-", "capture", "{count}"),
    ("take a photo", "capture", "-", "-", "-", "capture", "1"),
    ("snap a picture", "capture", "-", "-", "-", "capture", "1"),
    ("take {count} {c_word} of the {dir} side", "capture", "{dir}", "-", "-", "capture", "{count}"),
    ("get me {count} {c_word}", "capture", "-", "-", "-", "capture", "{count}"),
]
for _ in range(150):
    tpl, intent, dir_val, dist_val, dur_val, task_val, count_val = random.choice(capture_templates)
    c = random.choice(counts)
    d = random.choice(simple_directions) # Keep capture directions simple
    c_word = random.choice(count_words)

    cmd_str = tpl.format(count=c, dir=d, c_word=c_word)
    dir_val = dir_val.format(dir=d) if "{dir}" in dir_val else dir_val
    count_val = count_val.format(count=c) if "{count}" in count_val else count_val
    
    data.append([cmd_str, intent, dir_val, dist_val, dur_val, task_val, count_val])

# --- 4. Generate HOVER Commands (approx. 100) ---
hover_templates = [
    ("hover for {dur}", "hover", "-", "-", "{dur}", "-", "-"),
    ("stay still for {dur}", "hover", "-", "-", "{dur}", "-", "-"),
    ("hold position for {dur}", "hover", "-", "-", "{dur}", "-", "-"),
    ("hover in place", "hover", "-", "-", "-", "-", "-"),
]
for _ in range(100):
    tpl, intent, dir_val, dist_val, dur_val, task_val, count_val = random.choice(hover_templates)
    dur = random.choice(durations)
    
    cmd_str = tpl.format(dur=dur)
    dur_val = dur_val.format(dur=dur) if "{dur}" in dur_val else dur_val
    
    data.append([cmd_str, intent, dir_val, dist_val, dur_val, task_val, count_val])

# --- 5. Generate Other Simple Commands (approx. 150) ---
for intent in ["scan", "return", "land", "start", "stop", "takeoff"]:
    cmd_templates = {
        "scan": ["scan the area", "scan surroundings", "scan for {dur}", "scan the {dir} side for {dur}"],
        "return": ["return to base", "go home", "return to launch", "come back now", "RTL"],
        "land": ["land", "land the drone", "touchdown", "land at home base"],
        "start": ["start mission", "begin", "start recording", "start scan", "initiate sequence"],
        "stop": ["stop", "halt", "stop recording", "abort mission", "emergency stop"],
        "takeoff": ["take off", "launch", "get in the air", "initiate takeoff"]
    }
    task_map = {"scan": "scan", "start": "record", "stop": "record"}

    for _ in range(25): # 25 examples for each
        cmd_str = random.choice(cmd_templates[intent])
        d = random.choice(simple_directions)
        dur = random.choice(durations)
        
        cmd_str = cmd_str.format(dur=dur, dir=d)
        
        dir_val = d if "{dir}" in cmd_str else "-"
        dur_val = dur if "{dur}" in cmd_str else "-"
        task_val = task_map.get(intent, "-")

        data.append([cmd_str, intent, dir_val, "-", dur_val, task_val, "-"])

# --- 6. Generate COMPLEX/COMPOUND Commands (approx. 200) ---
# This is key to fixing our bugs!
compound_templates = [
    ("fly {dist} {dir} and take {count} {c_word}", "fly", "{dir}", "{dist}", "-", "capture", "{count}"),
    ("go {dist} {dir} then scan for {dur}", "fly", "{dir}", "{dist}", "{dur}", "scan", "-"),
    ("climb {dist} and hover", "fly", "up", "{dist}", "-", "hover", "-"),
    ("move {dist} {dir} and record video for {dur}", "fly", "{dir}", "{dist}", "{dur}", "record", "-"),
    ("take {count} {c_word} then land", "capture", "-", "-", "-", "land", "{count}"),
    ("scan for {dur} then return to base", "scan", "-", "-", "{dur}", "return", "-"),
    ("take off and go {dist} {dir}", "takeoff", "{dir}", "{dist}", "-", "fly", "-"),
    ("hover for {dur} then take {count} {c_word}", "hover", "-", "-", "{dur}", "capture", "{count}"),
]

for _ in range(200):
    tpl, intent, dir_val, dist_val, dur_val, task_val, count_val = random.choice(compound_templates)
    d = random.choice(all_directions) # Use all directions here
    dist = random.choice(distances)
    dur = random.choice(durations)
    c = random.choice(counts)
    c_word = random.choice(count_words)

    cmd_str = tpl.format(dist=dist, dir=d, dur=dur, count=c, c_word=c_word)
    dir_val = dir_val.format(dir=d) if "{dir}" in dir_val else dir_val
    dist_val = dist_val.format(dist=dist) if "{dist}" in dist_val else dist_val
    dur_val = dur_val.format(dur=dur) if "{dur}" in dur_val else dur_val
    count_val = count_val.format(count=c) if "{count}" in count_val else count_val

    data.append([cmd_str, intent, dir_val, dist_val, dur_val, task_val, count_val])


# --- 7. Create and Save DataFrame ---
df = pd.DataFrame(data, columns=columns)
# Remove any accidental duplicates
df = df.drop_duplicates(subset=["command"])

# Save to CSV
df.to_csv("drone_commands_1000.csv", index=False)

print(f"Dataset created successfully: drone_commands_1000.csv")
print(f"Total commands generated: {len(df)}")