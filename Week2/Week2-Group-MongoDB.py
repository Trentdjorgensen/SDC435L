#Horace Vial
#09/10/2026
#GitHub Archive MongoDB Project
#Python application that stores and analyzes GitHub Archive data using MongoDB

import json
import zipfile
import pymongo


#Name of the dataset ZIP file
DATASET_ZIP = "GitHubArchive-Dataset.zip"

#The Languages file is very large, so only a portion is used for analysis.
LANGUAGE_RECORD_LIMIT = 10000

prompt = "Type in a number and press enter to execute the menu option."


def read_json_lines(file_name, limit=None):
    """Read JSON objects from a file stored inside the dataset ZIP."""
    records = []

    try:
        with zipfile.ZipFile(DATASET_ZIP, "r") as archive:
            path = "GitHubArchive-Dataset/" + file_name

            with archive.open(path) as file:
                for line_number, line in enumerate(file):
                    if limit is not None and line_number >= limit:
                        break

                    line = line.decode("utf-8").strip()

                    if line:
                        records.append(json.loads(line))

    except FileNotFoundError:
        print("\n[ERROR] GitHubArchive-Dataset.zip was not found.")
    except KeyError:
        print(f"\n[ERROR] {file_name} was not found in the dataset ZIP.")
    except json.JSONDecodeError:
        print(f"\n[ERROR] A record in {file_name} could not be read.")

    return records


def connectDB():
    """Connect to MongoDB and return the database and collections."""
    print("Connecting to local Mongo database...")

    myClient = pymongo.MongoClient("mongodb://localhost:27017/")

    #Use the GitHubArchive MongoDB database
    db = myClient["GitHubArchive"]

    #Collections used by the application
    repositoryCollection = db["Repositories"]
    commitCollection = db["Commits"]
    languageCollection = db["Languages"]

    return myClient, db, repositoryCollection, commitCollection, languageCollection


def load_repository_data(repositoryCollection):
    """Load repository data into MongoDB if the collection is empty."""
    if repositoryCollection.count_documents({}) > 0:
        return

    print("Loading repository data...")

    records = read_json_lines("Sample_Repos.json")

    if records:
        repositoryCollection.insert_many(records)
        print("Repository data loaded successfully.")


def load_commit_data(commitCollection):
    """Load commit data into MongoDB if the collection is empty."""
    if commitCollection.count_documents({}) > 0:
        return

    print("Loading commit data...")

    records = read_json_lines("Sample_Commits.json")

    if records:
        commitCollection.insert_many(records)
        print("Commit data loaded successfully.")


def load_language_data(languageCollection):
    """Load language data into MongoDB if the collection is empty."""
    if languageCollection.count_documents({}) > 0:
        return

    print("Loading language data...")

    records = read_json_lines("Languages.json", LANGUAGE_RECORD_LIMIT)

    if records:
        languageCollection.insert_many(records)
        print("Language data loaded successfully.")


def initialize_database(repositoryCollection, commitCollection, languageCollection):
    """Load the GitHub Archive data needed by the application."""
    load_repository_data(repositoryCollection)
    load_commit_data(commitCollection)
    load_language_data(languageCollection)


#User main menu
def main_menu():
    print("\n" + "=" * 35)
    print("        GITHUB ARCHIVE MENU")
    print("=" * 35)
    print("1. Create a repository record")
    print("2. Read a repository record")
    print("3. Update a repository record")
    print("4. Delete a repository record")
    print("5. View most popular repositories")
    print("6. Analyze programming languages")
    print("7. Search contributor history")
    print("8. Exit the program")


#Create
def create_repository(repositoryCollection):
    """Create a new repository document in MongoDB."""
    repo_name = input("Enter the repository name: ").strip()

    if repo_name == "":
        print("Repository name cannot be blank.")
        return

    if repositoryCollection.find_one({"repo_name": repo_name}) is not None:
        print("A repository with that name already exists.")
        return

    watch_count = input("Enter the watch count: ").strip()

    if not watch_count.isdigit():
        print("Watch count must be a number.")
        return

    newDocument = {
        "repo_name": repo_name,
        "watch_count": int(watch_count)
    }

    result = repositoryCollection.insert_one(newDocument)

    print("Repository record added successfully.")
    print("MongoDB document ID:", result.inserted_id)


#Read
def read_repository(repositoryCollection):
    """Retrieve and display one repository document using find_one()."""
    repo_name = input("Enter the repository name: ").strip()

    repository = repositoryCollection.find_one(
        {"repo_name": repo_name},
        {"_id": False}
    )

    if repository is not None:
        print("\nRepository Information")
        print("----------------------")
        print(repository)
    else:
        print("Repository was not found.")


#Update
def update_repository(repositoryCollection):
    """Update the watch count of an existing repository document."""
    repo_name = input("Enter the repository name to update: ").strip()

    repository = repositoryCollection.find_one({"repo_name": repo_name})

    if repository is None:
        print("Repository was not found.")
        return

    watch_count = input("Enter the new watch count: ").strip()

    if not watch_count.isdigit():
        print("Watch count must be a number.")
        return

    result = repositoryCollection.update_one(
        {"repo_name": repo_name},
        {"$set": {"watch_count": int(watch_count)}}
    )

    if result.modified_count > 0:
        print("Repository record updated successfully.")
    else:
        print("No changes were made.")


#Delete
def delete_repository(repositoryCollection):
    """Delete one repository document from MongoDB."""
    repo_name = input("Enter the repository name to delete: ").strip()

    result = repositoryCollection.delete_one({"repo_name": repo_name})

    if result.deleted_count > 0:
        print("Repository record deleted successfully.")
    else:
        print("Repository was not found.")


#Feature 1
def popular_repositories(repositoryCollection):
    """Display the ten repositories with the highest watch counts."""
    repositories = repositoryCollection.find(
        {},
        {"_id": False, "repo_name": True, "watch_count": True}
    ).sort("watch_count", pymongo.DESCENDING).limit(10)

    repositories = list(repositories)

    if not repositories:
        print("No repository data was found.")
        return

    print("\nTop 10 Most Popular Repositories")
    print("--------------------------------")

    for number, repository in enumerate(repositories, start=1):
        repo_name = repository.get("repo_name", "Unknown")
        watch_count = repository.get("watch_count", 0)

        try:
            watch_count = int(watch_count)
        except (ValueError, TypeError):
            watch_count = 0

        print(f"{number}. {repo_name} - {watch_count} watchers")


#Feature 2
def analyze_languages(languageCollection):
    """Display the ten most common programming languages."""
    pipeline = [
        {"$unwind": "$language"},
        {
            "$group": {
                "_id": "$language.name",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    languages = list(languageCollection.aggregate(pipeline))

    if not languages:
        print("No language data was found.")
        return

    print("\nTop 10 Programming Languages")
    print("----------------------------")

    for number, language in enumerate(languages, start=1):
        language_name = language.get("_id", "Unknown")
        count = language.get("count", 0)
        print(f"{number}. {language_name} - {count} repositories")

    print(
        f"\nAnalysis is based on the first "
        f"{LANGUAGE_RECORD_LIMIT} language records."
    )


#Feature 3
def contributor_history(commitCollection):
    """Search commit history for a GitHub contributor."""
    search_name = input("Enter the contributor name: ").strip()

    if search_name == "":
        print("Contributor name cannot be blank.")
        return

    #Search the nested author.name field without requiring an exact case match
    results = list(
        commitCollection.find(
            {"author.name": {"$regex": search_name, "$options": "i"}},
            {
                "_id": False,
                "commit": True,
                "author.name": True,
                "repo_name": True,
                "subject": True
            }
        )
    )

    if not results:
        print("No matching contributor was found.")
        return

    #Group the matching commits by contributor name
    contributors = {}

    for document in results:
        author = document.get("author") or {}
        author_name = author.get("name", "Unknown")
        contributors.setdefault(author_name, []).append(document)

    for author_name in sorted(contributors):
        commits = contributors[author_name]

        print("\nContributor:", author_name)
        print("Number of commits:", len(commits))

        repositories = set()

        for commit in commits:
            repo_name = commit.get("repo_name")

            if repo_name:
                repositories.add(repo_name)

        if repositories:
            print("Repositories contributed to:")

            for repo_name in sorted(repositories):
                print("-", repo_name)


def main():
    program_running = True

    try:
        myClient, db, repositoryCollection, commitCollection, languageCollection = connectDB()
        myClient.admin.command("ping")
    except pymongo.errors.ConnectionFailure:
        print(
            "\n[ERROR] Could not connect to MongoDB. "
            "Make sure the MongoDB server is running."
        )
        return

    initialize_database(
        repositoryCollection,
        commitCollection,
        languageCollection
    )

    print()
    print(prompt)

    while program_running == True:
        main_menu()

        try:
            menu_choice = int(input("Enter your choice (1-8): "))
        except ValueError:
            print("Please enter only 1-8")
            continue

        if menu_choice == 1:
            create_repository(repositoryCollection)

        elif menu_choice == 2:
            read_repository(repositoryCollection)

        elif menu_choice == 3:
            update_repository(repositoryCollection)

        elif menu_choice == 4:
            delete_repository(repositoryCollection)

        elif menu_choice == 5:
            popular_repositories(repositoryCollection)

        elif menu_choice == 6:
            analyze_languages(languageCollection)

        elif menu_choice == 7:
            contributor_history(commitCollection)

        elif menu_choice == 8:
            print("Exiting program.")
            program_running = False

        else:
            print("Please enter only 1-8")


if __name__ == "__main__":
    main()
