#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import h5py as h5
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

plt.rc('text', usetex=True)
plt.rc('font', family='serif')

f=h5.File('Transmission_SAMBA_beforeObjective_withOD02.h5','r')
data=np.array(f['Spectral density'])
f.close()

#interRef=interp1d(ref[:,0],ref[:,1],'cubic')
#retroOverRef=retro[:,1]/interRef(retro[:,0])
def pernm_to_permeV(wave,density):
    temp=1240*(1/(wave-0.5)-1/(wave+0.5))*1000
    return 1240/wave,density/temp

x,y=data[:,0],data[:,1]
fig=plt.figure()
ax=fig.add_subplot(111)
#ax.plot([1240/450,1240/450],[-0.05,1],'k--')
ax.plot(*pernm_to_permeV(x,y),'b-')
#ax.set_xlim([350,1100])
ax.set_xlim([1240/1100,1240/400])
ax.set_xlabel(r'Energy (eV)')
ax.set_ylim([-0.02,1])
ax.set_ylabel(r'Spectral density (\textmu W/meV)')
ax.grid(b=True)
power_area=(x>400)&(x<1240/1.3)
ax.set_title(r'Total power $\approx$%i \textmu W between 1.3 and 3.1 eV'%(round(np.sum(y[power_area])/10)*10))
fig.savefig('Spectral_density_beforeObjective_filteredSAMBA400_withOD02_energy.pdf', bbox_inches='tight')
fig.show()