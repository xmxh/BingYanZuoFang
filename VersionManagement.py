#!/usr/bin/python
#encoding=utf-8
import sys
import os
import difflib
import getopt
import shutil
from shutil import copy
import datetime

#diff函数用于判断两个文件内容是否有改动，是，返回1；否，返回0
def diff(f1path,f2path):
    F1 = open(f1path)
    F2 = open(f2path)
    OutPath = HubPath + 'diff\\' + f1path.split('\\')[-1]  #输出对比结果为html到diff文件夹下的该文件夹内
    Context1 = F1.readlines()
    Context2 = F2.readlines()
    # 快速判断两个文件是否不同
    if len(Context1) != len(Context2): #长度不同，文件一定不同
        # 生成html方便查看
        d = difflib.HtmlDiff()
        html = d.make_file(Context1, Context2)
        if not os.path.isdir(OutPath):
            os.mkdirs(OutPath)
        # 记录此次与上次的具体不同，并保存为一个递增编号的文件
        version = len([x for x in os.listdir(os.path.dirname(OutPath)) if os.path.isfile(x)])
        Out = open(OutPath + 'diff_%d.html' % version, 'w')
        Out.write(html)
        return 1
    else: #长度相同，在判断是否每行都相同
        for (l1, l2) in zip(Context1, Context2):
            if l1 != l2:
                # 生成html方便查看
                d = difflib.HtmlDiff()
                html = d.make_file(Context1, Context2)
                if not os.path.isdir(OutPath):
                    os.mkdirs(OutPath)
                # 记录此次与上次的具体不同，并保存为一个递增编号的文件
                version = len([x for x in os.listdir(os.path.dirname(OutPath)) if os.path.isfile(x)])
                Out = open(OutPath + 'diff_%d.html' % version, 'w')
                Out.write(html)
                return 1
        return 0


#create函数对应于create要求，用以创建一个目录，并初始化一个svn文件夹
def create(dirname):
    path = os.getcwd()
    parent_path = os.path.dirname(path) #判断当前目录是否在一个版本仓库下，若是，创建失败，返回0
    tmp = parent_path.split('\\')
    if 'svn' in tmp:
        print("当前目录已在一个版本仓库下！")
        return 0
    os.mkdirs(path + dirname + '\svn')
    os.mkdirs(path + dirname + '\diff') #初始化一个diff文件夹，用以保存各个文件的版本的同上次的具体变化
    return 1

#status函数对应于status命令
def status():
    global HubPath
    files = os.walk(HubPath)[2]
    for file in files:
        if file not in statusRecord['?']: #首先判断file是否被管理，未被管理者不予输出状态
            if os.path.exists(HubPath + 'svn\\' + file):  # 在svn中存在该文件夹
                FilePath = HubPath + file
                CommittedPath = HubPath + 'svn\\' + file + '\\' + file
                Modified = diff(FilePath, CommittedPath)
                if Modified:
                    statusRecord['M'].append(file)
            else: #如果svn中不存在该文件，说明为新增文件
                statusRecord['+'].append(file)
    print(statusRecord)

#add函数对应于add命令,讲一个文件或目录加入管理范围,其实就是未受收托管状态中删除
def add(name):
    if name in statusRecord['?']:
        statusRecord['?'].remove(name)

#delete函数对应于delete命令,讲一个文件或目录纳出管理范围,force为真，代表删除物理文件
def delete(name,force = False):
    if name not in statusRecord['?']:
        statusRecord['?'].append(name)
    if (force):
        os.remove(HubPath + name)
        statusRecord['D'].append(name)

#mv函数对应于mv命令,移动文件夹,讲仓库里的文件（夹）移动到指定目录下，targetpath需输入相对路径
def mv(name,targetpath):
    shutil.move(name, './'+targetpath)
    statusRecord['MV'].append(name + ' ./' + name+'-> ./' + targetpath + name)#记录文件的移动情况

# commit函数对应于commit命令,提交修改，记录提交修改的文件以及内容，同时保存日志，提交成功，返回一个递增的版本号，
#文件未变化，提交失败，提示 “ no modification ”
def commit(filename, describe="A new commit"):
    global HubPath
    FilePath = HubPath + filename
    CommittedFile = HubPath + 'svn\\' + filename + '\\' + filename
    ThisFileDirInSvn = HubPath + 'svn\\' + filename
    # 如果该路径不存在，说明是第一次commit，要在svn文件夹创建一个以该文件名命名的文件夹，存放后续所有该文件版本
    if not os.path.exists(CommittedFile):

        os.mkdir(ThisFileDirInSvn)
        copy(FilePath, ThisFileDirInSvn)
        statusRecord['+'].append(filename) #更新状态记录，filename文件为新加：‘+’
    else:
        Modified = diff(FilePath, CommittedFile)
        #如果文件被修改了，对原来svn文件夹内该文件的最新版本重命名，将放入该最新版本
        #重命名规则为“文件名+所有版本总数”
        if(Modified):
            Version = len([x for x in os.listdir(os.path.dirname(ThisFileDirInSvn)) if os.path.isfile(x)])
            NewFileName = filename + '_%d'%Version
            os.rename(CommittedFile, os.path.join(ThisFileDirInSvn, NewFileName))
            copy(FilePath, ThisFileDirInSvn)
            statusRecord['M'].append(filename)  # 记录文件的修改情况

        else:
            print('no modification')
    logs = open(HubPath + 'log', 'a') #以追加的方式记录修改日志
    logs.write(describe + '\n')



#log函数查看所有版本信息以及提交日志，如果有具体文件名，只显示特定文件的提交信息
def log(filename=""):
    logs = open(HubPath + 'log')
    #如果未指定文件名，输出所有日志记录
    if not len(filename):
        print (logs.readlines())
    #指定文件名，只输入对应该文件名的日志记录
    else:
        while(1):
            line = logs.readline()
            if not line:
                break
            if line.find(filename) != -1:
                print (line)

#revert恢复当前文件到历史版本中
def revert(version="", filename=""):
    #不设置版本号和文件名，将所有文件恢复到上次提交版本
    if not len(version) and not len(filename):
        #直接删除所有文件
        filelist = os.listdir(HubPath)
        for f in filelist:
            filepath = os.path.join(HubPath, f)
            if os.path.isfile(filepath):
                os.remove(filepath)
        #然后将svn文件夹中所有文件拷贝过来
        CommitedFile = os.listdir(HubPath + 'svn')
        for f in CommitedFile:
            #取出最新被更改的文件，即为最近一次提交的文件
            filepath = os.path.join(HubPath + 'svn', f)
            l = os.listdir(filepath)
            l.sort(key=lambda fn: os.path.getmtime(filepath + fn) if not os.path.isdir(filepath + fn) else 0)
            #d = datetime.datetime.fromtimestamp(os.path.getmtime(filepath + l[-1]))
            #print('最后改动的文件是' + l[-1] + "，时间：" + d.strftime("%Y年%m月%d日 %H时%M分%S秒"))
            copy(os.path.join(filepath, l[-1]), HubPath)

    # 不设置版本号，设置文件名，将特定文件恢复到上次提交版本
    if not len(version) and len(filename):
        #先删除该文件
        filepath = os.path.join(HubPath, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
        #将特定文件的上次提交版本copy回来
        copy(os.path.join(filepath, filename), HubPath)

    # 设置版本号，不设置文件名，将所有文件恢复到特定提交版本
    if len(version) and not len(filename):
        # 直接删除所有文件
        filelist = os.listdir(HubPath)
        for f in filelist:
            filepath = os.path.join(HubPath, f)
            if os.path.isfile(filepath):
                os.remove(filepath)
        # 然后将svn文件夹中所有该版本文件拷贝过来
        CommitedFile = os.listdir(HubPath + 'svn')
        for f in CommitedFile:
            filepath = os.path.join(HubPath + 'svn', f)
            FileNames = os.listdir(filepath)
            for fn in FileNames:
                if '_%s' % version in fn:
                    copy(os.path.join(filepath, fn), HubPath)
                    os.rename(HubPath + fn, HubPath + f)

    # 设置版本号和文件名，将特定文件恢复到特定提交版本
    if len(version) and len(filename):
        # 先删除该文件
        filepath = os.path.join(HubPath, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
        # 将特定文件的特定版本copy回来
        FileNames = os.listdir(filepath)
        for fn in FileNames:
            if '_%s'%version in fn:
                copy(os.path.join(filepath, fn), HubPath)
                os.rename(HubPath + fn, HubPath + filename)


if __name__ == '__main__':

    global HubPath #仓库路径
    global statusRecord #初始化一个文件修改记录表
    statusRecord = {'M':[],'+':[],'D':[],'MV':[],'?':[]}
    while(1):
        CommodLine = input().split()
        Commend = CommodLine[1]
        if Commend == "create": #svn create [目录名]
            create(CommodLine[2])
            HubPath = os.getcwd() + '\\' + CommodLine[2] + '\\'
        elif Commend == "status":
            status()
        elif Commend == "add": # svn add [文件名/目录名]
            add(CommodLine[2])
        elif Commend == "delete": # svn delete [文件名] (--force)
            if len(CommodLine) == 4: #有force命令
                delete(CommodLine[2], True)
            else:
                delete(CommodLine[2])
        elif Commend == "mv": # svn mv [文件名/目录名] [目标目录]
            # mv函数对应于mv命令,移动文件夹,讲仓库里的文件（夹）移动到指定目录下，targetpath需输入相对路径
             mv(CommodLine[2], CommodLine[3])
        elif Commend == "commit": # svn commit [文件名/目录名] (-m '提交日志')
            if len(CommodLine)== 5:
                commit(CommodLine[2], CommodLine[4])
            else:
                commit(CommodLine[2])
        elif Commend == "git": #svn git log (文件名)
            # log函数查看所有版本信息以及提交日志，如果有具体文件名，只显示特定文件的提交信息
            if len(CommodLine) == 4: #有文件名
                log(CommodLine[3])
            else:
                log()
        elif Commend == "revert": #svn revert (版本号) (-f 文件名/目录名)
            # revert恢复当前文件到历史版本中
            if len(CommodLine) == 2: #不设置版本号，不设置文件名
                revert()
            elif len(CommodLine) == 3: #只设置版本号，不设置文件名
                revert(CommodLine[2])
            elif len(CommodLine) == 4: #不设置版本号，只设置文件名
                revert("", CommodLine[4])
            elif len(CommodLine) == 5: #设置版本号，设置文件名
                revert(CommodLine[2], CommodLine[4])























