#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
import numpy as np
import os
import h5py as h5
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def data_dictionary(directory):
    data_dictionary={}
    for filename in os.listdir(directory):
        if filename.endswith(".h5"):
            f=h5.File(directory+filename,'r')
            try:
                file_keys=[key.decode('utf-8') for key in f['Ref']]
            except KeyError:
                file_keys=f.keys()
            data_dictionary.update(dict.fromkeys(file_keys,directory+filename))
            f.close()
            continue
        else:
            continue
    return data_dictionary

components_directory='data/components/'
sources_directory='data/sources/'
components_dictionary=data_dictionary(components_directory)
sources_dictionary=data_dictionary(sources_directory)
try:
    os.mkdir(os.getcwd()+'/results/')
except:
    pass
    
def return_data(dictionary, ref, dataset):
    f=h5.File(dictionary[ref],'r')
    data=np.array(f[dataset])
    f.close()
    return data[:,0], data[:,1]

def calculate_transmission(tableWidget,source, ResolutionGraph):
    numrows = tableWidget.rowCount()
    min_wl=0
    max_wl=1e6
    transmission_interpolations=[]
    occurences=[]
    for i in range(numrows+1):
        if i<numrows:
            occurence=int(tableWidget.item(i,2).text())
            add_data=occurence!=0
            if add_data:
                ref=tableWidget.item(i,0).text()
                dataset=tableWidget.item(i,1).text()
                dictionary=components_dictionary
                y_scale=100
        else:
            add_data=source!='None'
            if add_data:
                occurence=1
                ref=source
                dataset=source
                dictionary=sources_dictionary
                y_scale=1
        if add_data:                    
            occurences+=[occurence]
            
            x,y=return_data(dictionary,ref,dataset)
            interp=interp1d(x,y/y_scale)
            
            min_wl=max(np.min(x),min_wl)
            max_wl=min(np.max(x),max_wl)
                
            transmission_interpolations+=[interp]

    x_transmission=np.arange(min_wl,max_wl,ResolutionGraph)
    transmission=np.ones(x_transmission.shape)
    for i,interp in enumerate(transmission_interpolations):
        transmission*=interp(x_transmission)**occurences[i]
    return x_transmission,transmission

class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        uic.loadUi("select_components.ui", self)
        self.setWindowTitle('Transmission simulation')
        
        refs=list(components_dictionary.keys())
        refs.sort()
        self.comboBox_refs.addItems(refs)
        
        sources=list(sources_dictionary.keys())
        sources.sort()
        self.comboBox_sources.addItems(sources)
        
        self.comboBox_refs.currentIndexChanged.connect(self.change_refs)
        self.pushButton_addComponent.clicked.connect(self.add_components)
        self.pushButton_plot.clicked.connect(self.plot_transmission)
        self.pushButton_clearTable.clicked.connect(self.clear_table)
        self.pushButton_save.clicked.connect(self.save)
        self.pushButton_load.clicked.connect(self.load)
        
    def change_refs(self):
        filename=components_dictionary[self.comboBox_refs.currentText()]
        f=h5.File(filename,'r')
        dataset_list=list(f.keys())
        f.close()
        dataset_list.remove('Ref')
        self.comboBox_datasets.clear()
        self.comboBox_datasets.addItems(dataset_list)
    
    def add_components(self):
        tableWidget=self.tableWidget_components
        rowPosition = tableWidget.rowCount()
        tableWidget.insertRow(rowPosition)
        numcols = tableWidget.columnCount()
        numrows = tableWidget.rowCount()           
        tableWidget.setRowCount(numrows)
        tableWidget.setColumnCount(numcols)           
        tableWidget.setItem(numrows -1,0,QtWidgets.QTableWidgetItem(self.comboBox_refs.currentText()))
        tableWidget.setItem(numrows -1,1,QtWidgets.QTableWidgetItem(self.comboBox_datasets.currentText()))
        tableWidget.setItem(numrows -1,2,QtWidgets.QTableWidgetItem(str(self.spinBox_quantity.value())))
       
    def plot_transmission(self):
        tableWidget=self.tableWidget_components
        source=self.comboBox_sources.currentText()
        x_transmission,transmission=calculate_transmission(tableWidget,source,np.float(self.lineEdit_ResolutionGraph.text()))
        
        fig=plt.figure()
        ax=fig.add_subplot(111)
        ax.plot(x_transmission,transmission,'b-')
        ax.set_xlim([np.float(self.lineEdit_plotAbsMin.text()),np.float(self.lineEdit_plotAbsMax.text())])
        ax.set_ylim([np.min(transmission)*0.95,np.max(transmission)*1.05])
        plt.show()
             
    def clear_table(self):
        self.tableWidget_components.setRowCount(0)
    
    def save(self):         
         filename,extension = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Transmission', os.getcwd()+'/results/Transmission.h5', '*.h5')
         if filename=='':
             pass
         else:
             tableWidget=self.tableWidget_components
             source=self.comboBox_sources.currentText()
             
             numrows=tableWidget.rowCount()
             parameters=[[tableWidget.item(i,j).text() for j in range(3)] for i in range(numrows)]
             parameters=np.array(parameters,dtype='S')
             f=h5.File(filename,'w')
             dset=f.create_dataset('Components', data=parameters)
             dset.attrs['Source']=source
             
             x_transmission,transmission=calculate_transmission(tableWidget,source, np.float(self.lineEdit_ResolutionGraph.text()))
             if source!='None':
                 dset2=f.create_dataset('Spectral density',(len(x_transmission),2))
                 dset2.attrs['Unit']='microW/nm'
             else:
                 dset2=f.create_dataset('Transmission',(len(x_transmission),2))
             dset2[:,:]=np.vstack((x_transmission,transmission)).T
             f.close()
         
    def load(self):         
         tableWidget=self.tableWidget_components
         sources=self.comboBox_sources
         
         filename,extension = QtWidgets.QFileDialog.getOpenFileName(self, 'Load Transmission', os.getcwd()+'/results/', '*.h5')
         if filename=='':
             pass
         else:
             f=h5.File(filename,'r')
             parameters=f['Components']
             numrows=parameters.shape[0]
             tableWidget.setRowCount(numrows)
             for i in range(numrows):
                 for j in range(3):
                     tableWidget.setItem(i,j,QtWidgets.QTableWidgetItem(parameters[i,j].decode('utf-8')))
             source=parameters.attrs['Source']
             index_source = sources.findText(source, QtCore.Qt.MatchFixedString)
             if index_source >= 0:
                 sources.setCurrentIndex(index_source)
             else:
                 print('Source not available!')
             f.close()
             #tableWidget.horizontalHeader().setStretchLastSection(True)
         
         
             
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.change_refs()
    window.show()
    app.exec_()