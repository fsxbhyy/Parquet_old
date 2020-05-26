import os
import sys
import re
import glob
import math
import numpy as np
#from pynufft import NUFFT_cpu, NUFFT_hsa
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D



#rs = None
#Lambda = None
#Mass2 = None
#Beta = None
#Charge2 = None
#TotalStep = None
#BetaStr = None
#rsStr = None
#ChargeStr = None
#Mass2Str = None
#LambdaStr = None
#
#with open("inlist", "r") as file:
#    line = file.readline()
#    para = line.split(" ")
#    BetaStr = para[1]
#    Beta = float(BetaStr)
#    rsStr = para[2]
#    rs = float(rsStr)
#    Mass2Str = para[3]
#    Mass2 = float(Mass2Str)
#    LambdaStr = para[4]
#    Lambda = float(LambdaStr)
#    ChargeStr = para[5]
#    Charge2 = float(ChargeStr)
#    TotalStep = float(para[7])
#
#print rs, Beta, Mass2, Lambda, TotalStep
#Miu=1.0
# 0: I, 1: T, 2: U, 3: S
Channel = [0, 1, 2, 3]
# Channel = [3]
ChanName = {0: "I", 1: "T", 2: "U", 3: "S"}
# 0: total, 1: order 1, ...
Order = [0, ]

#folder = "./Beta{0}_rs{1}_lambda{2}/".format(BetaStr, rsStr, Mass2Str)
folder = "./"

FreqBin=None
FreqBinSize=None
AngleBin = None
ExtMomBin = None
AngleBinSize = None
ExtMomBinSize = None
TauBin=None
TauBinSize=None
Data = {}  # key: (order, channel)
DataWithAngle = {}  # key: (order, channel)
DataErr = {}  # key: (order, channel)

Omega=3.0
g=2.0
kF = 1.0
#Nf = kF/2.0/np.pi**2
#Bubble = 0.0971916  # 3D, Beta=10, rs=1
#Step = None

def AngleIntegation(Data, l):
    # l: angular momentum
    shape = Data.shape[1:]
    Result = np.zeros(shape)
    for x in range(AngleBinSize):
        # Result += Data[x, ...] * \
        #     np.cos(l*AngleBin[x])*2.0*np.pi/AngleBinSize
        Result += Data[x, ...]*2.0/AngleBinSize
    return Result/2.0
    # return Result

with open("config.dat","r") as file:
    line0 = file.readline()
    print line0.split(" ")[-1]

    #read Beta from delta.dat
    Beta = float(line0.split(" ")[1])  
    print ("Beta", Beta)
    omega_c=float(line0.split(" ")[-1])  

    line2 = file.readline()
    if FreqBin is None:
        FreqBin = np.fromstring(
            line2, sep=' ')
        FreqBinSize = len(FreqBin)
        print (FreqBinSize)
    #line3 = file.readline()
    #if AngleBin is None:
    #    AngleBin = np.fromstring(
    #       line3.split(":")[1], sep=' ')
    #    AngleBinSize = len(AngleBin)
    #    print (AngleBinSize)
    line4 = file.readline()
    if ExtMomBin is None:
        ExtMomBin = np.fromstring(
            line4, sep=' ')
        ExtMomBinSize = len(ExtMomBin)
        ExtMomBin /= kF   
print ExtMomBin

TauBin=np.zeros(FreqBinSize)
TauBinSize=len(TauBin)
for i in range (TauBinSize):
    TauBin[i]=i*Beta/TauBinSize



#for order in Order:
   # for chan in Channel:
files = os.listdir(folder)
Num = 0
Norm = 0
Data0 = None
DataList = []
#FileName = "vertex{0}_{1}_pid[0-9]+.dat".format(order, chan)
FileName = "delta0.dat"
FileName1="delta0.dat"

if(np.all(FreqBin[:-1] <= FreqBin[1:])):
    print ("fine")
else:
    print ("error")


#initialize delta
gg=np.zeros((FreqBinSize,ExtMomBinSize))
gg_tau=np.zeros((TauBinSize,ExtMomBinSize))
for i0 in range (FreqBinSize):
    for j0 in range (ExtMomBinSize):
        E=ExtMomBin[j0]*ExtMomBin[j0]-1.0
        gg[i0][j0]=1.0 /(FreqBin[i0]*FreqBin[i0]+E*E)
    
for i0 in range (TauBinSize):
    for j0 in range (ExtMomBinSize):
        E=np.abs(ExtMomBin[j0]*ExtMomBin[j0]-1.0)
        gg_tau[i0][j0]=np.sinh(E*(Beta/2.0-TauBin[i0]))/2.0/E/np.cosh(Beta*E/2.0)

cut=np.searchsorted(FreqBin,omega_c,side='right') 

if(os.path.exists(folder+FileName1) and os.path.getsize(folder+FileName1)) > 0:
    delta = np.loadtxt(FileName1)
    delta=delta.reshape((FreqBinSize,ExtMomBinSize))


else:
    delta=np.zeros(FreqBinSize*ExtMomBinSize)
    delta=delta.reshape((FreqBinSize,ExtMomBinSize))
    delta[0:cut,:]=1.0
    delta[cut:,:]=-0.1

f_freq=np.multiply(gg,delta)
phase_shift=np.exp(-1j*np.pi/Beta*TauBin)
ff=phase_shift[:,np.newaxis]*np.fft.fft(f_freq,axis=0)/Beta
F=2*ff.real

#phase_shift=np.exp(-1j*np.pi/Beta*TauBin)
#dd=phase_shift[:,np.newaxis]*np.fft.fft(delta,axis=0)/Beta
#ff=np.multiply(gg_tau,dd)
#F=2*ff.real


delta0=0.0#-g/4.0/np.pi/np.pi*sum(ExtMomBin*F[0])/ExtMomBinSize*ExtMomBin[-1]
taudep= np.cosh(Omega*(0.5*Beta-np.abs(TauBin))) * np.tensordot(ExtMomBin,F,axes=([0,1]))/ExtMomBinSize*ExtMomBin[-1]
delta1=np.tensordot(taudep,np.cos(np.tensordot(FreqBin,TauBin,axes=0)),axes=([0,1]))/TauBinSize*Beta
delta1=delta1*g*Omega/8.0/np.pi/np.pi/np.sinh(0.5*Beta*Omega)+delta0
delta+=np.tensordot(delta1,ExtMomBin,axes=0)

modulus=math.sqrt(np.tensordot(delta[0:cut,:],delta[0:cut,:],axes=([0,1],[0,1])))
delta[0:cut,:]=delta[0:cut,:]/modulus


IterationType=1
loopcounter=0
lamu=0
shift=0.00
lamu_sum=0.0
modulus_dum=0.0
for loopcounter in range(500):

    f_freq=np.multiply(gg,delta)
    phase_shift=np.exp(-1j*np.pi/Beta*TauBin)
    ff=phase_shift[:,np.newaxis]*np.fft.fft(f_freq,axis=0)/Beta
    F=2*ff.real

    #phase_shift=np.exp(-1j*np.pi/Beta*TauBin)
    #dd=phase_shift[:,np.newaxis]*np.fft.fft(delta,axis=0)/Beta
    #ff=np.multiply(gg_tau,dd)
    #F=2*ff.real

    fig=plt.figure()
    ax=fig.add_subplot(111, projection='3d')
    a=FreqBin[:,np.newaxis]+ExtMomBin*0
    a=a.reshape(TauBinSize*ExtMomBinSize)
    print a
    b=np.transpose(ExtMomBin[:,np.newaxis]+TauBin*0)
    b=b.reshape(TauBinSize*ExtMomBinSize)
    print b
    c=delta.reshape(TauBinSize*ExtMomBinSize)
    #modulus=math.sqrt(np.tensordot(c,c,axes=(0,0)))
    #c=c/modulus
    ax.scatter(a, b,c , c='k',marker='.')
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
  #  plt.show()
    plt.savefig('f_q.png')
    plt.close()

    with open("f.dat","w") as file:
        for i in range(TauBinSize):
            file.write("{0} ".format(TauBin[i]))
        file.write("\n")
        for i in range(TauBinSize):
            for k in range(ExtMomBinSize):
                file.write("{0}\t".format(2*ff.real[i][k]))
        file.write("\n{0}".format(loopcounter+1))
    
    #if(loopcounter%5==0):
     #  IterationType=(IterationType+1)%2
    print IterationType
    myCmd='./feyncalc.exe >out.txt'
    #myCmd='python phonon.py>out.txt'
    os.system(myCmd)

    for f in files:
        if re.match(FileName, f):
            #print ("Loading ")
            Norm0 = -1
            d = None
            #try: 
            with open(folder+f, "r") as file:
                #line1 = file.readline()
                # print (line1)
                #Norm0 = float(line1.split(":")[-1])
                # print ("Norm: ", Norm0)
                #file.open(folder+f, "r")
                d = np.loadtxt(folder+f)
                #fig=plt.figure()
                #plt.axvline(omega_c)
                #plt.plot(FreqBin,delta[:,0],'ko')
                #plt.plot(ExtMomBin,delta[0,:],'r.')
                #ax=fig.add_subplot(111, projection='3d')
                #a=FreqBin[:,np.newaxis]+ExtMomBin*0
                #a=a.reshape(FreqBinSize*ExtMomBinSize)
                #print a
                #b=np.transpose(ExtMomBin[:,np.newaxis]+FreqBin*0)
                #b=b.reshape(FreqBinSize*ExtMomBinSize)
                #print b
                #c=d.reshape(FreqBinSize*ExtMomBinSize)
                #modulus=math.sqrt(np.tensordot(c,c,axes=(0,0)))
                #c=c/modulus
                #ax.scatter(a, b,c , c='k',marker='.')
                #ax.set_xlabel('X Label')
                #ax.set_ylabel('Y Label')
                #ax.set_zlabel('Z Label')

                #plt.savefig('d_q.png')
                #plt.close()
                #plt.figure()
                #plt.axvline(omega_c)
                #plt.plot(FreqBin,delta[:,0],'ko')
                #plt.plot(ExtMomBin,delta[0,:],'r.')
                #plt.savefig('delta_new.pdf')
                #plt.close()
                #if d is not None and Norm0 > 0:
                    #if Data0 is None:
                        #Data0 = d
                    #else:
                        # Data0 = d
                    #   Data0 += 
            
   
#       print (TauBin)
    d=-d.reshape((FreqBinSize,ExtMomBinSize))
    delta0=0.0#-g/4.0/np.pi/np.pi*sum(ExtMomBin*F[0])/ExtMomBinSize*ExtMomBin[-1]
    taudep= np.cosh(Omega*(0.5*Beta-np.abs(TauBin))) * np.tensordot(ExtMomBin,F,axes=([0,1]))/ExtMomBinSize*ExtMomBin[-1]
    delta1=np.tensordot(taudep,np.cos(np.tensordot(FreqBin,TauBin,axes=0)),axes=([0,1]))/TauBinSize*Beta
    delta1=delta1*g*Omega/8.0/np.pi/np.pi/np.sinh(0.5*Beta*Omega)+delta0
    d+=np.tensordot(delta1,ExtMomBin,axes=0)
    
    #test=np.sin((Beta*FreqBin-np.pi)/FreqBinSize)
# print (test)
# dd[:,0,0,0]=dd[:,0,0,0]+test
    #separate delta in to high and low frequency 

    
    #print (FreqBin)
    if(IterationType==0):
        delta[cut:,:]=d[cut:,:]
    elif(IterationType==1): 
        d[0:cut,:]=d[0:cut,:]+(shift+0.9*modulus_dum)*delta[0:cut,:]
        lamu=np.tensordot(d[0:cut,:],delta[0:cut,:],axes=([0,1],[0,1]))
        lamu_sum=lamu_sum*0.9+lamu-shift-modulus_dum*0.9
        print lamu-shift-0.9*modulus_dum
        print lamu_sum/10.0
        modulus_dum=math.sqrt(np.tensordot(d[0:cut,:],d[0:cut,:],axes=([0,1],[0,1])))
        print ("modulus:",modulus)
        delta[0:cut,:]=d[0:cut,:]/modulus_dum  
    
    with open("lamu.txt","a+") as file:
    	file.write("{0} \n".format(lamu_sum/10.0))




    #fig=plt.figure()
    #plt.axvline(omega_c)
    #plt.plot(FreqBin,delta[:,0],'ko')
    #plt.plot(ExtMomBin,delta[0,:],'r.')
    #ax=fig.add_subplot(111, projection='3d')
    #a=FreqBin[:,np.newaxis]+ExtMomBin*0
    #a=a.reshape(FreqBinSize*ExtMomBinSize)
    #print a
    #b=np.transpose(ExtMomBin[:,np.newaxis]+FreqBin*0)
    #b=b.reshape(FreqBinSize*ExtMomBinSize)
    #print b
    #c=delta.reshape(FreqBinSize*ExtMomBinSize)
    #ax.scatter(a, b,c , c='k',marker='.')
    #ax.set_xlabel('X Label')
    #ax.set_ylabel('Y Label')
    #ax.set_zlabel('Z Label')
    
    delta.reshape((FreqBinSize,ExtMomBinSize))

    #plt.savefig('delta_q.png')
    #plt.close()
    
    #cut1_num=10.0
    #cut2_num=3.0
    #cut1=np.searchsorted(FreqBin,cut1_num,side='right')
    #cut2=np.searchsorted(ExtMomBin,cut2_num,side='right')
    cutf=np.searchsorted(ExtMomBin,1.0,side='right')
    sum0=1.0
    #for i in range(cut1):
    #    for j in range(cut2):
    #        if(j==cut2-1):
    #            step2=cut2_num-ExtMomBin[j]
    #        else:
    #            step2=ExtMomBin[j+1]-ExtMomBin[j]
    #        step1=2*np.pi/Beta
    #        sum0+=delta[i][j]*step2*step1
    #plt.show()

    with open("qmax.dat","w") as file:
        for i in range(FreqBinSize):
            file.write("{0} ".format(FreqBin[i]))
        file.write("\n")
        for i in range(FreqBinSize):
            file.write("{0} ".format(delta[i][-1]/sum0))
    
    with open("q0.dat","w") as file:
        for i in range(FreqBinSize):
            file.write("{0} ".format(FreqBin[i]))
        file.write("\n")
        for i in range(FreqBinSize):
            file.write("{0} ".format(delta[i][0]/sum0))

    with open("w0.dat","w") as file:
        for i in range(ExtMomBinSize):
            file.write("{0} ".format(ExtMomBin[i]))
        file.write("\n")
        for i in range(ExtMomBinSize):
           file.write("{0} ".format(delta[0][i]/sum0))

    with open("Fermi.dat","w") as file:
        for i in range(FreqBinSize):
            file.write("{0} ".format(FreqBin[i]))
        file.write("\n")
        for i in range(FreqBinSize):
            file.write("{0} ".format(delta[i][cutf]/sum0))


  #  fig=plt.figure()
  #  plt.plot(FreqBin,delta[:,-1],'k.')
  #  plt.savefig('delta_q0.png')
  #  plt.close()

  #  fig=plt.figure()
  #  plt.plot(ExtMomBin,delta[0,:],'k.')
  #  plt.savefig('delta_q1.png')
  #  plt.close()

    ##Fourier Transformation of delta*GG 

# om=np.random.randn(1512,1) #None-Uniform-Fourier-Transform
# Nd=(256,)
# Kd=(512,)
# Jd=(6,)
    
# time_data = np.zeros(256, )
# time_data[96:128+32] = 1.0

# NufftObj=NUFFT_cpu()
# NufftObj.plan(om,Nd,Kd,Jd)
# ff=NufftObj.forward(time_data)
        
# Fourier=np.exp(1j*2*np.pi*np.tensordot(FreqBin,TauBin,0))
# print Fourier.shape
# print Fourier
#  ff=np.tensordot(Fourier,dd,axes=([0,0]))
                #  Norm += Norm0
                #   dd = d.reshape(
                #       (AngleBinSize, ExtMomBinSize, 2))/Norm0
                #   dd = AngleIntegation(dd, 0)
                #   DataList.append(SpinMapping(dd))
                        
        # except:
            #    print "fail to load ", folder+f
            
    #if Norm > 0 and Data0 is not None:
    #        print "Total Weight: ", Data0[0]
    #        Data0 /= Norm
    #        Data0 = Data0.reshape((AngleBinSize, ExtMomBinSize, 2)

   
