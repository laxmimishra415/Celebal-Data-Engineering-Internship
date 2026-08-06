"""
Executes every query in sql/analysis_queries.sql against ecommerce.db
and prints a sample of results for each -- used to verify Part 3 works
end-to-end. Also writes full output to sql/query_results.txt.
"""

import os
import re
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "..", "ecommerce.db")
SQL_PATH = os.path.join(BASE_DIR, "..", "sql", "analysis_queries.sql")
OUT_PATH = os.path.join(BASE_DIR, "..", "sql", "query_results.txt")


def split_queries(sql_text):
    """Split the .sql file into (comment_title, query) pairs on numbered comments."""
    blocks = re.split(r"\n-- (\d+)\. (.+)\n", sql_text)
    # blocks[0] is preamble; then triplets of (num, title, query)
    queries = []
    for i in range(1, len(blocks), 3):
        num, title, query = blocks[i], blocks[i + 1], blocks[i + 2]
        query = query.strip().rstrip(";")
        if query:
            queries.append((num, title.strip(), query))
    return queries


def main():
    with open(SQL_PATH) as f:
        sql_text = f.read()

    queries = split_queries(sql_text)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    lines = []
    for num, title, query in queries:
        header = f"\n{'='*70}\nQuery {num}: {title}\n{'='*70}"
        print(header)
        lines.append(header)
        try:
            cur.execute(query)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchmany(5)
            lines.append(" | ".join(cols))
            print(" | ".join(cols))
            for row in rows:
                row_str = " | ".join(str(v) for v in row)
                lines.append(row_str)
                print(row_str)
            cur.execute(query)
            total = len(cur.fetchall())
            summary = f"... ({total} total rows)"
            lines.append(summary)
            print(summary)
        except Exception as e:
            error_msg = f"ERROR: {e}"
            lines.append(error_msg)
            print(error_msg)

    conn.close()
    with open(OUT_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"\n\nFull results saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
