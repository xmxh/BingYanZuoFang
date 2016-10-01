#!/usr/bin/python
#encoding=utf-8
import sys
import os
import difflib

#diff函数用于判断两个文件内容是否有改动，是，返回1；否，返回0
def diff(f1path,f2path):
    F1 = open(f1path)
    F2 = open(f2path)
    OutPath = r'c:\test\\'   #输出对比结果为html到该路径下
    Context1 = F1.readlines()
    Context2 = F2.readlines()
    #生成html方便查看
    d = difflib.HtmlDiff()
    html = d.make_file(Context1, Context2)
    Out = open(OutPath+'1.html','w')
    Out.write(html)

    #快速判断两个文件是否不同
    if len(Context1)!=len(Context2):
        return 1
    else:
        for (l1, l2) in zip(Context1, Context2):
            if l1 != l2:
                return 1
    return 0

if __name__ == '__main__':
    '''
    File1Path=r'c:\test\1.txt'
    File2Path=r'c:\test\2.txt'
    print (diff(File1Path, File2Path))
    '''
    commend = sys.argv[1]
    if(commend=='create'):
        os.mkdir(sys.argv[2])
