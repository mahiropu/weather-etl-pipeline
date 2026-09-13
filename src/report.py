import pandas as pd

from src import db
from src.utils import load_config, resolve


def split_queries(sql_text):
    queries = []
    for chunk in sql_text.split(";"):
        chunk = chunk.strip()
        if chunk:
            queries.append(chunk)
    return queries


def main():
    config = load_config()
    connection = db.connect(config)

    with open(resolve("sql/analytics_queries.sql")) as f:
        queries = split_queries(f.read())

    for i, query in enumerate(queries, start=1):
        df = pd.read_sql_query(query, connection)

        print(f"\n=== Query {i} ===")
        if df.empty:
            print("(no rows)")
        else:
            print(df.to_string(index=False))

    connection.close()


if __name__ == "__main__":
    main()
