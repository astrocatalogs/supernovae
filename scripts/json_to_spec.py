import json
import numpy as np
import matplotlib.pyplot as plt

file = raw_input('File to read:  ')

sn = file.split('.')[0]

f = open(file,'r')

data=json.load(f)


f.close()

plt.clf()

for i in range(len(data[sn]['spectra'])):
    test = np.array(data[sn]['spectra'][i]['data'])
    test2 = np.vectorize (float) (test)
    plt.plot(test2[:,0],test2[:,1])
    try:
        np.savetxt(data[sn]['spectra'][i]['filename'],test2,fmt='%.4e',delimiter='\t')
    except: #not all spectra have a filename!
        try:
            np.savetxt(sn+'_'+data[sn]['spectra'][i]['time']+'.dat',test2,fmt='%.4e',delimiter='\t')
        except:
            print ('Spectrum with index ' + str(i) + ' not saved')


plt.show()
