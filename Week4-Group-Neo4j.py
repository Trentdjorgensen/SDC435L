#Chase Vial & Trent Jorgensen SDC435
#September 24th, 2026

import json
import zipfile

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

# CONFIGURATION
DATASET_ZIP = "GitHubArchive-Dataset.zip"

# The Languages file is very large, so only the first
# 10,000 records are used for analysis.
LANGUAGE_RECORD_LIMIT = 10000

# Neo4j connection information
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "Password1"

prompt = "Type in a number and press enter to execute the menu option."

# READ JSON OBJECTS FROM ZIP FILE
def read_json_lines(file_name, limit=None):

    records = []

    try:

        with zipfile.ZipFile(
            DATASET_ZIP,
            "r"
        ) as archive:

            path = (
                "GitHubArchive-Dataset/"
                + file_name
            )

            with archive.open(path) as file:

                for line_number, line in enumerate(file):

                    if (
                        limit is not None
                        and line_number >= limit
                    ):
                        break

                    line = line.decode(
                        "utf-8"
                    ).strip()

                    if line:
                        records.append(
                            json.loads(line)
                        )

    except FileNotFoundError:

        print(
            "\n[ERROR] GitHubArchive-Dataset.zip "
            "was not found."
        )

    except KeyError:

        print(
            "\n[ERROR] "
            + file_name
            + " was not found in the dataset ZIP."
        )

    except json.JSONDecodeError:

        print(
            "\n[ERROR] A record in "
            + file_name
            + " could not be read."
        )

    return records

# CONNECT TO NEO4J
def connectDB():

    print(
        "Connecting to local Neo4j database..."
    )

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(
            NEO4J_USERNAME,
            NEO4J_PASSWORD
        )
    )

    driver.verify_connectivity()

    print(
        "Connected to Neo4j successfully."
    )

    return driver

# CREATE DATABASE CONSTRAINTS
def create_constraints(driver):

    queries = [

        """
        CREATE CONSTRAINT repository_name_unique
        IF NOT EXISTS
        FOR (r:Repository)
        REQUIRE r.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT language_name_unique
        IF NOT EXISTS
        FOR (l:Language)
        REQUIRE l.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT contributor_name_unique
        IF NOT EXISTS
        FOR (a:Contributor)
        REQUIRE a.name IS UNIQUE
        """
    ]

    with driver.session() as session:

        for query in queries:
            session.run(query)

# CHECK IF DATA EXISTS
def repositories_exist(driver):

    query = """
        MATCH (r:Repository)
        RETURN r
        LIMIT 1
    """

    with driver.session() as session:

        result = session.run(query)

        return result.single() is not None


def commits_exist(driver):

    query = """
        MATCH (c:Commit)
        RETURN c
        LIMIT 1
    """

    with driver.session() as session:

        result = session.run(query)

        return result.single() is not None


def languages_exist(driver):

    query = """
        MATCH (l:Language)
        RETURN l
        LIMIT 1
    """

    with driver.session() as session:

        result = session.run(query)

        return result.single() is not None

# LOAD REPOSITORY DATA
def load_repository_data(driver):

    records = read_json_lines(
        "Sample_Repos.json"
    )

    query = """
        MERGE (r:Repository {
            name: $repo_name
        })

        SET r.watch_count = $watch_count
    """

    with driver.session() as session:

        for record in records:

            repo_name = record.get(
                "repo_name"
            )

            if repo_name is None:
                continue

            watch_count = record.get(
                "watch_count",
                0
            )

            try:

                watch_count = int(
                    watch_count
                )

            except (
                ValueError,
                TypeError
            ):

                watch_count = 0

            session.run(
                query,
                repo_name=str(repo_name),
                watch_count=watch_count
            )

# LOAD COMMIT DATA
def load_commit_data(driver):

    records = read_json_lines(
        "Sample_Commits.json"
    )

    query = """
        CREATE (c:Commit {
            commit: $commit,
            author_name: $author_name,
            repo_name: $repo_name,
            subject: $subject
        })

        WITH c

        OPTIONAL MATCH (
            r:Repository {
                name: $repo_name
            }
        )

        FOREACH (_ IN CASE
            WHEN r IS NOT NULL THEN [1]
            ELSE []
        END |
            CREATE (c)-[:BELONGS_TO]->(r)
        )

        WITH c

        FOREACH (_ IN CASE
            WHEN $author_name <> '' THEN [1]
            ELSE []
        END |
            MERGE (
                a:Contributor {
                    name: $author_name
                }
            )

            CREATE (a)-[:MADE]->(c)
        )
    """

    with driver.session() as session:

        for record in records:

            author = record.get(
                "author"
            ) or {}

            commit = record.get(
                "commit"
            ) or ""

            author_name = author.get(
                "name"
            ) or ""

            repo_name = record.get(
                "repo_name"
            ) or ""

            subject = record.get(
                "subject"
            ) or ""

            session.run(
                query,
                commit=str(commit),
                author_name=str(author_name),
                repo_name=str(repo_name),
                subject=str(subject)
            )

# LOAD LANGUAGE DATA
def load_language_data(driver):

    records = read_json_lines(
        "Languages.json",
        LANGUAGE_RECORD_LIMIT
    )

    # Clear the old language nodes first.
    # This makes sure old data without usage_count
    # cannot interfere with the new analysis.
    delete_query = """
        MATCH (l:Language)
        DETACH DELETE l
    """

    with driver.session() as session:
        session.run(delete_query)

    # Count language occurrences in Python first.
    language_counts = {}

    for record in records:

        languages = record.get(
            "language"
        ) or []

        for language in languages:

            if isinstance(
                language,
                dict
            ):

                language_name = language.get(
                    "name"
                )

                if language_name:

                    language_name = str(
                        language_name
                    )

                    if language_name in language_counts:

                        language_counts[
                            language_name
                        ] += 1

                    else:

                        language_counts[
                            language_name
                        ] = 1

    # Insert one node for each language
    # with its total occurrence count.
    query = """
        CREATE (l:Language {
            name: $language_name,
            usage_count: $usage_count
        })
    """

    with driver.session() as session:

        for language_name, usage_count in language_counts.items():

            session.run(
                query,
                language_name=language_name,
                usage_count=usage_count
            )

# ANALYZE PROGRAMMING LANGUAGES
def analyze_languages(driver):

    query = """
        MATCH (l:Language)

        RETURN
            l.name AS language_name,
            l.usage_count AS language_count

        ORDER BY language_count DESC

        LIMIT 10
    """

    with driver.session() as session:

        results = list(
            session.run(query)
        )

    if not results:

        print(
            "No language data was found."
        )

        return

    print(
        "\nTop 10 Programming Languages"
    )

    print(
        "----------------------------"
    )

    for number, language in enumerate(
        results,
        start=1
    ):

        print(
            str(number)
            + ". "
            + str(language["language_name"])
            + " - "
            + str(language["language_count"])
            + " records"
        )

    print(
        "\nAnalysis is based on the first "
        + str(LANGUAGE_RECORD_LIMIT)
        + " language records."
    )

# INITIALIZE DATABASE
def initialize_database(driver):

    create_constraints(driver)

    # Repository data is loaded only if it does not exist.
    if not repositories_exist(driver):
        load_repository_data(driver)

    # Commit data is loaded only if it does not exist.
    if not commits_exist(driver):
        load_commit_data(driver)

    # Language data is ALWAYS rebuilt.
    #
    # This is intentional because the language analysis
    # depends on usage counts from the first 10,000
    # records in Languages.json.
    load_language_data(driver)

# MAIN MENU
def main_menu():
    print(
        "   GITHUB ARCHIVE MENU\n"
    )
    print(prompt)
    
    print(
        "\n1. Create a repository record"
    )

    print(
        "2. Read a repository record"
    )

    print(
        "3. Update a repository record"
    )

    print(
        "4. Delete a repository record"
    )

    print(
        "5. View most popular repositories"
    )

    print(
        "6. Find top 10 programming languages"
    )

    print(
        "7. Search contributor history"
    )

    print(
        "8. Exit the program\n"
    )

# CREATE REPOSITORY
def create_repository(driver):

    repo_name = input(
        "Enter the repository name: "
    ).strip()

    if repo_name == "":

        print(
            "Repository name cannot be blank."
        )

        return

    check_query = """
        MATCH (r:Repository {
            name: $repo_name
        })

        RETURN r
        LIMIT 1
    """

    with driver.session() as session:

        result = session.run(
            check_query,
            repo_name=repo_name
        )

        if result.single() is not None:

            print(
                "A repository with that name "
                "already exists."
            )

            return

    watch_count = input(
        "Enter the watch count: "
    ).strip()

    if not watch_count.isdigit():

        print(
            "Watch count must be a number."
        )

        return

    query = """
        CREATE (r:Repository {
            name: $repo_name,
            watch_count: $watch_count
        })
    """

    with driver.session() as session:

        session.run(
            query,
            repo_name=repo_name,
            watch_count=int(watch_count)
        )

    print(
        "Repository record added successfully."
    )

# READ REPOSITORY
def read_repository(driver):

    repo_name = input(
        "Enter the repository name: "
    ).strip()

    query = """
        MATCH (r:Repository {
            name: $repo_name
        })

        RETURN
            r.name AS repo_name,
            r.watch_count AS watch_count
    """

    with driver.session() as session:

        result = session.run(
            query,
            repo_name=repo_name
        )

        repository = result.single()

    if repository is not None:

        print(
            "\nRepository Information"
        )

        print(
            "----------------------"
        )

        print(
            "Repository:",
            repository["repo_name"]
        )

        print(
            "Watch count:",
            repository["watch_count"]
        )

    else:

        print(
            "Repository was not found."
        )

# UPDATE REPOSITORY
def update_repository(driver):

    repo_name = input(
        "Enter the repository name to update: "
    ).strip()

    check_query = """
        MATCH (r:Repository {
            name: $repo_name
        })

        RETURN r
        LIMIT 1
    """

    with driver.session() as session:

        result = session.run(
            check_query,
            repo_name=repo_name
        )

        if result.single() is None:

            print(
                "Repository was not found."
            )

            return

    watch_count = input(
        "Enter the new watch count: "
    ).strip()

    if not watch_count.isdigit():

        print(
            "Watch count must be a number."
        )

        return

    query = """
        MATCH (r:Repository {
            name: $repo_name
        })

        SET r.watch_count = $watch_count
    """

    with driver.session() as session:

        session.run(
            query,
            repo_name=repo_name,
            watch_count=int(watch_count)
        )

    print(
        "Repository record updated successfully."
    )

# DELETE REPOSITORY
def delete_repository(driver):

    repo_name = input(
        "Enter the repository name to delete: "
    ).strip()

    check_query = """
        MATCH (r:Repository {
            name: $repo_name
        })

        RETURN r
        LIMIT 1
    """

    with driver.session() as session:

        result = session.run(
            check_query,
            repo_name=repo_name
        )

        if result.single() is None:

            print(
                "Repository was not found."
            )

            return

    query = """
        MATCH (r:Repository {
            name: $repo_name
        })

        DETACH DELETE r
    """

    with driver.session() as session:

        session.run(
            query,
            repo_name=repo_name
        )

    print(
        "Repository record deleted successfully."
    )

# FEATURE 1
# MOST POPULAR REPOSITORIES
def popular_repositories(driver):

    query = """
        MATCH (r:Repository)

        RETURN
            r.name AS repo_name,
            r.watch_count AS watch_count

        ORDER BY watch_count DESC

        LIMIT 10
    """

    with driver.session() as session:

        results = list(
            session.run(query)
        )

    if not results:

        print(
            "No repository data was found."
        )

        return

    print(
        "\nTop 10 Most Popular Repositories"
    )

    print(
        "--------------------------------"
    )

    for number, repository in enumerate(
        results,
        start=1
    ):

        watch_count = (
            repository["watch_count"]
            if repository["watch_count"] is not None
            else 0
        )

        print(
            str(number)
            + ". "
            + str(repository["repo_name"])
            + " - "
            + str(watch_count)
            + " watchers"
        )

# FEATURE 2
# Top 10 PROGRAMMING LANGUAGES


def analyze_languages(driver):

    query = """
        MATCH (l:Language)

        RETURN
            l.name AS language_name,
            l.usage_count AS language_count

        ORDER BY language_count DESC

        LIMIT 10
    """

    with driver.session() as session:

        results = list(
            session.run(query)
        )

    if not results:

        print(
            "No language data was found."
        )

        return

    print(
        "\nTop 10 Programming Languages"
    )

    print(
        "----------------------------"
    )

    for number, language in enumerate(
        results,
        start=1
    ):

        print(
            str(number)
            + ". "
            + str(language["language_name"])
            + " - "
            + str(language["language_count"])
            + " records"
        )

    print(
        "\nTop 10 is based on the first "
        + str(LANGUAGE_RECORD_LIMIT)
        + " language records."
    )

# FEATURE 3
# SEARCH CONTRIBUTOR HISTORY
def contributor_history(driver):

    search_name = input(
        "Enter the contributor name: "
    ).strip()

    if search_name == "":

        print(
            "Contributor name cannot be blank."
        )

        return

    query = """
        MATCH (a:Contributor)-[:MADE]->(c:Commit)

        WHERE toLower(a.name)
              CONTAINS toLower($search_name)

        OPTIONAL MATCH
            (c)-[:BELONGS_TO]->(r:Repository)

        RETURN
            a.name AS author_name,
            count(DISTINCT c) AS commit_count,
            collect(DISTINCT r.name) AS repositories

        ORDER BY author_name
    """

    with driver.session() as session:

        results = list(
            session.run(
                query,
                search_name=search_name
            )
        )

    if not results:

        print(
            "No matching contributor was found."
        )

        return

    for contributor in results:

        print(
            "\nContributor:",
            contributor["author_name"]
        )

        print(
            "Number of commits:",
            contributor["commit_count"]
        )

        repositories = [
            repository
            for repository
            in contributor["repositories"]
            if repository is not None
        ]

        if repositories:

            print(
                "Repositories contributed to:"
            )

            for repo_name in sorted(
                repositories
            ):

                print(
                    "-",
                    repo_name
                )

# MAIN PROGRAM
def main():

    program_running = True

    driver = None

    try:

        driver = connectDB()

    except ServiceUnavailable:

        print(
            "\n[ERROR] Could not connect to Neo4j."
        )

        print(
            "Make sure the Neo4j server is running."
        )

        return

    except Exception as error:

        print(
            "\n[ERROR] Could not connect to Neo4j:"
        )

        print(error)

        return

    try:

        initialize_database(driver)

        print()
       

        while program_running:

            main_menu()

            try:

                menu_choice = int(
                    input(
                        "Enter your choice (1-8): "
                    )
                )

            except ValueError:

                print(
                    "Please enter only 1-8"
                )

                continue

            if menu_choice == 1:

                create_repository(driver)

            elif menu_choice == 2:

                read_repository(driver)

            elif menu_choice == 3:

                update_repository(driver)

            elif menu_choice == 4:

                delete_repository(driver)

            elif menu_choice == 5:

                popular_repositories(driver)

            elif menu_choice == 6:

                analyze_languages(driver)

            elif menu_choice == 7:

                contributor_history(driver)

            elif menu_choice == 8:

                print(
                    "Exiting program."
                )

                program_running = False

            else:

                print(
                    "Please enter only 1-8"
                )

    finally:

        if driver is not None:
            driver.close()

# START PROGRAM
if __name__ == "__main__":
    main()



