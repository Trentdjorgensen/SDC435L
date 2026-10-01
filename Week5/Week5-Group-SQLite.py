#Horace Vial & Trent Jorgensen
#10/01/2026
#GitHub Archive SQLite Project
#Python application that stores and analyzes GitHub Archive data using SQLite

import sqlite3
import json
import zipfile


#Name of the dataset ZIP file
DATASET_ZIP = "GitHubArchive-Dataset.zip"

#The Languages file is very large, so only a portion is used for analysis.
LANGUAGE_RECORD_LIMIT = 10000


#Connect to the SQLite database
print("Connecting to local SQLite database...")
db = sqlite3.connect("GitHubArchive.db")


# *** CREATE SECTION ***

#Create the Repositories table
newTable = '''
    CREATE TABLE IF NOT EXISTS Repositories (
        repo_name TEXT PRIMARY KEY,
        watch_count INTEGER
    );
'''

db.execute(newTable)
print("Repositories Table Created!")


#Create the Commits table
newTable = '''
    CREATE TABLE IF NOT EXISTS Commits (
        commit_id TEXT PRIMARY KEY,
        author_name TEXT,
        repo_name TEXT,
        subject TEXT
    );
'''

db.execute(newTable)
print("Commits Table Created!")


#Create the Languages table
newTable = '''
    CREATE TABLE IF NOT EXISTS Languages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_name TEXT,
        language_name TEXT
    );
'''

db.execute(newTable)
print("Languages Table Created!")


#Check if repository data has already been loaded
query = "SELECT COUNT(*) FROM Repositories;"
resultSet = db.execute(query)

repositoryCount = 0

for row in resultSet:
    repositoryCount = row[0]


#Load repository data if the table is empty
if repositoryCount == 0:

    print("Loading repository data...")

    with zipfile.ZipFile(DATASET_ZIP, "r") as archive:

        path = "GitHubArchive-Dataset/Sample_Repos.json"

        with archive.open(path) as file:

            for line in file:

                line = line.decode("utf-8").strip()

                if line:

                    dataSet = json.loads(line)

                    repoName = str(dataSet.get("repo_name", ""))
                    watchCount = dataSet.get("watch_count", 0)

                    if repoName != "":

                        insert = "INSERT OR IGNORE INTO Repositories "
                        insert += "(repo_name, watch_count) VALUES("
                        insert += "'" + repoName.replace("'", "''") + "', "
                        insert += str(watchCount) + ");"

                        db.execute(insert)

    db.commit()
    print("Repository data loaded successfully.")


#Check if commit data has already been loaded
query = "SELECT COUNT(*) FROM Commits;"
resultSet = db.execute(query)

commitCount = 0

for row in resultSet:
    commitCount = row[0]


#Load commit data if the table is empty
if commitCount == 0:

    print("Loading commit data...")

    with zipfile.ZipFile(DATASET_ZIP, "r") as archive:

        path = "GitHubArchive-Dataset/Sample_Commits.json"

        with archive.open(path) as file:

            for line in file:

                line = line.decode("utf-8").strip()

                if line:

                    dataSet = json.loads(line)

                    commitID = str(dataSet.get("commit", ""))
                    repoName = str(dataSet.get("repo_name", ""))
                    subject = str(dataSet.get("subject", ""))

                    author = dataSet.get("author")

                    if author is None:
                        authorName = ""
                    else:
                        authorName = str(author.get("name", ""))

                    if commitID != "":

                        insert = "INSERT OR IGNORE INTO Commits "
                        insert += "(commit_id, author_name, repo_name, "
                        insert += "subject) VALUES("
                        insert += "'" + commitID.replace("'", "''") + "', "
                        insert += "'" + authorName.replace("'", "''") + "', "
                        insert += "'" + repoName.replace("'", "''") + "', "
                        insert += "'" + subject.replace("'", "''") + "');"

                        db.execute(insert)

    db.commit()
    print("Commit data loaded successfully.")


#Check if language data has already been loaded
query = "SELECT COUNT(*) FROM Languages;"
resultSet = db.execute(query)

languageCount = 0

for row in resultSet:
    languageCount = row[0]


#Load language data if the table is empty
if languageCount == 0:

    print("Loading language data...")

    with zipfile.ZipFile(DATASET_ZIP, "r") as archive:

        path = "GitHubArchive-Dataset/Languages.json"

        with archive.open(path) as file:

            recordCount = 0

            for line in file:

                if recordCount >= LANGUAGE_RECORD_LIMIT:
                    break

                line = line.decode("utf-8").strip()

                if line:

                    dataSet = json.loads(line)

                    repoName = str(dataSet.get("repo_name", ""))
                    languages = dataSet.get("language", [])

                    for language in languages:

                        languageName = str(language.get("name", ""))

                        if languageName != "":

                            insert = "INSERT INTO Languages "
                            insert += "(repo_name, language_name) VALUES("
                            insert += "'" + repoName.replace("'", "''") + "', "
                            insert += "'" + languageName.replace("'", "''")
                            insert += "');"

                            db.execute(insert)

                    recordCount += 1

    db.commit()
    print("Language data loaded successfully.")


# *** MENU SECTION ***

while True:

    print("\nType in a number and press enter to execute the menu option.")
    print("1. Create a repository record")
    print("2. Read a repository record")
    print("3. Update a repository record")
    print("4. Delete a repository record")
    print("5. View most popular repositories")
    print("6. View top 10 programming languages")
    print("7. Search contributor history")
    print("8. Exit the program")

    choice = input()


    # *** CREATE SECTION ***

    if choice == "1":

        repoName = input("Enter the repository name: ").strip()

        if repoName == "":

            print("Repository name cannot be blank.")

        else:

            query = "SELECT * FROM Repositories WHERE repo_name = '"
            query += repoName.replace("'", "''") + "';"

            resultSet = db.execute(query)

            repositoryFound = False

            for row in resultSet:
                repositoryFound = True

            if repositoryFound == True:

                print("A repository with that name already exists.")

            else:

                watchCount = input("Enter the watch count: ").strip()

                if watchCount.isdigit():

                    insert = "INSERT INTO Repositories "
                    insert += "(repo_name, watch_count) VALUES("
                    insert += "'" + repoName.replace("'", "''") + "', "
                    insert += watchCount + ");"

                    db.execute(insert)
                    db.commit()

                    print("Repository record added successfully.")

                else:

                    print("Watch count must be a number.")


    # *** READ SECTION ***

    elif choice == "2":

        repoName = input("Enter the repository name: ").strip()

        query = "SELECT repo_name, watch_count "
        query += "FROM Repositories WHERE repo_name = '"
        query += repoName.replace("'", "''") + "';"

        resultSet = db.execute(query)

        repositoryFound = False

        for row in resultSet:

            repositoryFound = True

            print("\nRepository Information")
            print("----------------------")
            print(row)

        if repositoryFound == False:

            print("Repository was not found.")


    # *** UPDATE SECTION ***

    elif choice == "3":

        repoName = input(
            "Enter the repository name to update: "
        ).strip()

        query = "SELECT * FROM Repositories WHERE repo_name = '"
        query += repoName.replace("'", "''") + "';"

        resultSet = db.execute(query)

        repositoryFound = False

        for row in resultSet:
            repositoryFound = True

        if repositoryFound == False:

            print("Repository was not found.")

        else:

            watchCount = input(
                "Enter the new watch count: "
            ).strip()

            if watchCount.isdigit():

                update = "UPDATE Repositories SET watch_count = "
                update += watchCount
                update += " WHERE repo_name = '"
                update += repoName.replace("'", "''") + "';"

                db.execute(update)
                db.commit()

                print("Repository record updated successfully.")

            else:

                print("Watch count must be a number.")


    # *** DELETE SECTION ***

    elif choice == "4":

        repoName = input(
            "Enter the repository name to delete: "
        ).strip()

        query = "SELECT * FROM Repositories WHERE repo_name = '"
        query += repoName.replace("'", "''") + "';"

        resultSet = db.execute(query)

        repositoryFound = False

        for row in resultSet:
            repositoryFound = True

        if repositoryFound == False:

            print("Repository was not found.")

        else:

            delete = "DELETE FROM Repositories WHERE repo_name = '"
            delete += repoName.replace("'", "''") + "';"

            db.execute(delete)
            db.commit()

            print("Repository record deleted successfully.")


    # *** FEATURE 1 SECTION ***

    elif choice == "5":

        print("\nTop 10 Most Popular Repositories")
        print("--------------------------------")

        query = '''
            SELECT repo_name, watch_count
            FROM Repositories
            ORDER BY watch_count DESC
            LIMIT 10;
        '''

        resultSet = db.execute(query)

        number = 1

        for row in resultSet:

            print(
                str(number)
                + ". "
                + str(row[0])
                + " - "
                + str(row[1])
                + " watchers"
            )

            number += 1


    # *** FEATURE 2 SECTION ***

    elif choice == "6":

        print("\nTop 10 Programming Languages")
        print("----------------------------")

        query = '''
            SELECT language_name, COUNT(language_name)
            FROM Languages
            GROUP BY language_name
            ORDER BY COUNT(language_name) DESC
            LIMIT 10;
        '''

        resultSet = db.execute(query)

        number = 1

        for row in resultSet:

            print(
                str(number)
                + ". "
                + str(row[0])
                + " - "
                + str(row[1])
                + " repositories"
            )

            number += 1

        print(
            "\nAnalysis is based on the first "
            + str(LANGUAGE_RECORD_LIMIT)
            + " language records."
        )


    # *** FEATURE 3 SECTION ***

    elif choice == "7":

        searchName = input(
            "Enter the contributor name: "
        ).strip()

        if searchName == "":

            print("Contributor name cannot be blank.")

        else:

            query = '''
                SELECT author_name, repo_name
                FROM Commits
                WHERE LOWER(author_name) LIKE
            '''

            query += "'%" + searchName.lower().replace("'", "''") + "%' "
            query += "ORDER BY author_name, repo_name;"

            resultSet = db.execute(query)

            contributors = {}

            for row in resultSet:

                authorName = row[0]
                repoName = row[1]

                if authorName not in contributors:
                    contributors[authorName] = []

                contributors[authorName].append(repoName)

            if len(contributors) == 0:

                print("No matching contributor was found.")

            else:

                for authorName in contributors:

                    print("\nContributor:", authorName)
                    print(
                        "Number of commits:",
                        len(contributors[authorName])
                    )

                    print("Repositories contributed to:")

                    repositoryList = []

                    for repoName in contributors[authorName]:

                        if repoName not in repositoryList:
                            repositoryList.append(repoName)

                    for repoName in repositoryList:
                        print("-", repoName)


    elif choice == "8":

        print("Exiting program.")
        break


    else:

        print("Please enter only 1-8")


#Close connection to database
db.close()
