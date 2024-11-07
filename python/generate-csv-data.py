import random

numFile=1
rowSize=100000
columnSize=500
sep=","
type=["int", "float", "varchar", "boolean"]
# generate column type
colType = []
for i in range(columnSize):
    colType.append(type[random.randint(0,3)])

for k in range(numFile):
    fname=str(k)+"_"+str(rowSize)+"_"+str(columnSize)+".csv"
    print("File="+fname)
    f = open(fname, "w")
    row = ""
    for i in range(columnSize):
        if i == columnSize - 1:
            row += "c" + str(i)
            break
        else:
            row += "c" + str(i) + sep 

    f.write(row + "\n")

    for i in range(rowSize):
        row = ""
        for j in range(columnSize):
            if colType[j] == "int":
                row += str(j)
            elif colType[j] == "float":
                row += str(j) 
            elif colType[j] == "varchar":
                row += "abc"
            elif colType[j] == "boolean":
                row += "true"
            if j != columnSize - 1:
                row += sep
        f.write(row+"\n")

    f.close()
