# trello-workplan-script
Python script for creating a new board and cards from an excel sheet for project tracking.

## How to use
- Clone the script to your machine. 
- Create a workplan in the same structure as the template found in the root directory.
- Get your Trello API key and token.
    - Head to the [Trello Power Ups Admin page](https://trello.com/power-ups/admin) and click the "New" button. 
    - Fill out the fields in the next page. You can skip the "Ifram connector URL" field. 
    - Generate your API key and follow Trello's instructions for generating a token. 
- Get your "Workspace ID" from Trello. .
    - In the search bar, enter this URL with your workspace name, key, and token: https://api.trello.com/1/organizations/{WORKSPACE_NAME}?key={API_KEY}&token={TOKEN}
    - Grab the value in the "id" field. 
- In the root directory of the repo, create a file called ".env"
- In the .env file, paste the following and populate with your Workspace ID, API key, and token:
```
TRELLO_API_KEY={YOUR_API_KEY}
TRELLO_TOKEN={YOUR_TOKEN}
WORKSPACE_{ID=YOUR_WORKSPACE_ID}
```
- In the "parse_workplan.py" adjust the file location to your workplan as needed. 
- Run the script. A new Trello board, with members, labels, lists, cards, checklists, and checklist items will be created.  
