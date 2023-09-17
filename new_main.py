import tkinter as tk
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageTk
import random
import math as m
#备注：复杂字母输入方式：S=sh;C=ch;z=zh;O=ong;c=ts;R=dzh;K=kh;'=shala-ralash;T=th
#初始化部分,,,目前面临一个竖排无法对齐的问题，可能需要后续的offset设定，再加一列数据
coordinates_f=open("character_reference/coordinates.txt","r")
coo_x=list()#四个坐标从左往右规定了两类字母的左右边界
coo_y=list()#每行先是一个字母，然后4个坐标规定了2个字母的上下边界：1_y_0,2_y_0,1_y_1,2_y_1
is_first_line=1
for line in coordinates_f:
    line=line.strip('\n')
    items=line.split(',')
    proc_items=list()
    is_first_item=1
    for item in items:#要进行处理，把表示数字的字符串变成int
        if is_first_item:
            is_first_item=0
            if is_first_line:
                item=eval(item)#妈的，还得单独调整，数组混合不同数据类型就是个错误，以后别这样了
            pass
        else:
            item=eval(item)
        proc_items.append(item)
    if is_first_line:
        is_first_line=0
        coo_x=proc_items
    else:
        coo_y.append(proc_items)
char_num=len(coo_y)

canvas_dx=512
canvas_dy=512
show_canvas=np.ones((canvas_dy,canvas_dx,3),dtype=np.uint8)*255
cv2.imwrite("canvas.png",show_canvas)

ref_img=cv2.imread('character_reference/refs_calibrate1.png')
#裁剪
char_pics_1=list()
char_pics_2=list()
for index in range(char_num):
    print(coo_y[index][0])
    x0,x1,x2,x3=coo_x
    y0,y2,y1,y3=coo_y[index][1:]
    extract_1=ref_img[y0:y1,x0:x1]
    extract_2=ref_img[y2:y3,x2:x3]
    char_pics_1.append(extract_1)
    char_pics_2.append(extract_2)
    #cv2.imwrite('tmp/'+coo_y[index][0]+'1.png',extract_1)
    #cv2.imwrite('tmp/'+coo_y[index][0]+'2.png',extract_2)
    
#函数定义区
def white_bg_merge(graph,adding,x,y):
    #首先将2者都转为负片
    graph=255-graph
    adding=255-adding
    graph=graph.astype(np.uint16)
    cv2.imwrite('tmp_pointer.png',adding)
    try:
        graph[y:y+adding.shape[0],x:x+adding.shape[1]]=graph[y:y+adding.shape[0],x:x+adding.shape[1]]+adding
    except:
        print('unable to comply')
    ret,graph[:,:,0]=cv2.threshold(graph[:,:,0], 255, 255, cv2.THRESH_TRUNC)
    ret,graph[:,:,1]=cv2.threshold(graph[:,:,1], 255, 255, cv2.THRESH_TRUNC)
    ret,graph[:,:,2]=cv2.threshold(graph[:,:,2], 255, 255, cv2.THRESH_TRUNC)
    graph=graph.astype(np.uint8)
    graph=255-graph#变回原片
    return graph
def put_next_char_on_canvas(graph,adding,cursor_x,cursor_y,offset):#cursor的位置是上一个字符打印之后，那个字符的左下角坐标
    #首先要判断当前位置还能不能放下字符，选择是否换行
    dy=adding.shape[0]
    if cursor_y+dy>=graph.shape[0]:
        #换行！
        cursor_y=10
        cursor_x=cursor_x-adding.shape[1]-10
    #最后一步打印的时候再把offset放上来，避免污染cursor的含义
    graph=white_bg_merge(graph,adding,cursor_x-offset,cursor_y)
    #更新cursor
    cursor_y=cursor_y+adding.shape[0]
    return graph,cursor_x,cursor_y
#界面的程序
#root = tk.Tk()#第一次运行用这个，之后都用下面那一行Toplevel这样就不会报错
root = tk.Toplevel()
root.title('瓦肯语打字输出图片')
#菜单
what = tk.IntVar(value=1)#字体选择的状态变量
menuType = tk.Menu(root, tearoff=0)
def drawCharType1():
    what.set(1)
menuType.add_command(label='瓦肯语传统字符标识', command=drawCharType1)
def drawCharType2():
    what.set(2)
menuType.add_command(label='瓦肯语标准打印体', command=drawCharType2)
root.config(menu=menuType)#显示菜单

#键盘监听函数,此处也是主函数！一切反馈皆来源于此
cursor_x=canvas_dx-(coo_x[3]-coo_x[2])-5#初始化光标位置
cursor_y=10
def keyboard_response(event):
    global show_canvas
    global char_pics_1,char_pics_2
    global cursor_x,cursor_y
    print("event.char =", event.char)
    #print("event.keycode =", event.keycode)
    #找到对应的图片
    target=event.char
    for index in range(char_num):
        if target==coo_y[index][0]:
            if what.get()==1:#字母手写符号
                char_img=char_pics_1[index]
            elif what.get()==2:
                char_img=char_pics_2[index]
            show_canvas,cursor_x,cursor_y=put_next_char_on_canvas(show_canvas,char_img,cursor_x,cursor_y,0)
            cv2.imwrite("canvas.png",show_canvas)
            new_graph_PIL = Image.fromarray(cv2.cvtColor(show_canvas, cv2.COLOR_BGR2RGB))#先转隔壁PIL
            struct_img = ImageTk.PhotoImage(image = new_graph_PIL)#再转专门的tk格式
            theLabel.configure(image = struct_img)#然后这两个才能给更新Label里的图片
            theLabel.image=struct_img#更新显示图片
    return 0
            
    
root.bind("<Key>",keyboard_response)
#增加背景图片
photo = tk.PhotoImage(file="canvas.png")
theLabel = tk.Label(root,
                    text="",#内容
                    justify=tk.LEFT,#对齐方式
                    image=photo,#加入图片
                    compound = tk.CENTER,#关键:设置为背景图片
                    font=("华文行楷",20),#字体和字号
                    fg = "white")#前景色
theLabel.pack()


tk.mainloop()