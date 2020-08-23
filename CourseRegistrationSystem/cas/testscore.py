import random

with open('score.txt','w',encoding='utf-8') as f:
    for i in range(1,43):
        if i<10:
            sno = "1827120%d "%i
        else:
            sno = "182712%d "%i
        f.write(sno+str(random.randint(80,100))+" "+str(random.randint(30,100))+"\n")
