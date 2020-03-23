import numpy as np 

def multilabel_encoder(df,labels,delim='_##_'):
	'''Creates a unique index for a set of labels in a dataframe
	A generalisation of sklearn LabelEncoder'''
	# string merge the label to create a hashable set of labels
	mrg_lab=df[labels[0]].astype(str)
	for label in labels[1:]:
		mrg_lab+=delim+df[label].astype(str)

	# create a dictionary for labels with labels as key and 0..N and values
	unique_lab=mrg_lab.unique()
	ucode=dict(zip(unique_lab,range(len(unique_lab))))
	return [ ucode[v] for v in mrg_lab],mrg_lab # reverse encode labels

def embeded_index( df, col1, col2):
	'''returns the index arrays that surjectivily maps col1 into col2
	* col1 must have more distinct elements than col2
	* each unique element col1 must to 1 element of col2
	* every element of col2 mapped ()
	'''
	# check that there are less elements in col2
	ncol1 = len(df[col1].unique())
	ncol2 = len(df[col2].unique())		  
	if( ncol1 < ncol2):
		raise Exception('col {} has more elements than col {}'.format(col1,col2))
	
	# make unique combinations
	delim='_##_'
	i_lab, u_lab = multilabel_encoder(df,[col1,col2],delim=delim)
	#return u_lab
	if( ncol1< len(u_lab.unique())):
		print( u_lab)
		raise Exception('col1 maps to multiple elements in col2')	
	# get the list of unique label mappings
	KV = np.array([list(map(int,lab.split(delim))) for lab in u_lab.unique() ]).T
	
	# just in case col1 is not sorted
	isort = np.argsort(KV[0])
	return KV[1,isort]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def add_2level_hierarchy( var,var_dict, lv2_mu,lv2_sd, lv1_sd, lv0_sd, index, dist='halfnorm'):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	'''add a 2-level heirachical variable set for 'var' in pymc3
	 var	  : name of the variable
	 var_dict : the dictionary used to store the theano variabale for pymc3 in
	lv2_mu	 : mean of the groups means					 \ controls prior for the group location
	 lv2_sd   : standard deviation of the mean of the means  /
	lv1_sd   : prior for spread in the group means (betwen group variation)
	lv0_sd   : prior for spread within groups
	index	: embedding index


	  	
	 level 0			  level 1				  level 2

	 var	   
	 variable vector	  
					  index 
	 var_0  =  dvar_0	 0  ---/---dvar_l1_0		\
	var_1  =  dvar_1	 0  --/  /-dvar_l1_1		|  var_l2  
	var_2  =  dvar_2	 1  ----/				   |		  
	var_3  =  dvar_3	 1  ----/  dvar_l1_N1   /
	...			 
	var_N0 =  dvar_N0						  
	
	 Priors:
			   lv0_sd			  lvl1_sd			  lvl2_mu
														     lvl2_sd 
	'''
	import pymc3 as pm

	var_l2 = var+'_l2'
	var_dict[var_l2]   = pm.Normal	(var_l2 ,mu=lv2_mu,sd=lv2_sd)
	
	
	dvar_l1 = 'd'+var+'_l1'; dvar_l1c  = dvar_l1 +'c'
	dvar_l1s = dvar_l1+'s' ; dvar_l1sc = dvar_l1s+'c'

	n1 = len(np.unique(index))
	var_dict[dvar_l1s] = pm.HalfNormal   ( dvar_l1s,	   sd=lv1_sd  )
	
	#var_dict[dvar_l1s] = pm.Exponential   ( dvar_l1s,	   lam=lv1_sd  ) 
	var_dict[dvar_l1 ] = pm.Deterministic( dvar_l1,  var_dict[dvar_l1s]*pm.Normal(dvar_l1c,mu=0,sd=1,shape=n1) )
	 
	
	dvar_l0 = 'd'+var+'_l0'; dvar_l0c  = dvar_l0 +'c'
	dvar_l0s = dvar_l0+'s' ; dvar_l0sc = dvar_l0s+'s'
	n2 = len(index)
	if( dist=='halfnorm'):
		var_dict[dvar_l0s] = pm.Deterministic( dvar_l0s,		lv0_sd			*pm.HalfNormal( dvar_l0sc,sd=1,shape=n1)  )	
	if( dist=='gamma'):
		var_dict[dvar_l0s] = pm.Gamma   ( dvar_l0s,	 mu=lv0_sd, sd=lv0_sd*0.7 ,shape=n1  )   
	#var_dict[dvar_l0s] = pm.Deterministic( dvar_l0s,		lv0_sd			*pm.Exponential( dvar_l0sc,1,shape=n1)  )	

	var_dict[dvar_l0 ] = pm.Deterministic( dvar_l0,  var_dict[dvar_l0s][index]*pm.Normal(dvar_l0c,mu=0,sd=1,shape=n2) )
	
	var_dict[var] =pm.Deterministic(var, var_dict[var_l2] + var_dict[dvar_l1][index]+var_dict[dvar_l0])
