import subprocess
import cv2
import numpy as np
import time
import threading
import re
from collections import Counter

ZONA=(0.22,0.78,0.04,0.10) #Zona disparadora, como fracción de la pantalla: (x desde, x hasta, y desde, y hasta)
TOL=20

def capturar(serial):
    datos=subprocess.run(["adb","-s",serial,"exec-out","screencap","-p"],capture_output=True).stdout
    return cv2.imdecode(np.frombuffer(datos,np.uint8),cv2.IMREAD_COLOR)

def agrupar(valores,tol):
    valores=sorted(valores)
    grupos=[[valores[0]]]
    for v in valores[1:]:
        if v-grupos[-1][-1]<=tol: grupos[-1].append(v)
        else: grupos.append([v])
    return grupos

def detectarTablero(img):
    imgInt=img.astype(int)
    fondo=imgInt[5,5]
    difFondo=np.abs(imgInt-fondo).max(axis=2)
    difBlanco=np.abs(imgInt-255).max(axis=2)
    mascara=((difFondo>12)&(difBlanco>12)).astype(np.uint8)
    total,_,stats,_=cv2.connectedComponentsWithStats(mascara)
    cand=[]
    for i in range(1,total):
        x,y,w,h,_=stats[i]
        if 40<w<400 and abs(int(w)-int(h))<=6: cand.append((int(x),int(y),int(w),int(h)))
    if len(cand)<9: return None
    modo=Counter(c[2] for c in cand).most_common(1)[0][0]
    cand=[c for c in cand if abs(c[2]-modo)<=5]
    colsOk=[g for g in agrupar([c[0] for c in cand],5) if len(g)>=3]
    filasOk=[g for g in agrupar([c[1] for c in cand],5) if len(g)>=3]
    if len(colsOk)!=len(filasOk) or len(colsOk)<3: return None
    xsOk=[x for g in colsOk for x in g]
    ysOk=[y for g in filasOk for y in g]
    cand=[c for c in cand if c[0] in xsOk and c[1] in ysOk]
    n=len(colsOk)
    xmin=min(c[0] for c in cand); xmax=max(c[0]+c[2] for c in cand)
    ymin=min(c[1] for c in cand); ymax=max(c[1]+c[3] for c in cand)
    huecoX=((xmax-xmin)-modo)/(n-1)-modo
    huecoY=((ymax-ymin)-modo)/(n-1)-modo
    return n,xmin-huecoX/2,ymin-huecoY/2,xmax+huecoX/2,ymax+huecoY/2

def leerTablero(img,N,X0,Y0,X1,Y1):
    cw,ch=(X1-X0)/N,(Y1-Y0)/N
    colores,matriz=[],[]
    for fila in range(N):
        linea=[]
        for col in range(N):
            x=int(X0+col*cw+cw*0.2)
            y=int(Y0+fila*ch+ch*0.2)
            parche=img[y-2:y+3,x-2:x+3].reshape(-1,3)
            color=np.median(parche,axis=0)
            for i,c in enumerate(colores):
                if np.linalg.norm(color-c)<TOL:
                    linea.append(i)
                    break
            else:
                colores.append(color)
                linea.append(len(colores)-1)
        matriz.append(linea)
    return matriz,len(colores)

def detectarGatos(img,N,X0,Y0,X1,Y1):
    cw,ch=(X1-X0)/N,(Y1-Y0)/N
    gatos=[-1]*N
    for fila in range(N):
        for col in range(N):
            celda=img[int(Y0+fila*ch):int(Y0+(fila+1)*ch),
                      int(X0+col*cw):int(X0+(col+1)*cw)]
            gris=cv2.cvtColor(celda,cv2.COLOR_BGR2GRAY)
            if np.count_nonzero(gris<70)>300: gatos[fila]=col
    return gatos

def colocar(matriz,fila,gatos,fijas,colsUsadas,regsUsadas):
    n=len(matriz)
    if fila==n: return True
    if fijas[fila]: return colocar(matriz,fila+1,gatos,fijas,colsUsadas,regsUsadas)
    for col in range(n):
        region=matriz[fila][col]
        if colsUsadas[col] or regsUsadas[region]: continue
        if fila>0 and gatos[fila-1]!=-1 and abs(gatos[fila-1]-col)<=1: continue
        if fila<n-1 and gatos[fila+1]!=-1 and abs(gatos[fila+1]-col)<=1: continue
        gatos[fila]=col
        colsUsadas[col]=True
        regsUsadas[region]=True
        if colocar(matriz,fila+1,gatos,fijas,colsUsadas,regsUsadas): return True
        gatos[fila]=-1
        colsUsadas[col]=False
        regsUsadas[region]=False
    return False

def resolver(matriz,iniciales):
    n=len(matriz)
    gatos=list(iniciales)
    fijas=[c!=-1 for c in iniciales]
    colsUsadas=[False]*n
    regsUsadas=[False]*n
    for fila in range(n):
        if fijas[fila]:
            colsUsadas[gatos[fila]]=True
            regsUsadas[matriz[fila][gatos[fila]]]=True
    if colocar(matriz,0,gatos,fijas,colsUsadas,regsUsadas): return gatos,fijas
    return None,fijas

def tocar(fila,col,N,X0,Y0,X1,Y1,serial):
    cw,ch=(X1-X0)/N,(Y1-Y0)/N
    x=int(X0+(col+0.5)*cw)
    y=int(Y0+(fila+0.5)*ch)
    subprocess.run(["adb","-s",serial,"shell",f"input tap {x} {y} & input tap {x} {y}"])

def procesar(img):
    tablero=detectarTablero(img)
    if tablero is None: raise(SystemExit("No se encontro el tablero en la captura"))
    N,X0,Y0,X1,Y1=tablero
    matriz,nRegiones=leerTablero(img,N,X0,Y0,X1,Y1)
    if nRegiones!=N: raise(SystemExit(f"Se detectaron {nRegiones} regiones, se esperaban {N}"))
    iniciales=detectarGatos(img,N,X0,Y0,X1,Y1)
    sol,fijas=resolver(matriz,iniciales)
    if sol is None: raise(SystemExit("No se encontro la solucion, revisa la lectura"))
    return tablero,matriz,sol,fijas

def resolverNivel(serial):
    img=capturar(serial)
    tablero,matriz,sol,fijas=procesar(img)
    N,X0,Y0,X1,Y1=tablero
    print(serial,"-> Tablero",N,"x",N,sol)
    for fila,col in enumerate(sol):
        if fijas[fila]: continue
        tocar(fila,col,N,X0,Y0,X1,Y1,serial)
        time.sleep(0.0001)

def leerPantallaTactil(serial):
    salida=subprocess.run(["adb","-s",serial,"shell","getevent","-lp"],capture_output=True,text=True).stdout
    dispositivo,maxX,maxY,actual=None,None,None,None
    for linea in salida.splitlines():
        if linea.startswith("add device"):
            actual=linea.split(":")[-1].strip()
        m=re.search(r"ABS_MT_POSITION_X\s*:.*?max (\d+)",linea)
        if m and dispositivo is None:
            dispositivo,maxX=actual,int(m.group(1))
        m=re.search(r"ABS_MT_POSITION_Y\s*:.*?max (\d+)",linea)
        if m and actual==dispositivo and maxY is None:
            maxY=int(m.group(1))
    return dispositivo,maxX,maxY

def ejecutar(serial,bloqueo):
    try:
        resolverNivel(serial)
    except SystemExit as e:
        print(serial,"->",e)
    finally:
        bloqueo.release()

def escuchar(serial):
    dispositivo,maxX,maxY=leerPantallaTactil(serial)
    if dispositivo is None or maxX is None or maxY is None:
        print(serial,"-> no se encontro la pantalla tactil")
        return
    bloqueo=threading.Lock()
    proc=subprocess.Popen(["adb","-s",serial,"shell","getevent","-l",dispositivo],stdout=subprocess.PIPE,text=True)
    x,y,esperando=0,0,False
    for linea in proc.stdout:
        p=linea.split()
        if len(p)<3: continue
        codigo,valor=p[-2],p[-1]
        if codigo=="ABS_MT_POSITION_X": x=int(valor,16)/maxX
        elif codigo=="ABS_MT_POSITION_Y": y=int(valor,16)/maxY
        elif codigo=="ABS_MT_TRACKING_ID": esperando=(valor!="ffffffff")
        elif codigo=="SYN_REPORT" and esperando:
            esperando=False
            if ZONA[0]<=x<=ZONA[1] and ZONA[2]<=y<=ZONA[3]:
                if bloqueo.acquire(blocking=False):
                    threading.Thread(target=ejecutar,args=(serial,bloqueo)).start()

def listarDispositivos():
    salida=subprocess.run(["adb","devices"],capture_output=True,text=True).stdout
    return [l.split()[0] for l in salida.splitlines()[1:] if l.strip().endswith("device")]

if __name__=="__main__":
    dispositivos=listarDispositivos()
    print("Dispositivos:",dispositivos)
    for serial in dispositivos: threading.Thread(target=escuchar,args=(serial,),daemon=True).start()
    print("Pulsa la zona entre nivel y puntuacion en el celular conectado que quieras usar. Ctrl+C para salir.")
    while True: time.sleep(0.3)