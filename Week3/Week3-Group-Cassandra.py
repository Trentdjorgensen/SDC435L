#Horace Vial & Trent Jorgensen
#09/16/2026
#GitHub Archive Cassandra Project
#Python application that stores and analyzes GitHub Archive data using Cassandra

import json
import zipfile
from cassandra.cluster import Cluster, NoHostAvailable


#Name of the dataset ZIP file
DATASET_ZIP = "GitHubArchive-Dataset.zip"

#The Languages file is very large, so only a portion is used for analysis.
LANGUAGE_RECORD_LIMIT = 10000

prompt = "Type in a number and press enter to execute the menu option."


#Read JSON objects from a file stored inside the dataset ZIP
def read_json_lines(file_name, limit=None):
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
        print("\n[ERROR] " + file_name + " was not found in the dataset ZIP.")
    except json.JSONDecodeError:
        print("\n[ERROR] A record in " + file_name + " could not be read.")

    return records


#Make text safe to place inside a CQL string
def clean_value(value):
    if value is None:
        return ""

    return str(value).replace("'", "''")


#Connect to the local Cassandra database
def connectDB():
    print("Connecting to local Cassandra database...")

    cluster = Cluster()
    session = cluster.connect()

    #Create the GitHubArchive keyspace
    query = """
        CREATE KEYSPACE IF NOT EXISTS GitHubArchive WITH
        replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
    """
    session.execute(query)

    #Enter the GitHubArchive keyspace
    query = "USE GitHubArchive;"
    session.execute(query)

    #Create the Repositories table
    query = """
        CREATE TABLE IF NOT EXISTS Repositories(
        repo_name text PRIMARY KEY,
        watch_count int
        );
    """
    session.execute(query)

    #Create the Commits table
    query = """
        CREATE TABLE IF NOT EXISTS Commits(
        id uuid PRIMARY KEY,
        commit text,
        author_name text,
        repo_name text,
        subject text
        );
    """
    session.execute(query)

    #Create the Languages table
    query = """
        CREATE TABLE IF NOT EXISTS Languages(
        id uuid PRIMARY KEY,
        language_name text
        );
    """
    session.execute(query)

    return cluster, session


#Check if a table already contains data
def table_has_data(session, table_name):
    query = "SELECT * FROM " + table_name + " LIMIT 1;"
    results = session.execute(query)

    if results.one() is None:
        return False
    else:
        return True


#Load repository data into Cassandra
def load_repository_data(session):
    if table_has_data(session, "Repositories"):
        return

    print("Loading repository data...")

    records = read_json_lines("Sample_Repos.json")

    for record in records:
        repo_name = clean_value(record.get("repo_name"))
        watch_count = record.get("watch_count", 0)

        try:
            watch_count = int(watch_count)
        except (ValueError, TypeError):
            watch_count = 0

        #Insert repository data
        query = """
            INSERT INTO Repositories(repo_name, watch_count)
            VALUES('""" + repo_name + """', """ + str(watch_count) + """);
        """
        session.execute(query)

    if records:
        print("Repository data loaded successfully.")


#Load commit data into Cassandra
def load_commit_data(session):
    if table_has_data(session, "Commits"):
        return

    print("Loading commit data...")

    records = read_json_lines("Sample_Commits.json")

    for record in records:
        author = record.get("author") or {}

        commit = clean_value(record.get("commit"))
        author_name = clean_value(author.get("name"))
        repo_name = clean_value(record.get("repo_name"))
        subject = clean_value(record.get("subject"))

        #Insert commit data and generate the id using uuid()
        query = """
            INSERT INTO Commits(id, commit, author_name, repo_name, subject)
            VALUES(uuid(), '""" + commit + """', '""" + author_name + """',
            '""" + repo_name + """', '""" + subject + """');
        """
        session.execute(query)

    if records:
        print("Commit data loaded successfully.")


#Load language data into Cassandra
def load_language_data(session):
    if table_has_data(session, "Languages"):
        return

    print("Loading language data...")

    records = read_json_lines("Languages.json", LANGUAGE_RECORD_LIMIT)

    for record in records:
        languages = record.get("language") or []

        for language in languages:
            if isinstance(language, dict):
                language_name = clean_value(language.get("name"))

                if language_name != "":
                    #Insert language data and generate the id using uuid()
                    query = """
                        INSERT INTO Languages(id, language_name)
                        VALUES(uuid(), '""" + language_name + """');
                    """
                    session.execute(query)

    if records:
        print("Language data loaded successfully.")


#Load all GitHub Archive data
def initialize_database(session):
    load_repository_data(session)
    load_commit_data(session)
    load_language_data(session)


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
def create_repository(session):
    repo_name = input("Enter the repository name: ").strip()

    if repo_name == "":
        print("Repository name cannot be blank.")
        return

    repo_name = clean_value(repo_name)

    #Check if the repository already exists
    query = """
        SELECT * FROM Repositories
        WHERE repo_name = '""" + repo_name + """';
    """
    results = session.execute(query)

    if results.one() is not None:
        print("A repository with that name already exists.")
        return

    watch_count = input("Enter the watch count: ").strip()

    if not watch_count.isdigit():
        print("Watch count must be a number.")
        return

    #Insert the new repository
    query = """
        INSERT INTO Repositories(repo_name, watch_count)
        VALUES('""" + repo_name + """', """ + watch_count + """);
    """
    session.execute(query)

    print("Repository record added successfully.")


#Read
def read_repository(session):
    repo_name = clean_value(input("Enter the repository name: ").strip())

    #Select the requested repository
    query = """
        SELECT * FROM Repositories
        WHERE repo_name = '""" + repo_name + """';
    """
    results = session.execute(query)
    repository = results.one()

    if repository is not None:
        print("\nRepository Information")
        print("----------------------")
        print(repository)
    else:
        print("Repository was not found.")


#Update
def update_repository(session):
    repo_name = clean_value(
        input("Enter the repository name to update: ").strip()
    )

    #Check if the repository exists
    query = """
        SELECT * FROM Repositories
        WHERE repo_name = '""" + repo_name + """';
    """
    results = session.execute(query)
    repository = results.one()

    if repository is None:
        print("Repository was not found.")
        return

    watch_count = input("Enter the new watch count: ").strip()

    if not watch_count.isdigit():
        print("Watch count must be a number.")
        return

    #Update the repository watch count
    query = """
        UPDATE Repositories
        SET watch_count = """ + watch_count + """
        WHERE repo_name = '""" + repo_name + """';
    """
    session.execute(query)

    print("Repository record updated successfully.")


#Delete
def delete_repository(session):
    repo_name = clean_value(
        input("Enter the repository name to delete: ").strip()
    )

    #Check if the repository exists
    query = """
        SELECT * FROM Repositories
        WHERE repo_name = '""" + repo_name + """';
    """
    results = session.execute(query)

    if results.one() is None:
        print("Repository was not found.")
        return

    #Delete the repository
    query = """
        DELETE FROM Repositories
        WHERE repo_name = '""" + repo_name + """';
    """
    session.execute(query)

    print("Repository record deleted successfully.")


#Feature 1
def popular_repositories(session):
    #Select all repository data
    query = "SELECT * FROM Repositories;"
    results = session.execute(query)

    repositories = list(results)

    if not repositories:
        print("No repository data was found.")
        return

    #Sort the repositories by watch count
    repositories.sort(
        key=lambda repository: repository.watch_count or 0,
        reverse=True
    )

    repositories = repositories[:10]

    print("\nTop 10 Most Popular Repositories")
    print("--------------------------------")

    for number, repository in enumerate(repositories, start=1):
        print(
            str(number) + ". " + repository.repo_name +
            " - " + str(repository.watch_count) + " watchers"
        )


#Feature 2
def analyze_languages(session):
    #Select all language data
    query = "SELECT * FROM Languages;"
    results = session.execute(query)

    rows = list(results)

    if not rows:
        print("No language data was found.")
        return

    language_counts = {}

    #Count each programming language
    for row in rows:
        language_name = row.language_name

        if language_name in language_counts:
            language_counts[language_name] += 1
        else:
            language_counts[language_name] = 1

    languages = sorted(
        language_counts.items(),
        key=lambda item: item[1],
        reverse=True
    )

    languages = languages[:10]

    print("\nTop 10 Programming Languages")
    print("----------------------------")

    for number, language in enumerate(languages, start=1):
        print(
            str(number) + ". " + language[0] +
            " - " + str(language[1]) + " repositories"
        )

    print(
        "\nAnalysis is based on the first " +
        str(LANGUAGE_RECORD_LIMIT) +
        " language records."
    )


#Feature 3
def contributor_history(session):
    search_name = input("Enter the contributor name: ").strip()

    if search_name == "":
        print("Contributor name cannot be blank.")
        return

    #Select all commit data
    query = "SELECT * FROM Commits;"
    results = session.execute(query)

    matching_commits = []

    #Find contributor names that match the search
    for row in results:
        author_name = row.author_name

        if author_name is not None:
            if search_name.lower() in author_name.lower():
                matching_commits.append(row)

    if not matching_commits:
        print("No matching contributor was found.")
        return

    contributors = {}

    #Group commits by contributor
    for row in matching_commits:
        author_name = row.author_name

        if author_name not in contributors:
            contributors[author_name] = []

        contributors[author_name].append(row)

    for author_name in sorted(contributors):
        commits = contributors[author_name]

        print("\nContributor:", author_name)
        print("Number of commits:", len(commits))

        repositories = set()

        for commit in commits:
            if commit.repo_name is not None:
                repositories.add(commit.repo_name)

        if repositories:
            print("Repositories contributed to:")

            for repo_name in sorted(repositories):
                print("-", repo_name)


def main():
    program_running = True
    cluster = None

    try:
        cluster, session = connectDB()
    except NoHostAvailable:
        print(
            "\n[ERROR] Could not connect to Cassandra. "
            "Make sure the Cassandra server is running."
        )
        return

    try:
        initialize_database(session)

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
                create_repository(session)

            elif menu_choice == 2:
                read_repository(session)

            elif menu_choice == 3:
                update_repository(session)

            elif menu_choice == 4:
                delete_repository(session)

            elif menu_choice == 5:
                popular_repositories(session)

            elif menu_choice == 6:
                analyze_languages(session)

            elif menu_choice == 7:
                contributor_history(session)

            elif menu_choice == 8:
                print("Exiting program.")
                program_running = False

            else:
                print("Please enter only 1-8")

    finally:
        if cluster is not None:
            cluster.shutdown()


if __name__ == "__main__":
    main()
