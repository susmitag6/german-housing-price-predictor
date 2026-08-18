import pandas as pd

from database import get_db_engine


engine = get_db_engine()


df = pd.read_sql(
    "SELECT * FROM listings ORDER BY id;",
    engine
)


print(df.to_string(index=False))
