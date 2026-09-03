#Horace Vial
#09/03/2026
#Week 1 GitHub Archive Redis Project
#Application that stores and analyzes GitHub Archive data using Redis

import json
import zipfile
import redis


#Connect to the local Redis database
r = redis.StrictRedis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True
)


#Name of the dataset ZIP file
DATASET_ZIP = "GitHubArchive-Dataset.zip"

#The Languages file is very large, so only a portion is used for the
#language analysis during development.
LANGUAGE_RECORD_LIMIT = 10000


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


def load_repository_data():
    """Load repository data into Redis if it has not already been loaded."""
    if r.exists("repos_loaded"):
        return

    print("Loading repository data...")

    records = read_json_lines("Sample_Repos.json")

    for record in records:
        repo_name = record.get("repo_name")
        watch_count = record.get("watch_count", "0")

        if repo_name:
            key = "repo:" + repo_name

            r.hset(
                key,
                mapping={
                    "repo_name": repo_name,
                    "watch_count": watch_count
                }
            )

            try:
                r.zadd("repo_popularity", {repo_name: int(watch_count)})
            except ValueError:
                r.zadd("repo_popularity", {repo_name: 0})

    if records:
        r.set("repos_loaded", "1")


def load_commit_data():
    """Load commit data into Redis if it has not already been loaded."""
    if r.exists("commits_loaded"):
        return

    print("Loading commit data...")

    records = read_json_lines("Sample_Commits.json")

    for record in records:
        commit_id = record.get("commit")

        if not commit_id:
            continue

        author = record.get("author") or {}
        author_name = author.get("name", "Unknown")
        repo_name = record.get("repo_name", "")
        subject = record.get("subject", "")
        message = record.get("message", "")

        key = "commit:" + commit_id

        r.hset(
            key,
            mapping={
                "commit": commit_id,
                "author": author_name,
                "repo_name": repo_name,
                "subject": subject,
                "message": message
            }
        )

        r.sadd("authors", author_name)
        r.sadd("author:" + author_name + ":commits", commit_id)

        if repo_name:
            r.sadd("repo:" + repo_name + ":commits", commit_id)

    if records:
        r.set("commits_loaded", "1")


def load_language_data():
    """Load language counts into Redis if they have not already been loaded."""
    if r.exists("languages_loaded"):
        return

    print("Loading language data...")

    records = read_json_lines(
        "Languages.json",
        LANGUAGE_RECORD_LIMIT
    )

    for record in records:
        languages = record.get("language", [])

        for language in languages:
            name = language.get("name")

            if name:
                r.zincrby("language_popularity", 1, name)

    if records:
        r.set("languages_loaded", "1")


def initialize_database():
    """Load the GitHub Archive data needed by the application."""
    load_repository_data()
    load_commit_data()
    load_language_data()


def display_menu():
    """Print the available options to the console."""
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
def create_repository():
    """Create a new repository record in Redis."""
    repo_name = input("Enter the repository name: ").strip()

    if repo_name == "":
        print("Repository name cannot be blank.")
        return

    key = "repo:" + repo_name

    if r.exists(key):
        print("A repository with that name already exists.")
        return

    watch_count = input("Enter the watch count: ").strip()

    if not watch_count.isdigit():
        print("Watch count must be a number.")
        return

    r.hset(
        key,
        mapping={
            "repo_name": repo_name,
            "watch_count": watch_count
        }
    )

    r.zadd("repo_popularity", {repo_name: int(watch_count)})

    print("Repository record added successfully.")


#Read
def read_repository():
    """Retrieve and display a repository record."""
    repo_name = input("Enter the repository name: ").strip()
    key = "repo:" + repo_name

    if r.exists(key):
        repository = r.hgetall(key)

        print("\nRepository Information")
        print("----------------------")
        print("Repository:", repository.get("repo_name"))
        print("Watch Count:", repository.get("watch_count"))
    else:
        print("Repository was not found.")


#Update
def update_repository():
    """Update the watch count of an existing repository."""
    repo_name = input("Enter the repository name to update: ").strip()
    key = "repo:" + repo_name

    if not r.exists(key):
        print("Repository was not found.")
        return

    watch_count = input("Enter the new watch count: ").strip()

    if not watch_count.isdigit():
        print("Watch count must be a number.")
        return

    r.hset(key, "watch_count", watch_count)
    r.zadd("repo_popularity", {repo_name: int(watch_count)})

    print("Repository record updated successfully.")


#Delete
def delete_repository():
    """Delete an existing repository record."""
    repo_name = input("Enter the repository name to delete: ").strip()
    key = "repo:" + repo_name

    if r.exists(key):
        r.delete(key)
        r.zrem("repo_popularity", repo_name)
        print("Repository record deleted successfully.")
    else:
        print("Repository was not found.")


#Feature 1
def popular_repositories():
    """Display the ten repositories with the highest watch counts."""
    repositories = r.zrevrange(
        "repo_popularity",
        0,
        9,
        withscores=True
    )

    if not repositories:
        print("No repository data was found.")
        return

    print("\nTop 10 Most Popular Repositories")
    print("--------------------------------")

    for number, repository in enumerate(repositories, start=1):
        repo_name, watch_count = repository
        print(f"{number}. {repo_name} - {int(watch_count)} watchers")


#Feature 2
def analyze_languages():
    """Display the ten most common programming languages."""
    languages = r.zrevrange(
        "language_popularity",
        0,
        9,
        withscores=True
    )

    if not languages:
        print("No language data was found.")
        return

    print("\nTop 10 Programming Languages")
    print("----------------------------")

    for number, language in enumerate(languages, start=1):
        language_name, count = language
        print(f"{number}. {language_name} - {int(count)} repositories")

    print(
        f"\nAnalysis is based on the first "
        f"{LANGUAGE_RECORD_LIMIT} language records."
    )


#Feature 3
def contributor_history():
    """Search commit history for a GitHub contributor."""
    search_name = input("Enter the contributor name: ").strip().lower()

    if search_name == "":
        print("Contributor name cannot be blank.")
        return

    matching_authors = []

    for author in r.smembers("authors"):
        if search_name in author.lower():
            matching_authors.append(author)

    if not matching_authors:
        print("No matching contributor was found.")
        return

    for author in sorted(matching_authors):
        commits = r.smembers("author:" + author + ":commits")

        print("\nContributor:", author)
        print("Number of commits:", len(commits))

        repositories = set()

        for commit_id in commits:
            repo_name = r.hget("commit:" + commit_id, "repo_name")

            if repo_name:
                repositories.add(repo_name)

        if repositories:
            print("Repositories contributed to:")

            for repo_name in sorted(repositories):
                print("-", repo_name)


def main():
    try:
        r.ping()
    except redis.exceptions.ConnectionError:
        print(
            "\n[ERROR] Could not connect to Redis. "
            "Make sure the Redis server is running."
        )
        return

    initialize_database()

    is_running = True

    while is_running:
        display_menu()

        choice = input("Enter your choice (1-8): ").strip()

        if choice == "1":
            create_repository()

        elif choice == "2":
            read_repository()

        elif choice == "3":
            update_repository()

        elif choice == "4":
            delete_repository()

        elif choice == "5":
            popular_repositories()

        elif choice == "6":
            analyze_languages()

        elif choice == "7":
            contributor_history()

        elif choice == "8":
            print("\nExiting the program. Bye!")
            is_running = False

        else:
            print(
                "\n[ERROR] Invalid option. "
                "Please enter a number between 1 and 8."
            )


if __name__ == "__main__":
    main()
