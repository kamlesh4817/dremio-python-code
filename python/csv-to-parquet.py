import pandas as pd

try:
    df = pd.read_csv('C:\\Temp\\csv\\100 Sales Records.csv')
    df.to_parquet('C:\\Temp\\csv\\100 Sales Records.parquet')
    print('csv to parquet conversion operation successful')
except:
    print('csv to parquet conversion operation failed')    