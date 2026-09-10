# SDC435L
**Trent Jorgensen & Horace Vial**  
**ECPI University**

## Project Overview

This repository contains the SDC435L GitHub Archive database project.

The project uses Python to work with GitHub Archive data using different database technologies. Each week is stored in its own folder so the work for each assignment remains organized and separate.

## Repository Structure

### Week 1 - Redis

The Week1 folder contains the Redis version of the GitHub Archive project.

The application:

- Reads JSON-formatted GitHub Archive data
- Stores repository, commit, and language data in Redis
- Performs Create, Read, Update, and Delete operations
- Displays the most popular repositories based on watch count
- Analyzes the most common programming languages
- Allows users to search contributor commit history

Main file:

`Week1-Group-Redis.py`

---

### Week 2 - MongoDB

The Week2 folder contains the MongoDB version of the GitHub Archive project.

The application:

- Reads JSON-formatted GitHub Archive data
- Stores repository, commit, and language data in MongoDB
- Performs Create, Read, Update, and Delete operations
- Displays the most popular repositories based on watch count
- Analyzes the most common programming languages
- Allows users to search contributor commit history

Main file:

`Week2-Group-MongoDB.py`

## Technologies Used

- Python
- Redis
- MongoDB
- PyMongo
- JSON
- GitHub

## Dataset

The applications use the GitHub Archive dataset contained in:

`GitHubArchive-Dataset.zip`

The dataset includes repository, commit, and programming language information used by the weekly applications.
