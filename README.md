# SDC435L / Trent Jorgensen & Horace Vial


## Project Description

This Python application uses Redis to store, retrieve, update, delete, and analyze data from the GitHub Archive dataset. The program reads JSON-formatted GitHub data and stores selected information in Redis so users can perform CRUD operations and view additional analysis features.

## Features

- Connects to a local Redis database using Python.
- Reads JSON-formatted data from the GitHub Archive dataset.
- Automatically loads repository, commit, and programming language data into Redis.
- Supports basic CRUD operations:
  - Create a repository record.
  - Read a repository record.
  - Update a repository record.
  - Delete a repository record.
- Displays the most popular repositories based on watch count.
- Analyzes the most common programming languages in the dataset.
- Allows users to search contributor history and view repositories they have contributed to.
- Uses Redis hashes, sets, and sorted sets to organize stored data.
- Includes error handling for missing files, invalid input, and Redis connection problems.

## Dependencies

The following software and packages are required:

- Python 3
- Redis Server
- Python `redis` package

Install the Redis Python package with:

```bash
pip install redis
```

The program also uses the following Python standard library modules:

- `json`
- `zipfile`

These modules are included with Python and do not require separate installation.

## Technical Requirements

- Python 3.x
- Redis installed and running locally
- Redis server available at:
  - Host: `127.0.0.1`
  - Port: `6379`
- `GitHubArchive-Dataset.zip` located in the same directory as the Python program
- Python `redis` package installed
- A system capable of running Python and Redis

## Technologies Used

- Python
- Redis
- JSON
- GitHub Archive Dataset
- Git
- GitHub

## Running the Application

1. Make sure Redis is installed and running.
2. Place `GitHubArchive-Dataset.zip` in the same folder as the Python file.
3. Install the Redis Python package if needed:

```bash
pip install redis
```

4. Run the program:

```bash
python Week1-GitHubArchive-vial.py
```

## Main Menu

The program provides the following options:

```text
1. Create a repository record
2. Read a repository record
3. Update a repository record
4. Delete a repository record
5. View most popular repositories
6. Analyze programming languages
7. Search contributor history
8. Exit
```
