import warnings 
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
import numpy as np
import pandas as pd
from datetime import datetime as dt
import os
import requests
from dotenv import load_dotenv
import sys


# This is a experimental script for parsing an excel workplan and adding the information into a new trello board. 

load_dotenv()

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

# print("Unique lists in the workplan:", unique_lists)
# print("Board name:", new_board_name)
# print("Board members:", new_board_members)
# print("Unique cards in the workplan:", new_cards)

response = requests.get(
    "https://api.trello.com/1/organizations/{}/boards".format(os.getenv("WORKSPACE_ID")),
    params={
        "key": os.getenv("TRELLO_API_KEY"),
        "token": os.getenv("TRELLO_TOKEN")
    },
)

response.raise_for_status()

existing_board_names = {
    board["name"]: board["id"]
    for board in response.json()
}

if new_board_name in existing_board_names:
    board_id = existing_board_names[new_board_name]
    print(f"A board with the name '{new_board_name}' already exists.")
else:
    response = requests.post(
        "https://api.trello.com/1/boards/",
        params={
            "name": new_board_name,
            "key": os.getenv("TRELLO_API_KEY"),
            "token": os.getenv("TRELLO_TOKEN"),
            "idOrganization": os.getenv("WORKSPACE_ID"),
            "defaultLists": "false"
        },
    )
    response.raise_for_status()

    board_id = response.json()["id"]
    print(f"Created a new board with the name '{new_board_name}'.")

response = requests.get(
    f"https://api.trello.com/1/boards/{board_id}/lists",
    params={
        "key": os.getenv("TRELLO_API_KEY"),
        "token": os.getenv("TRELLO_TOKEN")
    }
)
response.raise_for_status()
existing_list_names = {lst["name"] for lst in response.json()}

for name in new_lists:
    if name in existing_list_names:
        print(f"A list with the name '{name}' already exists on the board.")
        continue

    response = requests.post (
        "https://api.trello.com/1/lists",
        params={
            "key": os.getenv("TRELLO_API_KEY"),
            "token": os.getenv("TRELLO_TOKEN"),
            "idBoard": board_id,
            "name": name
        }   ,
    )
    response.raise_for_status()
    print(f"Created a new list with the name '{name}' on the board.")

print("New board and lists ready.")





#         "key": os.getenv("TRELLO_API_KEY"),
#         "token": os.getenv("TRELLO_TOKEN"),
#         "idOrganization": os.getenv("WORKSPACE_ID")
#     }
# ).json()

# existing_board_names = {
#     board["name"]: board["id"]
#     for board in existing_boards
# }

# board_id = None
# existing_board_detected = False

# if new_board_name in existing_board_names:
#     board_id = existing_board_names[new_board_name]
#     existing_board_detected = True
#     print(f"A board with the name '{new_board_name}' already exists.")
# else:
#     board = requests.post(
#         "https://api.trello.com/1/boards/",
#         params={
#             "name": new_board_name,
#             "key": os.getenv("TRELLO_API_KEY"),
#             "token": os.getenv("TRELLO_TOKEN"),
#             "idOrganization": os.getenv("WORKSPACE_ID"),
#             "defaultLists": "false"
#         }
#     ).json()

#     board_id = board["id"]


# if not existing_board_detected:
#     for name in new_lists:
#         requests.post(
#             "https://api.trello.com/1/lists",
#             params={
#                 "key": os.getenv("TRELLO_API_KEY"),
#                 "token": os.getenv("TRELLO_TOKEN"),
#                 "idBoard": board_id,
#                 "name": name
#             }   
#         )
# else:
#     existing_lists = requests.get(
#         f"https://api.trello.com/1/boards/{board_id}/lists",
#         params={
#             "key": os.getenv("TRELLO_API_KEY"),
#             "token": os.getenv("TRELLO_TOKEN"),
#         }   
#     ).json()

#     for name in new_lists:
#         if name not in [lst["name"] for lst in existing_lists]:
#             requests.post(
#                 "https://api.trello.com/1/lists",
#                 params={
#                     "key": os.getenv("TRELLO_API_KEY"),
#                     "token": os.getenv("TRELLO_TOKEN"),
#                     "idBoard": board_id,
#                     "name": name
#                 }   
#             )



# print("Created the board and lists.")