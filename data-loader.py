import pandas as pd
import mysql.connector
import numpy as np

def load_to_mysql():
    df = pd.read_csv("pricebook_products_clean1.csv")

    df = df.rename(columns={
        'Product Name': 'name',
        'Price': 'price',
        'Year': 'year',
        'Product URL': 'url',
        'Product Image': 'image_url',
        'Ram (GB)': 'ram',
        'Camera (MP)': 'camera',
        'Screen (inch)': 'screen_size',
        'Battery (mAh)': 'battery',
        'ID': 'id'
    })

    df = df[['id', 'name', 'price', 'year', 'url', 'image_url', 'ram', 'camera', 'screen_size', 'battery']]

    # Ganti NaN dengan None
    df = df.replace({np.nan: None})

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="smartphone_db"
    )
    cursor = conn.cursor()

    # Hapus isi tabel (jika ada data sebelumnya)
    cursor.execute("DELETE FROM smartphones")

    # Masukkan data ke tabel
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO smartphones 
            (id, name, price, year, url, image_url, ram, camera, screen_size, battery)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, tuple(row))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Data berhasil dimasukkan ke MySQL.")

if __name__ == "__main__":
    load_to_mysql()
