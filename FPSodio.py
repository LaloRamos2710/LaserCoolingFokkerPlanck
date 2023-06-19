# -*- coding: utf-8 -*-
"""SparseNumerico_FokkerPlanck.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/139YsU0vuil0KgS3MccNNGeXix89dfC4g
"""

import cupy as cp
import numpy as np
import matplotlib.pyplot as plt
import scipy.constants as cnts
import cupyx.scipy as csc
from cupyx.scipy import sparse
import cupyx.scipy.sparse.linalg
import scipy as sc
from scipy import sparse
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation

#NÚMERO DE CICLOS
n = 4096

# CONSTANTES FISICAS
hbar = cnts.hbar # J s. constante de Planck
kB = cnts.k #m^2 kg s^(-2) K^(-1). constante de Boltzmann
c = cnts.speed_of_light # m/s. velocidad de la luz en el vacio
mu_B = 9.27400968e-24 #m^(-1) tesla^(-1). magneton de Bohr

#CONSTANTES ASOCIADAS A LITIO-6 Y TRANSICION D2
m_Li = 0.381754035e-25 # kg. masa
nu_12 = 508.8487162e12 #1/s. frecuencia de transicion
lifetime = 16.2492e-9 #sgs. vida media
v_r = 2.9461e-2 #m/s. velocidad de recoil
Isat = 13.4144 #mW/cm^2. intensidad de saturacion
g_Li = 2.002296 #factor g electronico total

#CALCULAMOS UNIDADES NATURALES DE LITIO-6

omega_12 = 2*np.pi*nu_12 #s^(-1). frecuencia
gm = 1/(2*lifetime) #1/s.
k_r = ((m_Li/hbar)*v_r) #1/m. #numero de onda asociado
z_r = 1/k_r #m. longitud natural
p_r = m_Li*v_r #kg m s^(-1). momento de recoil
E_r = ((hbar*k_r)**2)/(2*m_Li) #J. energia de recoil
omega_r = E_r/hbar #Hz. frecuencia de recoil
F_r = E_r/z_r #N. fuerza natural
D_r = omega_r*p_r**2

#VALORES ASOCIADOS AL LÁSER Y CAMPO MAGNETICO

delta = gm
#lambda_L = 671e-9 #m.  longitud de onda
#P_L = 75 #mW.  potencia
#radio_L = 1.27 #cm. radio de apertura
b = 25e-6 #T/m. campo magnetico

#CALCULAMOS CONSTANTES ASOCIADAS AL LASER

#k_L = (2*np.pi)/lambda_L # 1/m. numero de onda
#area_L = np.pi*(radio_L)**2 #cm^2. area de apertura
I_L = 0.1*Isat #mW/cm^2. intensidad del laser
omega_L = omega_12-delta #1/s.  frecuencia del laser
k_L = omega_L/c
lambda_L = (2*np.pi)/k_L

print(f"El número de onda del láser es k_L = {k_L}")
print(f"La intensidad del láser es I_L = {I_L}")
print(f"La frecuencia del láser es omega_L = {omega_L}")
print(f"La longitud de onda del láser es lambda_L = {lambda_L}")

#CONSTANTES ASOCIADAS A LA INTERACCIÓN ATOMO-MOT

#parametro de saturación
s= I_L/Isat
#frecuencia de rabi
Omega = 2*gm*np.sqrt(s/2) #Hz
#detuning
delta = omega_12-omega_L #s^(-1)
#constante de friccion
beta = 4*hbar*(k_L**2)*delta*s/(gm*(1 + s + (delta/gm)**2)**2) #s/m
#constante armonica
kappa = (g_Li*mu_B*b/(hbar*k_L))*beta
#constante de difusion
D = 2*(gm*(hbar*k_L)**2)*((s/(1 + s + (delta/gm)**2)))

#LONGITUDES NATURALES DEL SISTEMA
print(f"La frecuencia de transición es   omega_12={omega_12} 1/segundo")
print(f"La frecuencia de recoil es       omega_r={omega_r} 1/segundo")
print(f"El número de onda de recoil es   k_r={k_r} 1/m")
print(f"La frecuencia de recoil es       omega_r={omega_r} 1/segundo")
print(f"La longitud natural es           zr={1e9*z_r} nanómetros")
print(f"El momento natural es            pr={p_r} kg metros/segundo")
print(f"La velocidad natural es          vr={100*v_r} cm/segundo")
print(f"La energía natural es            Er={E_r} joules")
print(f"La fuerza natural es             Fr={F_r} newtons")
print(f"La difusión natural es           Dr={D_r} momento^2/sgs")

print(f"El parametro de saturación es s={s}")
print(f"La frecuencia de Rabi es Omega={Omega}")
print(f"El detuning es delta={delta}")
print(f"La constante de fricción es beta={beta}")
print(f"beta adimensional es {(1/F_r)*beta*v_r}")
print(f"La constante armónica es kappa={kappa}")
print(f"kappa adimensional es {(1/F_r)*kappa*z_r}")
print(f"La constante de difusión es D={D}")
print(f"D adimensional es {D/(omega_r*p_r**2)}")
print("\n")
print(f"La mínima temperatura debería ser {D/(kB*beta)}.")

# LÍMITES DEL SISTEMA
paso = 2**8

h = z_r # metros
dzr = 1024*h #metros
z_max = paso*dzr
print(f"dzr es {100*dzr} cm")
print(f"z_max es {100*z_max} cm")
print(f"\n")

hp = p_r # m/s
dpr = 4*hp
p_max = paso*dpr
print(f"dvr es {100*dpr/m_Li} cm/s")
print(f"v_max es {100*(p_max/m_Li)} cm/s")
print(f"\n")

print(f"Tenemos {2*paso} pasos.")
print(f"La fracción de paso es {1/(2*paso)}")

#fuerza que actúa sobre nuestro sistema
def Fz(c):
  z = c[0]*z_r
  p = c[1]*p_r
  v = p/m_Li

  return cp.float64(-(1/F_r)*(kappa*z +  beta*v))

# CONDICIÓN INICIAL f(z,p)

#la definiremos a partir de una temperatura inicial
T = 100e-3 # kelvins
sigmap = cp.sqrt(m_Li*kB*T)
sigmaz = 1e-3

def func_ini(z_adim,p_adim):
  z = z_adim*z_r
  p = p_adim*p_r

  Ap = cp.float64(z_r/((sigmap)*cp.sqrt(2*cp.pi)))
  Az = cp.float64(p_r/((sigmaz)*cp.sqrt(2*cp.pi)))

  fp = Ap*cp.exp(-0.5*((p/sigmap)**2))
  fz = Az*cp.exp(-0.5*((z/sigmaz)**2))

  #if z > sigmaz or z < -sigmaz:
    #return 0
  #else:
    #return cp.float64(fp/(2*sigmaz))
  
  return fp*fz

print(f"sigmav es {100*cp.sqrt(m_Li*kB*T)/m_Li} cm/s")
print(f"sigmaz es {sigmaz} m")

# ADIMENSIONALIZACIÓN Y CONSTRUCCIÓN DE ARREGLOS
z0 = z_max/z_r
dz = dzr/z_r
print(f"z0 es {z0}")
print(f"dz es {dz}")

p0 = p_max/p_r
dp = dpr/p_r
print(f"p0 es {p0}")
print(f"dp es {dp}")

zs = cp.arange(-z0, z0, dz)
mz = len(zs)
ZS = cp.asnumpy(zs)

ps = cp.arange(-p0,p0,dp)
mp = len(ps)
PS = cp.asnumpy(ps)
print(f"mz es {mz} y mp es {mp}")

#ps = 2.0*cp.pi*cp.sort(cp.fft.fftfreq(len(zs),dz))
#mp = len(ps)
#dp = 2*cp.pi/(dz*mz)

zs_center = int(cp.where(cp.abs(zs)<0.5*dz)[0][0])
ps_center = int(cp.where(cp.abs(ps)<0.5*dp)[0][0])

#calculamos todos los valores de fz y dfzp, y vemos cual es el maximo
maxFz = 0
maxDFzp = 0
for i in np.arange(mz):
  for j in np.arange(mp):
    z = ZS[i]
    p = PS[j]
    if abs(Fz((z,p))) > maxFz:
      maxFz = abs(Fz((z,p)))

print(f"El máximo de la fuerza es {maxFz}.")
#calculamos las cuatro condiciones para dt

D_adim = D/((p_r**2)*omega_r)
beta_adim = beta/(v_r*omega_r)

cond1 = (2*dz)/ps[mp-1]
cond2 = 2/beta_adim
cond3 = (4*dp)/maxFz
cond4 = (2*dp**2)/D_adim

condiciones = [cond1,cond2,cond3,cond4]

CondM = min(condiciones)
print(f"cond 1 = {cond1}, cond 2 = {cond2}, cond 3 = {cond3}, cond 4 = {cond4}")

#dt debe ser menor que 1/4 que la mínima condición
pow = 0
dt = 1
while dt/CondM > 1/4:
  pow = pow + 1
  dt = dt/2

print(f"dt adimensional es (1/2)^{pow}={dt}.")
#tiempo de iteración
max_iter_time = n*dt
print(f"tmax es {1e3*(2*np.pi*max_iter_time/omega_r)} con paso dt={1e3*(2*np.pi*dt/omega_r)} (en milisegundos).")

"""Ahora, definimos el intervalo de tiempo que utilizaremos, inicializamos la solución $u$ y ponemos la condición inicial $u(z,p,0)=f(z,p)$. Normalmente, tomaremos a $f(z,p)$ como una Gaussiana o una delta de Dirac."""

# Inicializamos la solución u(n,i,j)
u = cp.empty((n, mz, mp))

Z, P = cp.meshgrid(zs, ps)

#aplicamos la funcion al espacio fase 
# ponemos la condición inicial
u[0] = func_ini(Z,P)

"""A continuación, definimos la matriz de coeficientes $A^{n}_{\ell,k}$. Para ello, tratamos por separado el caso de los bordes, recordando que suponemos que nuestra solución se anula en ellos."""

#para realizar la simulación, primero definimos la matriz An
# inicializamos A
An = sc.sparse.lil_matrix((mz*mp,mz*mp))

for i in range(mz):
  for j in range(mp):
    k = i*mp + j
    l = j*mz + i
    z  = np.float64(ZS[i]-ZS[zs_center])
    p  = np.float64(PS[j]-PS[ps_center])
    coord = np.array([z,p])
    dF = -beta_adim
    
    FZ = np.float64(Fz(coord))
    
    a = 1/dt + 0.5*dF + D_adim/dp**2
    b = 2*p/(4*dz)
    c = -FZ/(4*dp) + D_adim/(2*(dp**2))
    d = -FZ/(4*dp) - D_adim/(2*(dp**2))

    #condiciones que indican si estamos en un borde o esquina
    esq_sup_izq = i==0 and j==0
    esq_sup_der = i==mz-1 and j==0
    esq_inf_izq = i==0 and j==mp-1
    esq_inf_der = i==mz-1 and j==mp-1

    lat_izq = i==0
    lat_der = i==mz-1
    bor_sup = j==0
    bor_inf = j==mp-1

    # tratamos las condiciones de frontera
    if lat_izq:
      if esq_sup_izq:
        An[k,l]   = a
        An[k,l+1] = b
        An[k,l+mp] = -c
      elif esq_inf_izq:
        An[k,l]   = a
        An[k,l+1] = b
        An[k,l-mp] = d
      else:
        An[k,l]   = a
        An[k,l+1] = b
        An[k,l+mp] = -c
        An[k,l-mp] = d
    elif lat_der:
      if esq_sup_der:
        An[k,l]   = a
        An[k,l-1] = -b
        An[k,l+mp] = -c
      elif esq_inf_der:
        An[k,l]   = a
        An[k,l-1] = -b
        An[k,l-mp] = d
      else:
        An[k,l]   = a
        An[k,l-1] = -b
        An[k,l+mp] = -c
        An[k,l-mp] = d
    elif bor_sup:
      An[k,l]   = a
      An[k,l+1] = b
      An[k,l-1] = -b
      An[k,l+mp] = -c
    elif bor_inf:
      An[k,l]   = a
      An[k,l+1] = b
      An[k,l-1] = -b
      An[k,l-mp] = d
    # vamos con los puntos interiores
    else:
      An[k,l]   = a
      An[k,l+1] = b
      An[k,l-1] = -b
      An[k,l+mp] = -c
      An[k,l-mp] = d

"""Construimos el lado derecho de la ecuación que queremos resolver, obteniendo el vector $\mathcal{D}^{n}_{i,j}$. Nótese que hay que construir este lado a partir de la matriz del paso anterior $u^{n}_{i,j}$."""

def VectorBn(U0):
  U = cp.transpose(U0)
  Dn = np.zeros((mz,mp))
  for i in range(mz):
    for j in range(mp):
      z  = ZS[j]-ZS[zs_center]
      p  = PS[j]-PS[ps_center]

      coord =  np.array([z,p])
      dF = -beta_adim
      
      FZ = Fz(coord)
  
      A = 1/dt - 0.5*dF - D_adim/dp**2
      a = 1/dt + 0.5*dF + D_adim/dp**2
      b = 2*p/(4*dz)
      c = -FZ/(4*dp) + D_adim/(2*(dp**2))
      d = -FZ/(4*dp) - D_adim/(2*(dp**2))

      esq_sup_izq = i==0 and j==0
      esq_sup_der = i==mz-1 and j==0
      esq_inf_izq = i==0 and j==mp-1
      esq_inf_der = i==mz-1 and j==mp-1

      lat_izq = i==0
      lat_der = i==mz-1
      bor_sup = j==0
      bor_inf = j==mp-1

      if lat_izq:
        if esq_sup_izq:
          Dn[i,j] = A*U[i,j]-b*U[i+1,j]+c*U[i,j+1]
        elif esq_inf_izq:
          Dn[i,j] = A*U[i,j]-b*U[i+1,j]-d*U[i,j-1]
        else:
          Dn[i,j] = A*U[i,j]-b*U[i+1,j]+c*U[i,j+1]-d*U[i,j-1]
      elif lat_der:
        if esq_sup_der:
          Dn[i,j] = A*U[i,j]+b*U[i-1,j]+c*U[i,j+1]
        elif esq_inf_der:
          Dn[i,j] = A*U[i,j]+b*U[i-1,j]-d*U[i,j-1]
        else:
          Dn[i,j] = A*U[i,j]+b*U[i-1,j]+c*U[i,j+1]-d*U[i,j-1]
      elif bor_sup:
        Dn[i,j] = A*U[i,j]-b*U[i+1,j]+b*U[i-1,j]+c*U[i,j+1]
      elif bor_inf:
        Dn[i,j] = A*U[i,j]-b*U[i+1,j]+b*U[i-1,j]-d*U[i,j-1]
      #por fin tratamos los casos interiores
      else:
        Dn[i,j] = A*U[i,j]-b*U[i+1,j]+b*U[i-1,j]+c*U[i,j+1]-d*U[i,j-1]

  vector_Bn = cp.array(cp.reshape(Dn,mz*mp,order='F'))
  return vector_Bn

An = csc.sparse.csr_matrix(An)

"""Para resolver el sistema $Ax=b$, lo primero que hacemos es invertir la matriz $A$. Posteriormente, calculamos la solución como $x=A^{-1}b$."""

from matplotlib.colors import Normalize
#esta función es la que realiza la simulación
def calculate(u0):
    for kt in range(0, n-1, 1):
      print(f"ciclo {kt+1} de {n-1}.")
      bn = VectorBn(cp.asnumpy((u0[kt])))
      Unew = csc.sparse.linalg.spsolve(An,bn)
      u0[kt+1] = cp.reshape(Unew,(mz,mp),order='F')
      #ponemos como condición que la solución sea cero en la frontera
      u0[kt+1,0,:] = 0.
      u0[kt+1,:,0] = 0.
      u0[kt+1,mz-1,:] = 0.
      u0[kt+1,:,mp-1] = 0.
      u0[kt+1][u0[kt+1]<0] = 0 #eliminamos los valores negativos de la solución
      #normalizamos la solución
      normal = dz*dp*cp.sum(u0[kt+1])
      u0[kt+1] = u0[kt+1]/normal
    return u0

u = calculate(u)

U = cp.asnumpy(u)
np.save('Ufpres.npy',U)
np.save('ZSfpres.npy',ZS)
np.save('PSfpres.npy',PS)

"""Realizamos una animación para ver gráficamente los resultados."""

ZS = cp.asnumpy(z_r*zs*100)
VS = cp.asnumpy(p_r*ps/m_Li)
US = U/(v_r*z_r)

def plotheatmap(u_k, kk):
    # Clear the current plot figure
    plt.clf()

    plt.title(f"Distribución FP. Ciclo {kk}. \n Temp. inicial={T} K, MOT.")
    plt.xlabel("z (cm)")
    plt.ylabel("v (m/s)")

    # This is to plot u_k (u at time-step k)
    plt.pcolormesh(ZS,VS,u_k, cmap=plt.cm.jet)#,vmin=-4e35,vmax=3.5e35)
    plt.colorbar()

    return plt

def animate(kk):
    plotheatmap(US[kk], kk)

anim = animation.FuncAnimation(plt.figure(), animate, interval=5, frames=n, repeat=False)
anim.save("fokker_planck_bueno.gif")

#calculamos el valor esperado de p, p^2, z y z^2
esperadoP = cp.zeros(n)
esperadoP2 = cp.zeros(n)

esperadoZ = cp.zeros(n)
esperadoZ2 = cp.zeros(n)

temp = cp.zeros(n)
DeltaZ = cp.zeros(n)

for k in cp.arange(n):
  UP = np.multiply(cp.asnumpy(cp.transpose(u[k])),p_r*PS)
  UP2 = np.multiply(UP,p_r*PS)

  sumP = np.sum(UP)
  sumP = dz*dp*sumP
  esperadoP[k] = sumP

  sumP2 = np.sum(UP2)
  sumP2 = dz*dp*sumP2
  esperadoP2[k] = sumP2

  temp[k] = (esperadoP2[k]-(esperadoP[k])**2)/(m_Li*kB)

  UZ = np.multiply(cp.asnumpy(cp.transpose(u[k])),ZS)
  UZ2 = np.multiply(UZ,ZS)

  sumZ = np.sum(UZ)
  sumZ = dz*dp*sumZ
  esperadoZ[k] = sumZ

  sumZ2 = np.sum(UZ2)
  sumZ2 = dz*dp*sumZ2
  esperadoZ2[k] = sumZ2

  DeltaZ[k] = esperadoZ2[k]-(esperadoZ[k])**2

TS = cp.asnumpy(temp)

np.save('temp_bueno.npy',TS)
Tmin = min(temp)
print(f"Temperatura mínima: {1e6*Tmin} microKelvin")

nt=n
ts = np.arange(nt)
plt.clf()
plt.scatter(ts,cp.asnumpy(temp)[0:nt],s=10)
plt.yscale('log')
plt.title("Temperatura contra ciclos de tiempo.")
plt.xlabel("Ciclo de tiempo")
plt.ylabel("Temperatura (Kelvin)")
plt.savefig("FP_temperatura_bueno.png")

nt=n
ts = np.arange(nt)
plt.clf()
plt.scatter(ts,cp.asnumpy(temp)[0:nt],s=10)
plt.yscale('log')
plt.title("Incertidumbre en z contra ciclos de tiempo.")
plt.xlabel("Ciclo de tiempo")
plt.ylabel("Incertidumbre en z (metros)")
plt.savefig("FP_DeltaZ_bueno.png")
