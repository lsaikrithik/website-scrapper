import requests
from bs4 import BeautifulSoup
import argparse
import sys
import json
import csv
import os
import hashlib
from datetime import datetime

CACHE_FILE = "./cache.txt"

def load_site(url):
    try:
        response = requests.get(url=url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        all_entries = soup.find_all(name="h3", class_="title")
        descriptions = soup.find_all(name="p")
        return all_entries, descriptions
    except requests.exceptions.RequestException as e:
        sys.exit(f"Failed to load the site: {e}")

def sort_entries(entries, descriptions, sort_by="rank"):
    movies = []
    for rank, (entry, desc) in enumerate(zip(entries[::-1], descriptions[::-1]), start=1):
        title = entry.get_text().strip()
        description = desc.get_text().strip()
        movie = {"rank": rank, "title": title, "description": description}
        movies.append(movie)
    
    if sort_by == "title":
        movies.sort(key=lambda x: x["title"])
    elif sort_by == "rank":
        movies.sort(key=lambda x: x["rank"])

    return movies

def save_file(movies, file_path, file_format="txt"):
    try:
        if file_format == "txt":
            with open(file=file_path, mode="w", encoding="ISO-8859-1") as f:
                for movie in movies:
                    f.write(f"{movie['rank']}) {movie['title']}\nDescription: {movie['description']}\n\n")
        elif file_format == "json":
            with open(file=file_path, mode="w", encoding="utf-8") as f:
                json.dump(movies, f, ensure_ascii=False, indent=4)
        elif file_format == "csv":
            with open(file=file_path, mode="w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["rank", "title", "description"])
                writer.writeheader()
                writer.writerows(movies)
        print(f"List saved to {file_path}")
    except IOError as e:
        sys.exit(f"Failed to save the file: {e}")

def display_list(movies):
    for movie in movies:
        print(f"{movie['rank']}) {movie['title']}")
        print(f"Description: {movie['description']}\n")

def check_for_updates(url):
    try:
        response = requests.get(url=url)
        response.raise_for_status()
        content_hash = hashlib.md5(response.content).hexdigest()
        
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as cache:
                cached_hash = cache.read()
            if cached_hash == content_hash:
                print("No updates found.")
                return False
            else:
                with open(CACHE_FILE, "w") as cache:
                    cache.write(content_hash)
                print("Updates found. Fetching new data.")
                return True
        else:
            with open(CACHE_FILE, "w") as cache:
                cache.write(content_hash)
            return True

    except requests.exceptions.RequestException as e:
        sys.exit(f"Failed to check for updates: {e}")

def main():
    parser = argparse.ArgumentParser(description="Fetch and sort top 100 movies.")
    parser.add_argument("-u", "--url", type=str, default="https://www.empireonline.com/movies/features/best-movies-2/", help="URL of the movie list.")
    parser.add_argument("-o", "--output", type=str, default="./movies.txt", help="Output file path.")
    parser.add_argument("-f", "--filter", type=str, help="Filter movies by a keyword.")
    parser.add_argument("-s", "--sort", type=str, choices=["rank", "title"], default="rank", help="Sort by rank or title.")
    parser.add_argument("-d", "--display", action="store_true", help="Display the sorted list in the console.")
    parser.add_argument("--format", type=str, choices=["txt", "json", "csv"], default="txt", help="Output file format.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode.")
    parser.add_argument("--check-updates", action="store_true", help="Check if the list has been updated.")
    args = parser.parse_args()

    if args.check_updates and not check_for_updates(args.url):
        sys.exit("The list has not been updated. Exiting.")

    entries, descriptions = load_site(args.url)

    if args.verbose:
        print(f"Loaded {len(entries)} entries from {args.url}")

    if args.filter:
        entries = [entry for entry in entries if args.filter.lower() in entry.get_text().lower()]

    sorted_list = sort_entries(entries, descriptions, sort_by=args.sort)

    if args.display:
        display_list(sorted_list)

    save_file(sorted_list, args.output, file_format=args.format)

if __name__ == "__main__":
    main()
