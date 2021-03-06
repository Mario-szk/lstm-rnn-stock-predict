#基于lstm-rnn的雅虎股票价格预测
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
#获取雅虎股票接口
from pandas_datareader import data as pdr
import datetime
import fix_yahoo_finance as yf
#国内股票包
import tushare as ts
#配置matplotlib画图的符号
plt.rcParams['font.sans-serif'] = ['SimHei']  #显示中文
plt.rcParams['axes.unicode_minus']=False #用来正常显示坐标中的负号
def get_home_data(num,start,end):
    try:
        data = tsts.get_hist_data(num,start = start,end = end)
        data = pd.DataFrame(data)
        data = np.array(data['close'])
        data = data[::1]
        print('股票数据获取完成！')
        return data
    except Exception:
        print('股票获取失败！')
# data = get_home_data('601318','2015-07-23','2018-08-25')
def get_national_data(name):
    try:
        yf.pdr_override()
    #获取阿里bab实时股票数据
        finance = pdr.get_data_yahoo(name,start = datetime.datetime(2014,11,11),end = datetime.datetime(2018,8,24))  
        data = np.array(finance['Close']) #获取收盘价的数据
        data = data[::1] #获取这列的所有数据
        print('股票数据获取完成！！')
        return data
    except Exception:
        print('股票数据获取失败！！')
data = get_national_data('BABA')
#以折线图展示导入的数据
fig =plt.figure()
#fig.add_subplot(1,2,1)
#plt.plot(data)
#plt.show()
normalize_data=(data-np.mean(data))/np.std(data)  #对数据进行标准化 （数据 - 均值）/（方差）
normalize_data=normalize_data[:,np.newaxis]       #增加数据的维度，使数据维度相同

#———————————————————形成训练集—————————————————————
#设置rnn网络的常量
time_step=20     #时间步 ，rnn每迭代20次，就向前推进一步
rnn_unit=10       # hidden layer units
batch_size=60     # 每一批训练多少个样例
input_size=1      # 输入层数维度
output_size=1     # 输出层数维度
lr=0.0006         # 学习率
train_x,train_y=[],[]   #训练集
for i in range(len(normalize_data)-time_step-1):
    x=normalize_data[i:i+time_step]
    y=normalize_data[i+1:i+time_step+1]
    train_x.append(x.tolist())
    train_y.append(y.tolist()) 
# print(len(normalize_data))
# print(train_x)
# print(train_y)

#———————————————————定义神经网络变量—————————————————————

X=tf.placeholder(tf.float32, [None,time_step,input_size])    #每批次输入网络的tensor
Y=tf.placeholder(tf.float32, [None,time_step,output_size])   # 每批次tensor对应的标签
#输入层、输出层的权重和偏置
weights={
         'in':tf.Variable(tf.random_normal([input_size,rnn_unit])),
         'out':tf.Variable(tf.random_normal([rnn_unit,1]))
         }
biases={
        'in':tf.Variable(tf.constant(0.1,shape=[rnn_unit,])),
        'out':tf.Variable(tf.constant(0.1,shape=[1,]))
        }

#———————————————————定义lstm网络—————————————————————
def lstm(batch):      #参数：输入网络批次数目
    w_in=weights['in']
    b_in=biases['in']
    input=tf.reshape(X,[-1,input_size])  #需要将tensor转为2维进行计算，计算后的结果作为 隐藏层的输入
    input_rnn=tf.matmul(input,w_in)+b_in
    input_rnn=tf.reshape(input_rnn,[-1,time_step,rnn_unit])   #将tensor转为3维，作为 lstm cell的输入
    cell=tf.nn.rnn_cell.BasicLSTMCell(rnn_unit)
    init_state=cell.zero_state(batch,dtype=tf.float32)
    output_rnn,final_states=tf.nn.dynamic_rnn(cell, input_rnn,initial_state=init_state, dtype=tf.float32)
    output=tf.reshape(output_rnn,[-1,rnn_unit])  #作为输出层的输入
    w_out=weights['out']
    b_out=biases['out']
    pred=tf.matmul(output,w_out)+b_out
    return pred,final_states

#———————————————————对模型进行训练—————————————————————
def train_lstm():
    global batch_size
    with tf.variable_scope("sec_lstm"):
        pred,_=lstm(batch_size)
    #定义损失函数
    loss=tf.reduce_mean(tf.square(tf.reshape(pred,[-1])-tf.reshape(Y, [-1])))
    train_op=tf.train.AdamOptimizer(lr).minimize(loss)
    saver=tf.train.Saver(tf.global_variables())
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        loss_list = [] #收集损失值
        for i in range(201): #模型训练的次数，We can increase the number of iterations to gain better result.
            step=0
            start=0
            end=start+batch_size
            while(end<len(train_x)):
                _,loss_=sess.run([train_op,loss],feed_dict={X:train_x[start:end],Y:train_y[start:end]})
                start+=batch_size
                end=start+batch_size
                #每训练10次保存一次参数
                if step%10==0:
                    print("Number of iterations:",i," loss:",loss_) #输出训练次数，输出损失值
                    print("model_save",saver.save(sess,'C:/Users/lidongming1/Desktop/tensorflow_demo/tensorflow_rnn/model_save1/modle.ckpt')) #第二个参数是保存的地址，可以修改为自己本地的保存地址
                    #I run the code in windows 10,so use  'model_save1\\modle.ckpt'
                    #if you run it in Linux,please use  'model_save1/modle.ckpt'
                    loss_list.append(loss_)
                step+=1
        print("The train has finished")
        print(len(loss_list))
        sns.set_style(style = 'whitegrid') #详细参数看seaborn的API  http://seaborn.pydata.org/api.html
        #设置字体
        sns.set_context(context = 'poster',font_scale = 1)
        plt.plot(np.arange(0,len(loss_list)),loss_list,'+-',color = 'g')
        plt.title('Loss trend')
        plt.ylabel('Loss')
train_lstm() #对模型进行训练

#———————————————————预测模型—————————————————————
def prediction():
    with tf.variable_scope("sec_lstm",reuse=True):
        pred,_=lstm(1)    #预测时只输入[1,time_step,input_size]的测试数据
    saver=tf.train.Saver(tf.global_variables())
    with tf.Session() as sess:
        #参数恢复
        saver.restore(sess, 'C:/Users/lidongming1/Desktop/tensorflow_demo/tensorflow_rnn/model_save1/modle.ckpt') #第二个参数是保存的地址，可以修改为自己本地的保存地址
        #I run the code in windows 10,so use  'model_save1\\modle.ckpt'
        #if you run it in Linux,please use  'model_save1/modle.ckpt'
        
        #取训练集最后一行为测试样本。shape = [1,time_step,input_size]
        prev_seq=train_x[-1]
        predict=[]
        #得到之后的100个预测结果
        for i in range(100):  #预测100个数值
            next_seq=sess.run(pred,feed_dict={X:[prev_seq]})
            predict.append(next_seq[-1])
            #每次得到最后一个时间步的预测结果，与之前的数据加在一起，形成新的测试数据
            prev_seq=np.vstack((prev_seq[1:],next_seq[-1]))
        #以折线图展示结果
        plt.figure(figsize = (6,6)) #图像大小为8*8英寸
        #设置背景风格
        sns.set_style(style = 'whitegrid') #详细参数看seaborn的API  http://seaborn.pydata.org/api.html
        #设置字体
        sns.set_context(context = 'poster',font_scale = 1)
        plt.title('lstm_rnn_stock_prediction')
        plt.plot(list(range(len(normalize_data))), normalize_data, color='b',label = 'raw data') #这是原来股票的价格走势，用蓝色曲线表示
        plt.plot(list(range(len(normalize_data), len(normalize_data) + len(predict))), predict, color='r',label = 'predict trend') #预测未来的价格走势用红色表示
        plt.legend(loc = 'best')
        plt.xlabel('stock_trend')
        plt.xticks([])#去掉X轴刻度
        plt.yticks([])
        plt.show()
#fig.add_subplot(1,2,2)       
prediction() 
