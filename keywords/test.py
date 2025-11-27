import json

# Load data
with open("keywords/all_articles_keywords.json", "r", encoding="utf-8") as f:
    data1 = json.load(f)

with open("keywords/all_articles_keywords_NEW.json", "r", encoding="utf-8") as f:
    data2 = json.load(f)

# Extract titles
titles1 = set(item.get("title", "") for item in data1)  # use set for fast lookup
titles2 = [item.get("title", "") for item in data2]

# Find titles in data2 not in data1
new_titles = [title for title in titles2 if title not in titles1]

# Find titles in data1 not in data2 (optional)
removed_titles = [title for title in titles1 if title not in titles2]

# Print results
print("Total titles in file 1:", len(titles1))
print("Total titles in file 2:", len(titles2))
print("Titles only in new file:", len(new_titles))
print("Titles only in old file:", len(removed_titles))

# print the titles themselves
if new_titles:
    print("\nTitles in new file not in old file:")
    for t in new_titles:
        print("  ", t)

if removed_titles:
    print("\nTitles in old file not in new file:")
    for t in removed_titles:
        print("  ", t)

