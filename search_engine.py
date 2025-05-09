# import mysql.connector
from sqlalchemy import create_engine
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Load model embedding
model = SentenceTransformer("all-MiniLM-L6-v2")


def get_connection():
    return create_engine("mysql+mysqlconnector://root:@localhost/smartphone_db")
    # return mysql.connector.connect(
    #     host="localhost",
    #     user="root",
    #     password="",
    #     database="smartphones_db"
    # )


def load_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM smartphones", conn)
    # conn.close()

    # Preprocessing
    df = df[df['name'].notna()].copy()
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df['ram'] = pd.to_numeric(df['ram'], errors='coerce').fillna(0)
    df['camera'] = pd.to_numeric(df['camera'], errors='coerce').fillna(0)
    df['screen_size'] = pd.to_numeric(df['screen_size'], errors='coerce').fillna(0)
    df['battery'] = pd.to_numeric(df['battery'], errors='coerce').fillna(0)

    df['name_embedding'] = df['name'].apply(lambda x: model.encode(str(x)))
    return df


# Load awal data
data_df = load_data()


def extract_filters_from_query(query):
    query = query.lower()
    filters = {}

    # Harga
    if "murah" in query:
        filters["price_max"] = 3000000
    if match := re.search(r"di bawah (\d+)", query):
        filters["price_max"] = int(match.group(1)) * 1000

    # RAM
    if "ram besar" in query or "ram gede" in query or "ram tinggi" in query:
        filters["ram_min"] = 6

    # Kamera
    if "kamera bagus" in query or "kamera jernih" in query:
        filters["camera_min"] = 50

    # Baterai
    if "baterai besar" in query or "baterai tahan lama" in query:
        filters["battery_min"] = 5000

    # Tahun
    if match := re.search(r"tahun (\d{4})", query):
        filters["year"] = int(match.group(1))
    elif match := re.search(r"\b(20[1-2][0-9]|2030)\b", query):
        filters["year"] = int(match.group(0))

    return filters


def search_smartphones(query="", price_min=None, price_max=None, ram_min=None, camera_min=None, battery_min=None, screen_min=None,year=None):
    df = data_df.copy()

    # Deteksi dari natural query
    extracted = extract_filters_from_query(query)
    price_min = price_min or extracted.get("price_min")
    price_max = price_max or extracted.get("price_max")
    ram_min = ram_min or extracted.get("ram_min")
    camera_min = camera_min or extracted.get("camera_min")
    battery_min = battery_min or extracted.get("battery_min")
    screen_min = screen_min or extracted.get("screen_min")
    year = year or extracted.get("year")

    # Filter numerik
    if price_min is not None:
        df = df[df['price'] >= price_min]
    if price_max is not None:
        df = df[df['price'] <= price_max]
    if ram_min is not None:
        df = df[df['ram'] >= ram_min]
    if camera_min is not None:
        df = df[df['camera'] >= camera_min]
    if battery_min is not None:
        df = df[df['battery'] >= battery_min]
    if screen_min is not None:
        df = df[df['screen'] >= screen_min]
    if year is not None:
        df = df[df['year'] == year]

    # Jika tanpa query teks
    if query.strip() == "":
        return df.drop(columns=["name_embedding"]).head(20).to_dict(orient="records")

    # Similarity
    query_vec = model.encode(query)
    df['similarity'] = df['name_embedding'].apply(lambda x: cosine_similarity([query_vec], [x])[0][0])
    df = df.sort_values(by='similarity', ascending=False)

    return df.drop(columns=["name_embedding"]).head(20).to_dict(orient="records")


def get_filter_options():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM smartphones", conn)
    conn.close()

    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['ram'] = pd.to_numeric(df['ram'], errors='coerce')
    df['camera'] = pd.to_numeric(df['camera'], errors='coerce')
    df['screen_size'] = pd.to_numeric(df['screen_size'], errors='coerce')
    df['battery'] = pd.to_numeric(df['battery'], errors='coerce')

    return {
        "ram_options": sorted(df['ram'].dropna().unique().tolist()),
        "camera_options": sorted(df['camera'].dropna().unique().tolist()),
        "screen_size_options": sorted(df['screen_size'].dropna().unique().tolist()),
        "battery_options": sorted(df['battery'].dropna().unique().tolist()),
        "year_options": sorted(df['year'].dropna().unique().tolist()) if "year" in df.columns else [],
        "price_min": float(df['price'].min()) if df['price'].notna().any() else 0,
        "price_max": float(df['price'].max()) if df['price'].notna().any() else 0
    }
