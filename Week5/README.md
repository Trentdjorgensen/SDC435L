# SDC435L / Trent Jorgensen & Horace Vial

## Project Description

This Python application uses SQLite to store, retrieve, update, delete, and analyze data from the GitHub Archive dataset. The program reads JSON-formatted GitHub data and stores selected information in SQLite so users can perform CRUD operations and view additional analysis features.

## Features

- Connects to a local SQLite database using Python.
- Reads JSON-formatted data from the GitHub Archive dataset.
- Automatically loads repository, commit, and programming language data into SQLite.
- Supports basic CRUD operations:
  - Create a repository record.
  - Read a repository record.
  - Update a repository record.
  - Delete a repository record.
- Displays the most popular repositories based on watch count.
- Analyzes the most common programming languages in the dataset.
- Allows users to search contributor history and view repositories they have contributed to.
- Includes error handling for missing files, invalid input, and Neo4j connection problems.

## Dependencies

The following software and packages are required:

- Python 3
- SQLite
- Python `sqlite3` package


The program also uses the following Python standard library modules:

- `json`
- `zipfile`

The `json` and `zipfile` modules are included with Python and do not require separate installation.

## Technical Requirements

- Python 3.x
- sqlite3 installed and running locally
- `GitHubArchive-Dataset.zip` located in the same directory as the Python program
- A system capable of running Python and SQLite

## Technologies Used

- Python
- SQLite
- JSON
- GitHub Archive Dataset
- Git
- GitHub

## Running the Application

1. Place `GitHubArchive-Dataset.zip` in the same folder as the Python file.
2. Install the sqlite3 Python package if needed:



4. Run the program:

```bash
python Week5-Group-SQLite.py
```

## Main Menu

The program provides the following options:

```text
1. Create a repository record
2. Read a repository record
3. Update a repository record
4. Delete a repository record
5. View most popular repositories
6. View top 10 programming languages
7. Search contributor history
8. Exit the program
```
