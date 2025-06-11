from sqlalchemy import create_engine
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Multilingual semantic model
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

def get_connection():
    return create_engine("mysql+mysqlconnector://root:@localhost/smartphone_db")

def load_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM smartphones", conn)

    df = df[df['name'].notna()].copy()
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df['ram'] = pd.to_numeric(df['ram'], errors='coerce').fillna(0)
    df['camera'] = pd.to_numeric(df['camera'], errors='coerce').fillna(0)
    df['screen_size'] = pd.to_numeric(df['screen_size'], errors='coerce').fillna(0)
    df['battery'] = pd.to_numeric(df['battery'], errors='coerce').fillna(0)

    df['name_embedding'] = df['name'].apply(lambda x: model.encode(str(x)))
    return df

data_df = load_data()

def extract_filters_from_query(query):
    query = query.lower()
    filters = {}

    # Harga
    if "murah" in query or "budget" in query or "terjangkau" in query or "low end" in query:
        filters["price_max"] = 3000000
    if match := re.search(r"(di bawah|maksimal|max|kurang dari|<)\s*rp?\s?(\d+)", query):
        filters["price_max"] = int(match.group(2)) * 1000
    if match := re.search(r"(di atas|minimal|lebih dari|>)\s*rp?\s?(\d+)", query):
        filters["price_min"] = int(match.group(2)) * 1000

    # RAM
    if match := re.search(r"ram\s*(\d+)\s*gb", query):
        filters["ram_min"] = int(match.group(1))
    elif match := re.search(r"(\d+)\s*gb\s*ram", query):
        filters["ram_min"] = int(match.group(1))
    elif any(kw in query for kw in ["ram besar", "ram tinggi", "ram bagus", "ram cepat"]):
        filters["ram_min"] = 6

    # Kamera
    if match := re.search(r"kamera\s*(\d+)\s*mp", query):
        filters["camera_min"] = int(match.group(1))
    elif match := re.search(r"(\d+)\s*mp\s*kamera", query):
        filters["camera_min"] = int(match.group(1))
    elif any(kw in query for kw in ["kamera bagus", "kamera jernih", "kamera tajam", "kamera bening"]):
        filters["camera_min"] = 50

    # Baterai
    if match := re.search(r"baterai\s*(\d+)", query):
        filters["battery_min"] = int(match.group(1))
    elif any(kw in query for kw in ["baterai besar", "baterai tahan lama", "baterai awet", "daya tahan tinggi"]):
        filters["battery_min"] = 5000

    # Layar
    if match := re.search(r"layar\s*(\d+(\.\d+)?)", query):
        filters["screen_min"] = float(match.group(1))
    elif any(kw in query for kw in ["layar besar", "layar lebar", "layar luas", "display besar"]):
        filters["screen_min"] = 6.5

    # Tahun Rilis
    if match := re.search(r"tahun\s*(\d{4})", query):
        filters["year"] = int(match.group(1))
    elif match := re.search(r"\b(20[1-2][0-9]|2030)\b", query):
        filters["year"] = int(match.group(0))
    
    return filters

def search_smartphones(query="", price_min=None, price_max=None, ram_min=None,
                       camera_min=None, battery_min=None, screen_min=None,
                       year=None, sort_by="similarity", order="desc",
                       similarity_threshold=0.3):
    df = data_df.copy()
    extracted = extract_filters_from_query(query)

    price_min = price_min or extracted.get("price_min")
    price_max = price_max or extracted.get("price_max")
    ram_min = ram_min or extracted.get("ram_min")
    camera_min = camera_min or extracted.get("camera_min")
    battery_min = battery_min or extracted.get("battery_min")
    screen_min = screen_min or extracted.get("screen_min")
    year = year or extracted.get("year")

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
        df = df[df['screen_size'] >= screen_min]
    if year is not None:
        df = df[df['year'] == year]

    if query.strip():
        query_vec = model.encode(query)
        df['similarity'] = df['name_embedding'].apply(
            lambda x: cosine_similarity([query_vec], [x])[0][0]
        )
        df = df[df['similarity'] >= similarity_threshold]
    else:
        df['similarity'] = 1.0

    valid_sort_columns = ['price', 'ram', 'camera', 'battery', 'screen_size', 'year', 'similarity']
    if sort_by not in valid_sort_columns:
        sort_by = 'similarity'

    ascending = (order == "asc")
    df = df.sort_values(by=sort_by, ascending=ascending)

    return df.drop(columns=["name_embedding"]).to_dict(orient="records")

def get_filter_options():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM smartphones", conn)

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
