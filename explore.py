import pandas as pd
import yaml

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

STORE_DIR = "data/STORE1"

orders = pd.read_parquet(f"{STORE_DIR}/orders.parquet")
users = pd.read_csv(f"{STORE_DIR}/users.csv")
with open(f"{STORE_DIR}/books.yaml", encoding="utf-8") as f:
    books = yaml.safe_load(f)


# --- first look ---

print("=== ORDERS ===", len(orders))
print(orders.head(10))
print(orders.dtypes)

print("\n=== USERS ===", len(users))
print(users.head(10))
print(users.dtypes)

print("\n=== BOOKS ===", type(books), len(books))
print(books[:3])

# price and timestamp are text in many different formats
# phone numbers are written differently
# book keys look like Ruby (":id", ":title")


# --- prices ---

currency = orders["unit_price"].str.replace(r"[\d.,\s]", "", regex=True)
print(currency.value_counts(dropna=False))
print("with comma:", orders["unit_price"].str.contains(",", na=False).sum())

print(orders.loc[orders["unit_price"].str.contains("¢"), "unit_price"].head(15))

# only $ and €, nothing missing, no commas
# cents format: "29€50¢" means 29.50 EUR


# --- timestamps ---

patterns = orders["timestamp"].str.replace(r"\d", "9", regex=True)
print(patterns.value_counts(dropna=False).to_string())
print("missing:", orders["timestamp"].isna().sum())

# a lot of formats, but nothing missing

ts = orders["timestamp"]

slash = ts.str.extract(r"(\d{2})/(\d{2})/(\d{2})").dropna().astype(int)
print("format 99/99/99, max of each part:\n", slash.max())

dots = ts.str.extract(r"(\d{1,2})\.(\d{1,2})\.(\d{4})").dropna().astype(int)
print("format 99.99.9999, max of each part:\n", dots.max())

# 99/99/99 is month/day/year, 99.99.9999 is day.month.year
# so I can't use one dayfirst setting for the whole column

# --- users ---

print(users.isna().sum())
print("duplicate user ids:", users["id"].duplicated().sum())

phone_patterns = users["phone"].str.replace(r"\d", "9", regex=True)
print(phone_patterns.value_counts().to_string())

print("emails with capitals:", (users["email"] != users["email"].str.lower()).sum())
print("same email used twice:", users["email"].str.lower().duplicated().sum())