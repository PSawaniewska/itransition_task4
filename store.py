import re
from itertools import combinations

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import yaml
from dateutil import parser

EUR_TO_USD = 1.2
STORES = [f"data/STORE{n}" for n in range(1, 6)]


def parse_price(text):
    is_eur = "EUR" in text or "€" in text
    numbers = re.findall(r"\d+(?:\.\d+)?", text)

    if "¢" in text:
        value = int(numbers[0]) + int(numbers[1]) / 100
    else:
        value = float(numbers[0])

    if is_eur:
        value = value * EUR_TO_USD
    return round(value, 2)


def parse_timestamp(text):
    cleaned = text.replace(";", " ").replace(",", " ")
    cleaned = cleaned.replace("A.M.", "AM").replace("P.M.", "PM")
    # dates with dots are day first, dates with slashes are month first
    day_first = re.search(r"\d{1,2}\.\d{1,2}\.\d{4}", cleaned) is not None
    return parser.parse(cleaned, dayfirst=day_first)


def to_author_set(text):
    return frozenset(name.strip() for name in text.split(","))


def load_orders(store_dir):
    orders = pd.read_parquet(f"{store_dir}/orders.parquet")

    orders["unit_price"] = orders["unit_price"].apply(parse_price)
    orders["paid_price"] = (orders["quantity"] * orders["unit_price"]).round(2)

    orders["timestamp"] = pd.to_datetime(orders["timestamp"].apply(parse_timestamp))
    orders["date"] = orders["timestamp"].dt.normalize()
    orders["year"] = orders["timestamp"].dt.year
    orders["month"] = orders["timestamp"].dt.month
    orders["day"] = orders["timestamp"].dt.day

    # the same order can show up twice with a different id
    same_order = ["user_id", "book_id", "quantity", "paid_price", "timestamp"]
    return orders.drop_duplicates(subset=same_order)


def load_books(store_dir):
    with open(f"{store_dir}/books.yaml", encoding="utf-8") as f:
        books = pd.DataFrame(yaml.safe_load(f))
    books.columns = [col.lstrip(":") for col in books.columns]
    books["authors"] = books["author"].apply(to_author_set)
    return books


def find_people(store_dir):
    users = pd.read_csv(f"{store_dir}/users.csv")
    users["phone"] = users["phone"].str.replace(r"\D", "", regex=True)

    # the same person changes only one field, so two rows matching on 3 of 4 fields are one person
    fields = ["name", "address", "phone", "email"]
    graph = nx.Graph()
    graph.add_nodes_from(users["id"])

    for key in combinations(fields, 3):
        for _, ids in users.groupby(list(key))["id"]:
            nx.add_path(graph, ids)

    return list(nx.connected_components(graph))


def process_store(store_dir):
    orders = load_orders(store_dir)
    books = load_books(store_dir)
    people = find_people(store_dir)

    daily_revenue = orders.groupby("date")["paid_price"].sum().round(2)
    top5_days = daily_revenue.sort_values(ascending=False).head(5)

    sold = orders.merge(
        books[["id", "authors"]].rename(columns={"id": "book_id"}),
        on="book_id",
    )
    author_sales = sold.groupby("authors")["quantity"].sum()
    top_authors = author_sales[author_sales == author_sales.max()].index

    person_of = {user_id: i for i, group in enumerate(people) for user_id in group}
    spending = orders.groupby(orders["user_id"].map(person_of))["paid_price"].sum()

    return {
        "daily_revenue": daily_revenue,
        "orders": len(orders),
        "top5_days": list(top5_days.index.strftime("%Y-%m-%d")),
        "unique_users": len(people),
        "author_sets": books["authors"].nunique(),
        "top_authors": [sorted(authors) for authors in top_authors],
        "best_buyer": sorted(people[spending.idxmax()]),
    }


if __name__ == "__main__":
    fig, axes = plt.subplots(len(STORES), 1, figsize=(12, 14), sharex=True)

    for store_dir, ax in zip(STORES, axes):
        result = process_store(store_dir)
        revenue = result["daily_revenue"]

        print(f"\n{store_dir}  ({revenue.index.min():%Y-%m-%d} - {revenue.index.max():%Y-%m-%d})")
        for key, value in result.items():
            if key != "daily_revenue":
                print(f"  {key}: {value}")

        revenue.plot(ax=ax, title=f"{store_dir} - daily revenue (USD)")

    plt.tight_layout()
    plt.show()