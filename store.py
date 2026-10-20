import re

import matplotlib.pyplot as plt
import pandas as pd
import yaml
from dateutil import parser

STORE_DIR = "data/STORE1"
EUR_TO_USD = 1.2


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


# --- orders ---

orders = pd.read_parquet(f"{STORE_DIR}/orders.parquet")

orders["unit_price_usd"] = orders["unit_price"].apply(parse_price)
orders["paid_price"] = (orders["quantity"] * orders["unit_price_usd"]).round(2)

orders["timestamp"] = pd.to_datetime(orders["timestamp"].apply(parse_timestamp))
orders["date"] = orders["timestamp"].dt.date
orders["year"] = orders["timestamp"].dt.year
orders["month"] = orders["timestamp"].dt.month
orders["day"] = orders["timestamp"].dt.day


# --- checks ---

# bad dates usually end up in the future or way too early
print("earliest:", orders["timestamp"].min())
print("latest:", orders["timestamp"].max())
print("in the future:", (orders["timestamp"] > pd.Timestamp.now()).sum())

print("duplicate order ids:", orders["id"].duplicated().sum())
same_order = ["user_id", "book_id", "quantity", "paid_price", "timestamp"]
print("duplicate orders (different id):", orders.duplicated(subset=same_order).sum())
print("non-positive quantity:", (orders["quantity"] <= 0).sum())


# --- daily revenue ---

daily_revenue = orders.groupby("date")["paid_price"].sum().round(2)
top5_days = daily_revenue.sort_values(ascending=False).head(5)

print("days:", len(daily_revenue))
print(top5_days)


# --- books ---

with open(f"{STORE_DIR}/books.yaml", encoding="utf-8") as f:
    books = pd.DataFrame(yaml.safe_load(f))
books.columns = [col.lstrip(":") for col in books.columns]

books["authors"] = books["author"].apply(to_author_set)

print(books[["author", "authors"]].head())
print("unique author sets:", books["authors"].nunique())

# check for very short names, e.g. "Jr." split off as a separate author
all_names = pd.Series([name for s in books["authors"] for name in s])
print(all_names[all_names.str.len() <= 5].value_counts())


# --- chart ---

# quick visual check for anomalies
daily_revenue.plot(figsize=(12, 4), title="STORE1 - daily revenue (USD)")
plt.ylabel("USD")
plt.tight_layout()
# plt.show()