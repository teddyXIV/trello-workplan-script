import warnings 
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
import pandas as pd
from datetime import datetime as dt
import os
import requests
from dotenv import load_dotenv


# This is a experimental script for parsing an excel workplan and adding the information into a new trello board. 

load_dotenv()
API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")


# Path to the excel workplan. Change this to match the location for you own workplan. 
workplan_file = r"C:\Users\tpeterschmidt\Documents\Work Plan RMPC-FishReg.xlsx"

# Change the sheet_name to match the name of your sheet.
workplan_df = pd.read_excel(workplan_file, sheet_name="Trello Version")

# print("found the workplan", workplan_df.shape[0], "rows")

# Parsing out the different workplan elements. These will be used to create the trello baord, add the board members, and create the lists. 
new_board_name = workplan_df["BOARD NAME"].iloc[0]

new_board_members = workplan_df["BOARD MEMBERS"].iloc[0].split(", ")

new_lists = workplan_df["LIST NAME"].unique()

new_cards = workplan_df["CARD NAME"].unique()

# ==============================================================================================
# Creating the board.
# ==============================================================================================

# Get existing boards in the workspace to check if the board already exsits.
response = requests.get(
    "https://api.trello.com/1/organizations/{}/boards".format(os.getenv("WORKSPACE_ID")),
    params={
        "key": API_KEY,
        "token": TOKEN
    },
)

response.raise_for_status()

existing_board_names = {
    board["name"]: board["id"]
    for board in response.json()
}

# If the board already exists, use the existing board moving forward. If not, create the new board and use the new board.
if new_board_name in existing_board_names:
    board_id = existing_board_names[new_board_name]
    print(f"A board with the name '{new_board_name}' already exists.")
else:
    response = requests.post(
        "https://api.trello.com/1/boards/",
        params={
            "name": new_board_name,
            "key": API_KEY,
            "token": TOKEN,
            "idOrganization": WORKSPACE_ID,
            "defaultLists": "false"
        },
    )
    response.raise_for_status()

    board_id = response.json()["id"]
    print(f"Created a new board with the name '{new_board_name}'.")

# ==============================================================================================
# Creating the labels.
# ==============================================================================================

label_df = workplan_df[["CARD LABEL", "CARD LABEL COLOR"]].dropna().drop_duplicates()

label_definitions = {
    row["CARD LABEL"]: row["CARD LABEL COLOR"].lower().strip()
    for _, row in label_df.iterrows()
}

response = requests.get(
    f"https://api.trello.com/1/boards/{board_id}/labels",
    params={
        "key": API_KEY,
        "token": TOKEN
    }
)
response.raise_for_status()

existing_labels_dict = {label["name"].lower(): label["id"] for label in response.json()}

label_dict = existing_labels_dict.copy()

for name, color in label_definitions.items():
    key = name.lower().strip()

    if key in existing_labels_dict:
        print(f"A label with the name '{name}' already exists on the board.")
        continue

    response = requests.post(
        f"https://api.trello.com/1/boards/{board_id}/labels",
        params={
            "key": API_KEY,
            "token": TOKEN,
            "name": name,
            "color": color
        }
    )
    response.raise_for_status()

    label_dict[key] = response.json()["id"]

    print(f"✅ Created label '{name}' ({color})")

# ==============================================================================================
# Creating the lists.
# ==============================================================================================

# Check the board for any existing lists to avoid creating duplicates. 
response = requests.get(
    f"https://api.trello.com/1/boards/{board_id}/lists",
    params={
        "key": API_KEY,
        "token": TOKEN
    }
)
response.raise_for_status()
existing_list_names = {lst["name"] for lst in response.json()}

# If the list already exists, do not create a duplicate. If not, create the new list from the workplan.
for name in new_lists:
    if name in existing_list_names:
        print(f"A list with the name '{name}' already exists on the board.")
        continue

    response = requests.post (
        "https://api.trello.com/1/lists",
        params={
            "key": API_KEY,
            "token": TOKEN,
            "idBoard": board_id,
            "name": name
        }   ,
    )
    response.raise_for_status()
    print(f"Created a new list with the name '{name}' on the board.")

# ==============================================================================================
# Creating the cards. 
# ==============================================================================================

# Get all the lists on the board to get the list ids for creating the cards.
response = requests.get(
    f"https://api.trello.com/1/boards/{board_id}/lists",
    params={
        "key": API_KEY,
        "token": TOKEN
    }
)
response.raise_for_status()

lists = response.json()

list_dict = {lst["name"].lower(): lst["id"] for lst in lists}

# Get a list of all the cards on the board to avoid creating duplicates.
response = requests.get(
    f"https://api.trello.com/1/boards/{board_id}/cards",
    params={
        "key": API_KEY,
        "token": TOKEN
    }
)
response.raise_for_status()

cards = response.json()

existing_cards = {
    (card["idList"], card["name"].lower())
    for card in cards}

# Loop through the rows of cards in the workplan and create the cards on the trello board. 
for _, row in workplan_df.iterrows():
    list_name = row["LIST NAME"]
    card_name = row["CARD NAME"]
    start_date_raw = pd.to_datetime(row["CARD START DATE"], errors="coerce")
    end_date_raw = pd.to_datetime(row["CARD END DATE"], errors="coerce")


    if pd.isna(list_name) or pd.isna(card_name):
        continue

    list_id = list_dict.get(list_name.lower())

    if list_id is None:
        print(f"List '{list_name}' not found on the board. Skipping card '{card_name}'.")
        continue

    if (list_id, card_name.lower()) in existing_cards:
        print(f"A card with the name '{card_name}' already exists in the list '{list_name}'. Skipping.")
        continue
    
    if pd.notna(start_date_raw):
        start_date = start_date_raw.tz_localize("UTC").isoformat().replace("+00:00", "Z")
    else:
        start_date = None

    if pd.notna(end_date_raw):
        end_date = end_date_raw.tz_localize("UTC").isoformat().replace("+00:00", "Z")
    else:
        end_date = None

    label_id = label_dict.get(row["CARD LABEL"].lower())

    response = requests.post(
        "https://api.trello.com/1/cards",
        params={
            "key": API_KEY,
            "token": TOKEN,
            "idList": list_id,
            "name": card_name,
            "idLabels": label_id,
            "start": start_date,
            "due": end_date,
            "dueReminder": 120
        },
    )
    response.raise_for_status()

    card_id = response.json()["id"]

    response = requests.post(
        f"https://api.trello.com/1/cards/{card_id}/checklists",
        params={
            "key": API_KEY,
            "token": TOKEN,
            "name": card_name
        },
    )

    response.raise_for_status()

    # when testing with a workspace that has more members available, make the call to add members here. 

    existing_cards.add((list_id, card_name.lower()))

# ==============================================================================================
# Adding checklist items to the cards.
# ==============================================================================================

# Get a list of all checklists and their ids. 
response = requests.get(
    f"https://api.trello.com/1/boards/{board_id}/cards",
    params={
        "key": API_KEY,
        "token": TOKEN,
        "checklists": "all"
    }
)
response.raise_for_status()

cards = response.json()

existing_checklist_items = {
    (checklist["id"], item["name"].lower())
    for card in cards
    for checklist in card.get("checklists", [])
    for item in checklist.get("checkItems", [])
}

checklist_dict = {
    (card["name"].lower(), checklist["name"].lower()): checklist["id"]
    for card in cards
    for checklist in card.get("checklists", [])
}

for _, row in workplan_df.iterrows():
    card_name = row["CARD NAME"]
    checklist_item = row["CHECKLIST ITEM DESCRIPTION"]
    due_date_raw = pd.to_datetime(row["CHECKLIST ITEM DUE DATE"], errors="coerce")

    if pd.isna(card_name) or pd.isna(checklist_item):
        continue

    checklist_id = checklist_dict.get((card_name.lower(), card_name.lower()))

    if checklist_id is None:
        print(f"Checklist for card '{card_name}' not found. Skipping checklist item '{checklist_item}'.")
        continue

    if (checklist_id, checklist_item.lower()) in existing_checklist_items:
        print(f"A checklist item with the name '{checklist_item}' already exists in the checklist for card '{card_name}'. Skipping.")
        continue

    if pd.notna(due_date_raw):
        due_date = due_date_raw.tz_localize("UTC").isoformat().replace("+00:00", "Z")
    else:
        due_date = None

    response = requests.post(
        f"https://api.trello.com/1/checklists/{checklist_id}/checkItems",
        params={
            "key": API_KEY,
            "token": TOKEN,
            "name": checklist_item,
            "due": due_date
        },
    )
    response.raise_for_status()

    existing_checklist_items.add((checklist_id, checklist_item.lower()))


print("New board and lists ready.")




