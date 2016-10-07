#!/usr/bin/python
#encoding=utf-8
import sys
import os
import difflib
import getopt
import shutil
from shutil import copy
from collections import defaultdict
import datetime

#加载全局状态变化表
def InitStatusRecord():
    if os.path.exists(os.getcwd() + os.sep + 'StatusRecord.txt'):
        sR = defaultdict(list)
        f = open(os.getcwd() + os.sep + 'StatusRecord.txt')
        lines = f.readlines()
        f.close()
        for line in lines:
            piece = line.strip().split(',')
            if len(piece[0]):
                sR[piece[0]].extend(piece[1:-1])
    else:
        sR = {'M': [], '+': [], 'D': [], 'MV': [], '?': []}
    return sR


# 保存全局状态变化表
def SaveStatusRecord():
    f = open(os.getcwd() + os.sep + 'StatusRecord.txt', 'w')
    for key in statusRecord.keys():
        f.write(key + ',')
        for value in statusRecord[key]:
            f.write(value + ',')
        f.write('\n')
    f.close()

#刷新全局状态表,key为最近一次更新的状态记录，要删除其他状态，一个文件只对应一种状态
def refresh(key, file):
    for k in statusRecord.keys():
        if k != key:
            if file in statusRecord[k]:
                statusRecord[k].remove(file)
'''
# Backup4Status函数每次都备份住程序结束运行时仓库下的所有文件

def Backup4Status():

    #如果存在一个bak版本，删除该版本，并更新为最新版本
    if os.path.exists(HubPath + 'bak'):
        shutil.rmtree(HubPath + 'bak')
    os.makedirs(HubPath + 'bak')
    for file in os.listdir(HubPath):
        if os.path.isfile(HubPath + file):
            copy(HubPath + file, HubPath + 'bak')
'''

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
            os.makedirs(OutPath)
        # 记录此次与上次的具体不同，并保存为一个递增编号的文件
        version = len([x for x in os.listdir(OutPath) if os.path.isfile(OutPath + os.sep + x)])
        Out = open(OutPath + os.sep + 'diff_%d.html' % version, 'w')
        Out.write(html)
        return 1
    else: #长度相同，在判断是否每行都相同
        for (l1, l2) in zip(Context1, Context2):
            if l1 != l2:
                # 生成html方便查看
                d = difflib.HtmlDiff()
                html = d.make_file(Context1, Context2)
                if not os.path.isdir(OutPath):
                    os.makedirs(OutPath)
                # 记录此次与上次的具体不同，并保存为一个递增编号的文件
                version = len([x for x in os.listdir(os.path.dirname(OutPath)) if os.path.isfile(x)])
                Out = open(OutPath + 'diff_%d.html' % version, 'w')
                Out.write(html)
                return 1
        return 0


#create函数对应于create要求，用以创建一个目录，并初始化一个svn文件夹
def create(dirname):
    path = os.getcwd()
    os.makedirs(path + os.sep + dirname + '\svn')
    os.makedirs(path + os.sep + dirname + '\diff') #初始化一个diff文件夹，用以保存各个文件的版本的同上次的具体变化
    return 1

#status函数对应于status命令
def status():
    global HubPath
    # 加载的信息并不能保证最新，还需要检查更新操作
    # 统计所有记录在册的文件，判断仓库中是否有新的文件不在记录中，则将其加入‘？’
    RecordedFiles = []
    for key in statusRecord.keys():
        RecordedFiles.extend(statusRecord[key])
    for file in os.listdir(HubPath):  # 取出仓库下所有的文件名
        if os.path.isfile(HubPath + file) and file not in RecordedFiles:
            statusRecord['?'].append(file)
    files = []
    commitedfiles = []
    for file in os.listdir(HubPath): #取出仓库下所有的文件名
        if os.path.isfile(HubPath + file):
            files.append(file)
    for file in os.listdir(HubPath + 'svn'):  # 取出svn下所有的文件名
        commitedfiles.append(file)
    #将仓库下的文件名和svn中文件名对比，就可以发现新增和删除的文件
    #print (files)
    #print(commitedfiles)
    files.remove('log')
    for file in files:
        if file not in statusRecord['?']:#首先判断file是否被管理，未被管理者不予比较差异
            if file in commitedfiles:
                FilePath = HubPath + file
                CommitedPath = HubPath + 'svn\\' + file +'\\' + file
                #print(FilePath, BakPath)
                Modified = diff(FilePath, CommitedPath)
                if Modified:
                    if file not in statusRecord['M']:
                        statusRecord['M'].append(file)
                        refresh('M', file)
                else:
                    if file in statusRecord['M']:
                        statusRecord['M'].remove(file)
    f = set(files)
    cf = set(commitedfiles)
    #print(files)
    #print(commitedfiles)
    #在仓库中，而不在svn中，说明为新增文件
    #print(list(f.difference(cf)))
    for d in list(f.difference(cf)):
        if d not in statusRecord['?'] and d not in statusRecord['+']:
            statusRecord['+'].append(d)
            refresh('+', d)
        #在svn中，而不在仓库中，说明为删除文件
    #print (list(cf.difference(f)))
    for d in list(cf.difference(f)):
        if d not in statusRecord['D']:
            statusRecord['D'].append(d)
            refresh('D', d)
    for k in statusRecord.keys():
        values = statusRecord[k]
        if len(values):
            print(k + ' ', values[:])

#add函数对应于add命令,讲一个文件或目录加入管理范围,其实就是未受收托管状态中删除
def add(name):
    if name in statusRecord['?']:
        statusRecord['?'].remove(name)
    if name not in statusRecord['+']:
        statusRecord['+'].append(name)
        refresh('+', name)
    #print (statusRecord)
#delete函数对应于delete命令,讲一个文件或目录纳出管理范围,force为真，代表删除物理文件
def delete(name,force = False):
    if name not in statusRecord['?']:
        statusRecord['?'].append(name)
        refresh('?', name)
    if (force):
        os.remove(HubPath + name)
        statusRecord['D'].append(name)
        refresh('D', name)

#mv函数对应于mv命令,移动文件夹,讲仓库里的文件（夹）移动到指定目录下，targetpath需输入相对路径
def mv(name,targetpath):
    if not os.path.exists(HubPath + targetpath):
        os.makedirs(HubPath + targetpath)
    shutil.move(HubPath + name, HubPath + targetpath + name)
    statusRecord['MV'].append(name + ' ./' + name+'-> ./' + targetpath + name)#记录文件的移动情况
    refresh('MV', name)
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
        copy(FilePath, CommittedFile + '_1') #第一个版本命名为:[文件名_1]
        copy(FilePath, CommittedFile)
        if filename not in statusRecord['+']:
            statusRecord['+'].append(filename) #更新状态记录，filename文件为新加：‘+’
            refresh('+', filename)
    else:
        Modified = diff(FilePath, CommittedFile)
        #如果文件被修改了，对原来svn文件夹内该文件的最新版本重命名，将放入该最新版本
        #重命名规则为“文件名+所有版本总数”
        if(Modified):
            Version = len([x for x in os.listdir(ThisFileDirInSvn) if os.path.isfile(ThisFileDirInSvn + os.sep + x)])
            #print (ThisFileDirInSvn)
            #print (Version)
            NewestFileName = filename + '_%d'%Version
            copy(FilePath, os.path.join(ThisFileDirInSvn, NewestFileName))
            # 将新提交的版本作为比较版本
            update = open(CommittedFile, 'w')
            Newest = open(FilePath, 'r')
            #print (str(Newest.readlines()))
            allLines = Newest.readlines()
            for eachLine in allLines:
                update.write(eachLine)
            Newest.close()
            update.close()
            #print('1:',filename)
            if filename not in statusRecord['M']:
                statusRecord['M'].append(filename)  # 记录文件的修改情况
                refresh('M', filename)
                #print (statusRecord['M'])

        else:
            print('no modification')
    logs = open(HubPath + 'log', 'a') #以追加的方式记录修改日志
    logs.write(filename + '  ' + describe + '\n')



#log函数查看所有版本信息以及提交日志，如果有具体文件名，只显示特定文件的提交信息
def log(filename=""):
    logs = open(HubPath + 'log')
    #如果未指定文件名，输出所有日志记录
    if not len(filename):
        while (1):
            line = logs.readline()
            if not line:
                break
            print(line)
    #指定文件名，只输入对应该文件名的日志记录
    else:
        while(1):
            line = logs.readline()
            if not line:
                break
            if line.find(filename) != -1:
                print(line)

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
                    #将回滚的版本作为比较版本
                    update = open(filepath + f, 'w')
                    BackTo = open(filepath + fn, 'r')
                    allLines = BackTo.readlines()
                    for eachLine in allLines:
                        update.write(eachLine)
                    BackTo.close()
                    update.close()

    # 设置版本号和文件名，将特定文件恢复到特定提交版本
    if len(version) and len(filename):
        # 先删除该文件
        filepath = os.path.join(HubPath, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
        # 将特定文件的特定版本copy回来
        FileInSvnPath = HubPath + 'svn\\' + filename
        Versions = os.listdir(FileInSvnPath)
        for fn in Versions:
            if '_%s'%version in fn:
                copy(os.path.join(FileInSvnPath, fn), HubPath)
                os.rename(HubPath + fn, HubPath + filename)
                # 将回滚的版本作为比较版本
                update = open(FileInSvnPath + os.sep + filename, 'w')
                BackTo = open(FileInSvnPath + os.sep + fn, 'r')
                allLines = BackTo.readlines()
                for eachLine in allLines:
                    update.write(eachLine)
                BackTo.close()
                update.close()


if __name__ == '__main__':

    global HubPath #仓库路径
    global statusRecord #初始化一个文件修改记录表
    #读出仓库路径
    if os.path.exists(os.getcwd() + os.sep + 'HubPath.txt'):
        GetPath = open(os.getcwd() + os.sep + 'HubPath.txt')
        HubPath = str(GetPath.readline())
        GetPath.close()

    #首先从文件中加载statusRecord信息

    statusRecord = InitStatusRecord()
    print ('1:', statusRecord)


    #print('2:', statusRecord)

    while(1):
        CommodLine = input().split()
        Commend = CommodLine[1]
        if Commend == "create": #svn create [目录名]
            # HubPath.txt用来存储仓库地址，如果该文件不存在，说明是第一次create
            if os.path.exists(os.getcwd() + os.sep + 'HubPath.txt'):
                GetPath = open(os.getcwd() + os.sep + 'HubPath.txt')
                HubPath = str(GetPath.readline())
                GetPath.close()
                print(HubPath)
                print('创建失败，当前已在一个版本仓库下!')
            else:
                create(CommodLine[2])
                HubPath = os.getcwd() + '\\' + CommodLine[2] + '\\'
                SavePath = open(os.getcwd() + os.sep + 'HubPath.txt', 'w')
                SavePath.write(HubPath)
                SavePath.close()

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
        elif Commend in ("q", "quit"):
            #一旦跳出while循环就要将全局状态变化表写文件保存
            SaveStatusRecord()
            break





















