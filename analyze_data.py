import pandas as pd, warnings, sys
warnings.filterwarnings('ignore')

df = pd.read_csv('data/full/studies.csv')

lines = []
lines.append("TOTAL STUDIES: " + str(len(df)))
lines.append("COLUMNS: " + str(list(df.columns)))

lines.append("\n--- STUDY_TYPE ---")
vc = df['study_type'].fillna('(missing)').str.split('\n').str[0].value_counts()
for k, v in vc.head(20).items():
    lines.append("  " + str(v) + "  " + str(k)[:80])

lines.append("\n--- DATA_ACCESS_TYPE ---")
vc2 = df['data_access_type'].fillna('(missing)').str.split('\n').str[0].value_counts()
for k, v in vc2.items():
    lines.append("  " + str(v) + "  " + str(k)[:80])

lines.append("\n--- KIND_OF_DATA ---")
vc3 = df['kind_of_data'].fillna('(missing)').str.split('\n').str[0].value_counts()
for k, v in vc3.items():
    lines.append("  " + str(v) + "  " + str(k)[:80])

lines.append("\n--- GEOGRAPHIC_COVERAGE ---")
vc4 = df['geographic_coverage'].fillna('(missing)').str.split('\n').str[0].str.strip().value_counts()
for k, v in vc4.items():
    lines.append("  " + str(v) + "  " + str(k)[:80])

lines.append("\n--- TOP 10 MOST VIEWED ---")
top = df[['title', 'year', 'views']].sort_values('views', ascending=False).head(10)
for _, r in top.iterrows():
    v = str(int(r['views'])) if pd.notna(r['views']) else "0"
    try:
        y = str(int(float(str(r['year'])))) if pd.notna(r['year']) else "N/A"
    except Exception:
        y = str(r['year'])
    t = str(r['title'])[:65]
    lines.append("  " + v.rjust(12) + "  " + y + "  " + t)

lines.append("\n--- YEAR DISTRIBUTION ---")
yd = df['year'].value_counts().sort_index()
for yr, cnt in yd.items():
    lines.append("  " + str(yr) + ": " + str(cnt))

lines.append("\n--- UNIVERSE top 10 ---")
universes = df['universe'].dropna().str.split('\n').str[0].str.strip().value_counts()
for k, v in universes.head(10).items():
    lines.append("  " + str(v) + "  " + str(k)[:80])

lines.append("\n--- VIEWS stats ---")
vs = df['views'].describe()
for k, v in vs.items():
    lines.append("  " + str(k) + ": " + str(int(v)))

lines.append("\n--- ORGANIZATION counts ---")
for k, v in df['organization'].value_counts().items():
    lines.append("  " + str(v) + "  " + str(k)[:80])

result = "\n".join(lines)
sys.stdout.write(result + "\n")
