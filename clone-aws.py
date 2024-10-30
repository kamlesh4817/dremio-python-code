import subprocess
import os 

for i in range(1,10000):
    os.system("aws s3 cp s3://datasets.dremio.com/10kFiles100kRowsEach/0_0_0.parquet s3://datasets.dremio.com/10kFiles100kRowsEach/0_0_{}.parquet".format(str(i)))
