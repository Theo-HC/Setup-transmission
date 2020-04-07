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

directory='data/'
data_dictionary={}
for filename in os.listdir(directory):
    if filename.endswith(".h5"):
        f=h5.File(directory+filename,'r')
        file_keys=[key.decode('utf-8') for key in f['Ref']]
        data_dictionary.update(dict.fromkeys(file_keys,filename))
        f.close()
        continue
    else:
        continue

try:
    os.mkdir(os.getcwd()+'/results/')
except:
    pass
    
def return_data(ref, dataset):
    f=h5.File(directory+data_dictionary[ref],'r')
    data=np.array(f[dataset])
    f.close()
    return np.min(data[:,0]),np.max(data[:,0]),interp1d(data[:,0],data[:,1]/100)

def calculate_transmission(tableWidget,ResolutionGraph):
    numrows = tableWidget.rowCount()
    min_wl=0
    max_wl=1e6
    transmission_interpolations=[]
    occurences=[]
    for i in range(numrows):
        ref=tableWidget.item(i,0).text()
        dataset=tableWidget.item(i,1).text()
        occurence=int(tableWidget.item(i,2).text())
        if occurence!=0:                    
            occurences+=[occurence]
            
            min_temp,max_temp,interp=return_data(ref,dataset)
            
            if min_temp>min_wl:
                min_wl=min_temp
            if max_temp<max_wl:
                max_wl=max_temp
                
            transmission_interpolations+=[interp]
    x_transmission=np.arange(min_wl,max_wl+ResolutionGraph,ResolutionGraph)
    transmission=np.ones(x_transmission.shape)
    for i in range(numrows):
        transmission*=transmission_interpolations[i](x_transmission)**occurences[i]
    return x_transmission,transmission

class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("select_components.ui", self)
        refs=list(data_dictionary.keys())
        refs.sort()
        self.comboBox_refs.addItems(refs)
        
        self.comboBox_refs.currentIndexChanged.connect(self.change_refs)
        self.pushButton_addComponent.clicked.connect(self.add_components)
        self.pushButton_plot.clicked.connect(self.plot_transmission)
        self.pushButton_clearTable.clicked.connect(self.clear_table)
        self.pushButton_save.clicked.connect(self.save)
        
    def change_refs(self):
        filename=data_dictionary[self.comboBox_refs.currentText()]
        f=h5.File(directory+filename,'r')
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
        x_transmission,transmission=calculate_transmission(tableWidget,np.float(self.lineEdit_ResolutionGraph.text()))
        
        fig=plt.figure()
        ax=fig.add_subplot(111)
        ax.plot(x_transmission,transmission,'b-')
        plt.show()
             
    def clear_table(self):
        self.tableWidget_components.setRowCount(0)
    
    def save(self):         
         filename,extension = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Transmission', os.getcwd()+'/results/Transmission.h5', '.h5')
         tableWidget=self.tableWidget_components
         numrows=tableWidget.rowCount()
         parameters=[[tableWidget.item(i,j).text() for j in range(3)] for i in range(numrows)]
         parameters=np.array(parameters,dtype='S')
         f=h5.File(filename,'w')
         f.create_dataset("Components", data=parameters)
         x_transmission,transmission=calculate_transmission(tableWidget,np.float(self.lineEdit_ResolutionGraph.text()))
         f.create_dataset("Transmission", data=np.vstack((x_transmission,transmission)).T)
         f.close()
             
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.change_refs()
    window.show()
    app.exec_()