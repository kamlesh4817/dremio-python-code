# For generating 1 billion rows , 500 columns, the recommended approach would be execute this script on a EC2 machine with enough storage capacity
# For 1 billion rows, set numFile = 10000 to generate 10000 files with 100000 rows with 500 columns
# For 1 billion rows, you will see 10000 output files
# Next, upload all the .csv files to a storage medium like S3 , promote the files so Dremio can recognize this table and the columns
import random

numFile=1
rowSize=100000
columnSize=500
sep=","
flag=["true", "false"]
# more data type
type=["int", "float", "varchar", "boolean"]  
# generate column type
colType = ["int", "varchar"]
for i in range(2, columnSize):
    colType.append(type[random.randint(0, len(type)-1)])

print ("Generate {} files with {} rows and {} columns".format(numFile, rowSize, columnSize))
for k in range(numFile):
    fname=str(k)+"_"+str(rowSize)+"_"+str(columnSize)+".csv"
    print("\nGenerating data for file="+fname)
    f = open(fname, "w")
    row = ""
    # generate header row
    for i in range(columnSize):
        if i == columnSize - 1:
            row += "c" + str(i)
            break
        else:
            row += "c" + str(i) + sep 
    f.write(row + "\n")

    # generate row data
    for i in range(rowSize):
        if i % 10000 == 0:
            print("....Generate total {} rows".format(rowSize))
        row = ""
        for j in range(columnSize):
            if colType[j] == "int":
                row += str(i + k * rowSize)
            elif colType[j] == "float":
                row += str(j * random.randint(0, i)) 
            elif colType[j] == "varchar":
                row += "abc" + str(i + k * rowSize)
            elif colType[j] == "boolean":
                row += flag[random.randint(0, 1)] 
            if j != columnSize - 1:
                row += sep
        f.write(row+"\n")

    f.close()
