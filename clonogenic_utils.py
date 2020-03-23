import numpy as np

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Functions 
# 	Definitions of functions used in the fitting
def logit(p):
	return np.log(p/(1-p))
def invlogit(a):
	return 1./(1.+np.exp(-a))

def LQ_model( conc, cells_plated, alpha, beta ):
	return cells_plated*np.exp(-alpha*conc-(beta*conc)**2)

def sigmoid_curve( x, sfrac, LC50, slope, nu):
	Q=-1+(1/0.5)**nu
   #return				 1/(1+Q*np.exp(alpha*(np.log(t+1e-18)-np.log(t0  ))))**(1./nu)
	return sfrac + (1-sfrac)/(1+Q*np.exp(slope*(np.log(x+1E-12)-np.log(LC50))) )**(1./nu)

def get_exp_label(df,i_exp):
	row = df.loc[df['i_exp']==i_exp].iloc[0]
	exp_label = "{} {}: {}".format(row['Cell_line'],row['Drug'],row['Plate'])
	return exp_label

def get_exp_index( df, drug, cell_line, rep ):
	mask = (df['Drug']==drug)&(df['Cell_line']==cell_line)
	dft = df[mask].copy()
	plates = dft['plate'].unique()

	return dft[dft['plate']==plates[rep]].iloc[0]['i_exp']

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Trace tools 
#   pull_samples - get postieor samples from a trace

def pull_samples( trace, varnames, nind, nsamp=100):
	''' get samples from the trace oject associated with an experimental unit
	trace: teh trace object
	varnames : [string] a list of the string fo the variabels names
   nind	 : index number for the experimental unit 
	'''
	npost = trace.get_values(varnames[0]).shape[0]
	pulls = np.zeros([npost,len(varnames)])
	for i,var in enumerate(varnames):
		post = trace.get_values(var)
		if( len(post.shape)==2):
			pulls[:,i]=post[:,ni]
		else:
			pulls[:,i]=post
	return np.array(pulls)

def pull_post(  trace,varnames, il=1, nsamp=100):
	post = np.zeros([nsamp,len(varnames)])
	for i,var in enumerate(varnames):
		vals = trace.get_values(var)
		if( i==0 ):
			# first time through make the sampling array
			isamp =np.random.randint(vals.shape[0],size=nsamp)
 
		if( len((vals.shape))==1 ):
			post[:,i]=vals[isamp]
		if( len((vals.shape))==2 ):
			post[:,i]=vals[isamp,il]
	return post

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Plot tools
#   pow2formatter - make a power of 2 axis label
from matplotlib.ticker import FuncFormatter,NullFormatter
def pow2formatter(x,pos):
	if( x==0): return '0'
	if( x==1): return '1'
	if( x>1 ): 
		n = np.round(np.log2(x))
		return r'${x}$'.format(x=int(x))
	if( x<1 ): 
		n = -np.round(np.log2(x))
		return r'$\frac{{1}}{{{x}}}$'.format(x=int(1/x))

def set_pow2format(ax,locs):
	formatter = FuncFormatter(pow2formatter)
	ax.xaxis.set_major_formatter(formatter);
	ax.xaxis.set_minor_formatter(NullFormatter())
	ax.set_xticks(locs);	

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def perc_plot( ax, x, samp,mask=None, **kwargs  ):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   if( mask is None): mask = range(len(x))
   percs = np.percentile( samp, [2.5,25,50,75,97.5], axis=0)
   ax.fill_between( x[mask], percs[0,mask],percs[4,mask], alpha=0.2, **kwargs )
   ax.fill_between( x[mask], percs[1,mask],percs[3,mask], alpha=0.5, **kwargs )
   ax.plot( x[mask], percs[2,mask], lw=1.5, **kwargs )
   return




def posterior_comp( ax, df, trace, ind):
	''''''
	# get the experimental unit
	dft = df[df['i_exp']==ind].copy()
	dft.sort_values('Treatment',inplace=True)

	ax.plot(dft['Treatment'],dft['Count'],'o')


	pulls = pull_post(trace,'PE alpha beta'.split(),ind)
	
	xp = np.array([0]+np.power(10,np.linspace(-5,2,61)))
	nsamp=400
	samps = np.zeros([nsamp,len(xp)])
	cp = np.median(dft['Cells Plated'])
	for i in range(nsamp):
		ir = np.random.randint(pulls.shape[0])
		samps[i] =LQ_model(xp, cp*pulls[ir,0],pulls[ir,1],pulls[ir,2])
	perc_plot(ax,xp,samps,color='red')
	
def posterior_comp_sigmoid( ax, df, trace, ind):
	# get the experimental unit
	dft = df[df['i_exp']==ind].copy()
	dft.sort_values('Treatment',inplace=True)

	ax.plot(dft['Treatment'],dft['Count'],'o')


	pulls = pull_post(trace,'PE sfrac LC50 slope nu'.split(),ind)
	
	xp = np.array([0]+np.power(10,np.linspace(-5,2,61)))
	nsamp=400
	samps = np.zeros([nsamp,len(xp)])
	cp = np.median(dft['Cells Plated'])
	for i in range(nsamp):
		ir = np.random.randint(pulls.shape[0])
		samps[i] =cp*pulls[ir,0]*sigmoid_curve(xp,*pulls[ir,1:])
	perc_plot(ax,xp,samps,color='red')

def var_comp(ax, df, trace,var, drugs=None, label=True,label_plate=False,legend=None):
	'''Compare a variable across the drug treatemetns
	'''
	if( drugs is None):	drugs = df['Drug'].unique()
	cell_lines = df['Cell_line'].unique()
	
	#cdict={"PEO4":'green','PEO1':'blue'}
	cdict=dict(zip(df['Cell_line'].unique(),'blue green orange red'.split()))
	pulls = trace.get_values(var)
	i=0
	locs=[]
	for iid,drug in enumerate(drugs):
		istart=i
		for cell_line in cell_lines:
			mask = (df['Drug']==drug)&(df['Cell_line']==cell_line)
			dft= df[mask].copy()

			i_exps = dft['i_exp'].unique()
			plate = int(dft['plate'].values[0])
			for i_exp in i_exps:
				percs=np.percentile(pulls[:,i_exp],[2.5,25,50,75,97.5])
				ax.plot( percs[[0,-1]],[-i,-i],color=cdict[cell_line],lw=1)
				ax.plot( percs[[1,-2]],[-i,-i],color=cdict[cell_line],lw=3)
				if( label_plate):
					ax.annotate("{}".format(plate),(0.05,-i),xycoords=('axes fraction','data'))
				i=i+1
			i=i+1
		if(iid%2==0 ): ax.axhspan(-(istart-0.5),-(i-0.5),alpha=0.1,color='grey')

		locs.append(-(i+istart)/2.)
	#if( label ):
	#	ax.annotate('{}'.format(drug),(-0.1,(i+istart)/2.),ha='right',va='center',xycoords=('axes fraction','data'))
	i=i+1
	if( label):
		ax.set_yticks(locs)
		ax.set_yticklabels(drugs)
	else:
		ax.yaxis.set_ticklabels([])
	if( legend is not None ):
		from matplotlib.lines import Line2D
		custom_lines = [Line2D([0,1], [0,0], color=col, lw=1) for col in cdict.values()]
		ax.legend(custom_lines,cdict.keys(),loc=legend)

def var_comp_level1(ax, df, trace,var, transform=lambda x: x, drugs=None, label=True, legend=None):
	''' creates a comparison plot by drug for level 1 (group means) comparison
	ax : axis to plot on
	df : dataframe of the raw data
	trace : trace object from MCMC (level2 heierachical model assumed)
	transform : the function to transform back from scale used for inference (normal) to measurement scale
				default is identity function
	drugs : optional, order the drugs by this list list
	label : label the y axis with the drug name
	legend : add the cell line legend sue location string eg "upper right")
	'''
	if( drugs is None ): drugs = df['Drug'].unique()

	# color the cell lines	
	cell_lines = df['Cell_line'].unique()
	cdict=dict(zip(df['Cell_line'].unique(),'blue green orange red'.split()))
	
	# construct the level0 means from the level2 mean and level 1 delta
	p2 = trace.get_values(	var+'_l2')
	p1 = trace.get_values('d'+var+'_l1')
	n1,n2 = p1.shape
	#				   reshape the means (create Ngroup copies )
	# transform to the native scale 
	pulls=transform(p1+np.broadcast_to( p2, (n2,n1)).T)
	
	i=0
	ylabel_locs=[]
	for iid,drug in enumerate(drugs):	
		istart=i
		for ic,cell_line in enumerate(cell_lines):
			mask = (df['Drug']==drug)&(df['Cell_line']==cell_line)
			dft= df[mask].copy()
			i_dc=dft['i_drugcell'].values[0]
			percs=np.percentile(pulls[:,i_dc],[2.5,25,50,75,97.5])
			ax.plot([percs[0],percs[-1]],[-i,-i],color=cdict[cell_line])
			ax.plot([percs[1],percs[-2]],[-i,-i],color=cdict[cell_line],lw=4)
			i=i+1
		   
		if(iid%2==0 ): ax.axhspan(-(istart-0.5),-(i-0.5),alpha=0.1,color='grey')
		ylabel_locs.append(-(istart+i)/2.+0.5)
	ax.set_yticks(ylabel_locs)
	if( label):
		ax.set_yticklabels(drugs)
	else:
		ax.set_yticklabels([])

	if( legend is not None ):
		from matplotlib.lines import Line2D
		custom_lines = [Line2D([0,1], [0,0], color=col, lw=1) for col in cdict.values()]
		ax.legend(custom_lines,cdict.keys(),loc=legend)
	return ylabel_locs,drugs
