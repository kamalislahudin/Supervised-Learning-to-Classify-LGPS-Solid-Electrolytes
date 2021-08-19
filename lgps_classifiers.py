# -*- coding: utf-8 -*-
"""LGPS Classifiers.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LzCKzRViDJ26uQMYp1-y4tXuVOLmbFVF

# Preparation
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import mean_squared_error as mse
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_validate
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import VotingClassifier
from sklearn.feature_selection import RFECV
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import RandomForestClassifier
import seaborn as sns
import matplotlib.pyplot as plt

data_path = 'C:/Users/muhak/OneDrive - Institut Teknologi Bandung/ML/DATASET/LGPS_DATASET_NEW.csv'
initial_data = pd.read_csv(data_path)

#Drop unnecessary columns
initial_data = initial_data.drop(['source','formula','conductivity','sub_element','temperature'], axis=1)
initial_data.head()

#Define value for X (features)  and y (target propertie)
X = initial_data.drop('good_cond', axis=1)
y = initial_data['good_cond']

"""# EDA"""

#Check the balance of the dataset

sns.countplot(initial_data['good_cond'],label="Sum")

plt.show()

#Using Pearson correlation to check the correlation between each features and the target propertie
correlation = initial_data.corr()

mask = np.zeros_like(correlation, dtype=np.bool)
mask[np.triu_indices_from(mask)] = True

f, ax = plt.subplots(figsize=(20, 20))

cmap = sns.diverging_palette(180, 20, as_cmap=True)
sns.heatmap(correlation, mask=mask, cmap=cmap, vmax=1, vmin =-1, center=0,
            square=True, linewidths=.5, cbar_kws={"shrink": .5}, annot=True)

plt.show()

#Check the missing value on the dataset
missing_values_count = initial_data.isnull().sum()
missing_values_count

"""# Model Building"""

#Split the dataset into train set and test set
X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.25)

#LazyClassifier Phase
from lazypredict.Supervised import LazyClassifier

lcl = LazyClassifier(verbose=0,ignore_warnings=True, custom_metric=None)
models, predictions = lcl.fit(X_train, X_test, y_train, y_test)

# Get the list of the methods' names
modellist = list(models.index.values) 

Nrep = 1000 # Number of replications, the higher the better
r2score = np.zeros((len(modellist),Nrep)) # Initialize the r2score
position = np.zeros((len(modellist),Nrep)) # Initialize the position (rank)
for LOOP in range(0,Nrep):

    #Using LazyRegressor for cut dataset
    clf = LazyClassifier(verbose=0, ignore_warnings=True, custom_metric=None)
    modelstemp, predictionstemp = clf.fit(X_train, X_test, y_train, y_test)
 
    modellisttemp = list(modelstemp.index.values)
    
    for i, mdl in zip(range(0,len(modellist)),modellist):
        search_pos = int(modellisttemp.index(models.index.values[i]))
        r2score[i,LOOP] = modelstemp.iloc[:,0][search_pos]
        position[i,LOOP] = search_pos

idx = np.argmax(np.mean(r2score, axis=1))
print('The best model according to the mean acc. score is ',modellist[idx],'with score',max(np.mean(r2score,axis=1)))
idx = np.argmax(np.median(r2score,axis=1))
print('The best model according to the median acc. score is ',modellist[idx],'with score',max(np.median(r2score,axis=1)))
idx = np.argmin(np.mean(position,axis=1))
print('The best model according to the mean ranking is ',modellist[idx],'with score',min(np.mean(position,axis=1)))
idx = np.argmin(np.median(position,axis=1))
print('The best model according to the median ranking is ',modellist[idx],'with score',min(np.median(position,axis=1)))

modellist_df = pd.DataFrame(modellist).rename(columns = {0:'Model'})
mean_df = pd.DataFrame(np.mean(r2score, axis = 1)).rename(columns = {0:'Accuracy mean'})
med_df = pd.DataFrame(np.median(r2score, axis = 1)).rename(columns = {0:'Accuracy median'})
rankmean_df = pd.DataFrame(np.mean(position, axis = 1)).rename(columns = {0:'Rank mean'})
rankmed_df = pd.DataFrame(np.median(position, axis = 1)).rename(columns = {0:'Rank median'})
models_df = pd.concat([modellist_df, mean_df, rankmean_df, med_df, rankmed_df], axis = 1)
models_df.sort_values(['Accuracy mean', 'Accuracy median'], ascending = False).head(30)

"""# Model Optimization"""

import optuna
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import LeaveOneOut
from numpy import mean
from numpy import std

def LOO_cross_val (X, y, model):
    cvpred = np.zeros([len(X)]) #Creating array of zeros as big as the length of X
    Xnp = X.to_numpy() #Converts feature set to np array
    ynp = y.to_numpy() #Converts target property to numpy
    for i in range(0,len(X)):
        xpred = Xnp[i,:].reshape(1,-1) #Define X_val
        XLOO = np.delete(Xnp,i,axis=0) #Define X_train
        yLOO = np.delete(ynp,i).reshape(-1,1) #Define y_train
        modelLOO = model #Define model
        modelLOO.fit(XLOO, yLOO) #Fitting model to training set
        cvpred[i] = modelLOO.predict(xpred) #Adding predict score to array of zeros
    LOOCVscore = np.sum(cvpred == ynp)/len(X)
    return LOOCVscore

classifier = BaggingClassifier()
score_bg = LOO_cross_val(X, y, classifier) 
#scores = cross_val_score(classifier, X, y, scoring='accuracy', cv=cv, n_jobs=-1)
print('Accuracy: %.3f' % (mean(score_bg)))

classifier = RandomForestClassifier()
score_rf = LOO_cross_val(X, y, classifier) 
#scores = cross_val_score(classifier, X, y, scoring='accuracy', cv=cv, n_jobs=-1)
print('Accuracy: %.3f' % (mean(score_rf)))

classifier = ExtraTreesClassifier()
score_et = LOO_cross_val(X, y, classifier)  
#scores = cross_val_score(classifier, X, y, scoring='accuracy', cv=cv, n_jobs=-1)
print('Accuracy: %.3f' % (mean(score_dt)))

def objective_bg(trial):
    n_estimators_bg= trial.suggest_int('n_estimators',10,100)
   
    classifier = BaggingClassifier(random_state = None,
                                       n_estimators=n_estimators_bg)
    
    score = LOO_cross_val(X, y, classifier)                            
    return score

study_bg = optuna.create_study(direction="maximize")
study_bg.optimize(objective_bg, n_trials=100, n_jobs = -1)
print(study_bg.best_trial, '\n')

print('The best hyperparameters for BaggingClassifier:\n{}\n'.format(study_bg.best_params))
print('The best leave-one-out cross-validation score for BaggingClassifier:\n{}\n'.format(study_bg.best_value))

def objective_rf(trial):
    bootstrap_rf=trial.suggest_categorical('bootstrap', [True, False])
    max_features_rf=trial.suggest_categorical('max_features',['auto','sqrt'])
    min_samples_leaf_rf= trial.suggest_int('min_samples_leaf',1,5)
    min_samples_split_rf=trial.suggest_int('min_samples_split',2,10)
    max_depth_rf=trial.suggest_int('max_depth',1,10)
    n_estimators_rf=trial.suggest_int('n_estimators',100,500)
    
    classifier = RandomForestClassifier(random_state = None,
                                       bootstrap=bootstrap_rf,
                                       max_features=max_features_rf,
                                       min_samples_leaf=min_samples_leaf_rf,
                                       min_samples_split=min_samples_split_rf,
                                       max_depth=max_depth_rf,
                                       n_estimators=n_estimators_rf)
                                
    score = LOO_cross_val(X, y, classifier) 
    return score

study_rf = optuna.create_study(direction="maximize")
study_rf.optimize(objective_rf, n_trials=100, n_jobs = -1)
print(study_rf.best_trial, '\n')

print('The best hyperparameters for RandomForestClassifier:\n{}\n'.format(study_rf.best_params))
print('The best leave-one-out cross-validation score for RandomForestClassifier:\n{}\n'.format(study_rf.best_value))

def objective_et(trial):
    n_estimators_et= trial.suggest_int('n_estimators',10,1000)
    min_samples_split_et= trial.suggest_int('min_samples_split',2,15)
   
    classifier = ExtraTreesClassifier(random_state = None,
                                       n_estimators=n_estimators_et,
                                       min_samples_split=min_samples_split_et)
    score = LOO_cross_val(X, y, classifier)                            
    return score

study_et = optuna.create_study(direction="maximize")
study_et.optimize(objective_et, n_trials=100, n_jobs = -1)
print(study_dt.best_trial, '\n')

print('The best hyperparameters for ExtraTreesClassifier:\n{}\n'.format(study_et.best_params))
print('The best cross-validation score for ExtraTreesClassifier:\n{}\n'.format(study_et.best_value))

result = pd.DataFrame({
    'Model'         : ['Bagging', 'Random Forest', 'Extras Tree'],
    'Base Score'    : [mean(score_bg), mean(score_rf), mean(score_et)],
    'Bayesian Opt Score': [study_bg.best_value, study_rf.best_value, study_et.best_value],    
    }, columns = ['Model', 'Base Score', 'Bayesian Opt Score'])

result

"""# Defining The Optimized Best Model"""

#Using decision tree as the best model with the highest score
model_opt= BaggingClassifier(n_estimators= 20)
model_opt.fit(X_train,y_train)

model_opt2=RandomForestClassifier(bootstrap= False, max_features= 'auto', min_samples_leaf= 3, min_samples_split= 6, max_depth= 5, n_estimators= 187)
model_opt2.fit(X,y)

"""# Feature Importance"""

import shap  # package used to calculate Shap values
model = RandomForestClassifier(bootstrap= False, max_features= 'sqrt', min_samples_leaf= 4, min_samples_split= 5, max_depth= 5, n_estimators= 470)
# Fit the Model
model_fit = model.fit(X, y)
shap.initjs()

explainer = shap.TreeExplainer(model_fit)
shap_values = explainer.shap_values(X)

shap.summary_plot(shap_values, features=X, feature_names=X.columns)

shap.summary_plot(shap_values[1], X)

import eli5
from eli5.sklearn import PermutationImportance

perm = PermutationImportance(model_fit, random_state=0).fit(X, y)
eli5.show_weights(perm, feature_names = X.columns.tolist())