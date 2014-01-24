#!/usr/bin/env python

import sys,os,argparse,pickle,re




#*************************************************************************************************************** 
#*   Log of change                                                                                             *
#*   January 16, 2014  - George Weingart - george.weingart@gmail.com                                           *
#*                                                                                                             *
#*   biom Support                                                                                              *
#*   Modified the program to enable it to accept biom files as input                                           *
#*                                                                                                             *
#*   Added two optional input parameters:	                                                                   *
#*   1. biom_c is the name of the biom metadata to be used as class                                            *
#*   2. biom_s is the name of the biom metadata to be used as subclass                                         *
#*   class and subclass are used in the same context as the original                                           *
#*   parameters class and subclass                                                                             *
#*   These parameters are totally optional, the default is the program                                         *
#*   chooses as class the first metadata received from the conversion                                          *
#*   of the biom file into a sequential (pcl) file as generated by                                             *
#*   breadcrumbs, and similarly, the second metadata is selected as                                            *
#*   subclass.                                                                                                 *
#*   The syntax or logic for the original non-biom case was NOT changed.                                       *
#*                                                                                                             *
#*   <*******************  IMPORTANT NOTE   *************************>                                         *
#*   The biom case requires breadcrumbs and therefore there is a                                               *
#*      a conditional import of the breadcrumbs modules                                                        *
#*   If the User uses a biom input and breadcrumbs is not detected,                                            *
#*       the run is abnormally ended                                                                           *
#*   breadcrumbs itself needs a biom environment, so if the immport                                            *
#*       of biom in breadcrumbs fails,  the run is also abnormally 
#*       ended (Only if the input file was biom)                                                               *
#*                                                                                                             *
#*   USAGE EXAMPLES                                                                                            *
#*   --------------                                                                                            *
#*   Case #1: Using a sequential file as input (Old version - did not change                                   *
#*  ./format_input.py hmp_aerobiosis_small.txt hmp_aerobiosis_small.in -c 1 -s 2 -u 3 -o 1000000               * 
#*   Case #2: Using a biom file as input                                                                       *
#*  ./format_input.py hmp_aerobiosis_small.biom hmp_aerobiosis_small.in  -o 1000000                            *
#*   Case #3: Using a biom file as input and override the class and subclass                                   *
#*   ./format_input.py lefse.biom hmp_aerobiosis_small.in -biom_c oxygen_availability -biom_s body_site -o 1000000
#*                                                                                                             *
#***************************************************************************************************************         

def read_input_file(inp_file, CommonArea):

	if inp_file.endswith('.biom'):   			#*  If the file format is biom: 
		CommonArea = biom_processing(inp_file)  #*  Process in biom format 
		return CommonArea 						#*  And return the CommonArea

	with open(inp_file) as inp:
		CommonArea['ReturnedData'] = [[v.strip() for v in line.strip().split("\t")] for line in inp.readlines()]
		return CommonArea

def transpose(data):
	return zip(*data)

def read_params(args):
	parser = argparse.ArgumentParser(description='LEfSe formatting modules')
	parser.add_argument('input_file', metavar='INPUT_FILE', type=str, help="the input file, feature hierarchical level can be specified with | or . and those symbols must not be present for other reasons in the input file.")
	parser.add_argument('output_file', metavar='OUTPUT_FILE', type=str,
		help="the output file containing the data for LEfSe")
	parser.add_argument('--output_table', type=str, required=False, default="",
		help="the formatted table in txt format")
	parser.add_argument('-f',dest="feats_dir", choices=["c","r"], type=str, default="r",
		help="set whether the features are on rows (default) or on columns")
	parser.add_argument('-c',dest="class", metavar="[1..n_feats]", type=int, default=1,
		help="set which feature use as class (default 1)")	
	parser.add_argument('-s',dest="subclass", metavar="[1..n_feats]", type=int, default=None,
		help="set which feature use as subclass (default -1 meaning no subclass)")
	parser.add_argument('-o',dest="norm_v", metavar="float", type=float, default=-1.0,
		help="set the normalization value (default -1.0 meaning no normalization)")
	parser.add_argument('-u',dest="subject", metavar="[1..n_feats]", type=int, default=None,
		help="set which feature use as subject (default -1 meaning no subject)")
	parser.add_argument('-m',dest="missing_p", choices=["f","s"], type=str, default="d",
		help="set the policy to adopt with missin values: f removes the features with missing values, s removes samples with missing values (default f)")
	parser.add_argument('-n',dest="subcl_min_card", metavar="int", type=int, default=10,
		help="set the minimum cardinality of each subclass (subclasses with low cardinalities will be grouped together, if the cardinality is still low, no pairwise comparison will be performed with them)")

	parser.add_argument('-biom_c',dest="biom_class", type=str, 
		help="For biom input files: Set which feature use as class  ")		
	parser.add_argument('-biom_s',dest="biom_subclass", type=str, 
		help="For biom input files: set which feature use as subclass   ")
	
	args = parser.parse_args()
	
	return vars(args)	

def remove_missing(data,roc):
	if roc == "c": data = transpose(data)
	max_len = max([len(r) for r in data])
	to_rem = []
	for i,r in enumerate(data):
		if len([v for v in r if not( v == "" or v.isspace())]) < max_len: to_rem.append(i)
	if len(to_rem):
		for i in to_rem.reverse():
			data.pop(i)
	if roc == "c": return transpose(data)
	return data

                                                                                                                                      
def sort_by_cl(data,n,c,s,u):           
	def sort_lines1(a,b): 
        	return int(a[c] > b[c])*2-1                                                                                           
	def sort_lines2u(a,b):        
        	if a[c] != b[c]: return int(a[c] > b[c])*2-1                                                                  
		return int(a[u] > b[u])*2-1
	def sort_lines2s(a,b):        
        	if a[c] != b[c]: return int(a[c] > b[c])*2-1                                                                  
		return int(a[s] > b[s])*2-1
	def sort_lines3(a,b):      
        	if a[c] != b[c]: return int(a[c] > b[c])*2-1                                                                   
		if a[s] != b[s]: return int(a[s] > b[s])*2-1                                                                          
		return int(a[u] > b[u])*2-1 
        if n == 3: data.sort(sort_lines3)                                                                                  
        if n == 2: 
	  if s is None: 
	    data.sort(sort_lines2u)
	  else:
	    data.sort(sort_lines2s)
        if n == 1: data.sort(sort_lines1)                                                                                  
	return data  

def group_small_subclasses(cls,min_subcl):
	last = ""
	n = 0
	repl = []
	dd = [list(cls['class']),list(cls['subclass'])]
	for d in dd:
		if d[1] != last:
			if n < min_subcl and last != "":
				repl.append(d[1])
			last = d[1]
		n = 1	
	for i,d in enumerate(dd):
		if d[1] in repl: dd[i][1] = "other"
		dd[i][1] = str(dd[i][0])+"_"+str(dd[i][1])
	cls['class'] = dd[0]
	cls['subclass'] = dd[1]
	return cls		

def get_class_slices(data):
        previous_class = data[0][0]
        previous_subclass = data[0][1]
        subclass_slices = []
        class_slices = []
        last_cl = 0     
        last_subcl = 0                                                                                                                 
        class_hierarchy = []
        subcls = []                                                                                                                    
        for i,d in enumerate(data):
                if d[1] != previous_subclass:                                                                                          
                        subclass_slices.append((previous_subclass,(last_subcl,i)))
                        last_subcl = i                                                                                                 
                        subcls.append(previous_subclass)                                                                               
                if d[0] != previous_class:                                                                                             
                        class_slices.append((previous_class,(last_cl,i)))                                                              
                        class_hierarchy.append((previous_class,subcls))                                                                
                        subcls = [] 
                        last_cl = i     
                previous_subclass = d[1]
                previous_class = d[0]
        subclass_slices.append((previous_subclass,(last_subcl,i+1)))
        subcls.append(previous_subclass)
        class_slices.append((previous_class,(last_cl,i+1)))                                                                            
        class_hierarchy.append((previous_class,subcls))
        return dict(class_slices), dict(subclass_slices), dict(class_hierarchy)

def numerical_values(feats,norm):
	mm = []
	for k,v in feats.items():
		feats[k] = [float(val) for val in v]
	if norm < 0.0: return feats
	tr = zip(*(feats.values()))
	mul = []
	fk = feats.keys()
	hie = True if sum([k.count(".") for k in fk]) > len(fk) else False
	for i in range(len(feats.values()[0])):
		if hie: mul.append(sum([t for j,t in enumerate(tr[i]) if fk[j].count(".") < 1 ]))
		else: mul.append(sum(tr[i]))
	if hie and sum(mul) == 0:
		mul = []
		for i in range(len(feats.values()[0])):
			mul.append(sum(tr[i]))
	for i,m in enumerate(mul):
		if m == 0: mul[i] = 0.0
		else: mul[i] = float(norm) / m
	for k,v in feats.items():
		feats[k] = [val*mul[i] for i,val in enumerate(v)]
	return feats

def add_missing_levels2(ff):
	
	if sum( [f.count(".") for f in ff] ) < 1: return ff
	
	dn = {}

	added = True
	while added:
		added = False
		for f in ff:
			lev = f.count(".")
			if lev == 0: continue
			if lev not in dn: dn[lev] = [f]
			else: dn[lev].append(f)	
		for fn in sorted(dn,reverse=True):
			for f in dn[fn]:
				fc = ".".join(f.split('.')[:-1])
				if fc not in ff:
					ab_all = [ff[fg] for fg in ff if (fg.count(".") == 0 and fg == fc) or (fg.count(".") > 0 and fc == ".".join(fg.split('.')[:-1]))]
					ab =[]
					for l in [f for f in zip(*ab_all)]:
						ab.append(sum([float(ll) for ll in l]))
					ff[fc] = ab
					added = True
			if added:
				break
		
	return ff
				
				
def add_missing_levels(ff):
	if sum( [f.count(".") for f in ff] ) < 1: return ff
	
	clades2leaves = {}
	for f in ff:
		fs = f.split(".")
		if len(fs) < 2:
			continue
		for l in range(len(fs)):
			n = ".".join( fs[:l] )
			if n in clades2leaves:
				clades2leaves[n].append( f )
			else:
				clades2leaves[n] = [f]
	for k,v in clades2leaves.items():
		if k and k not in ff:
			ff[k] = [sum(a) for a in zip(*[[float(fn) for fn in ff[vv]] for vv in v])]
	return ff

			

def modify_feature_names(fn):
	ret = fn

	for v in [' ',r'\$',r'\@',r'#',r'%',r'\^',r'\&',r'\*',r'\"',r'\'']:
                ret = [re.sub(v,"",f) for f in ret]
        for v in ["/",r'\(',r'\)',r'-',r'\+',r'=',r'{',r'}',r'\[',r'\]',
		r',',r'\.',r';',r':',r'\?',r'\<',r'\>',r'\.',r'\,']:
                ret = [re.sub(v,"_",f) for f in ret]
        for v in ["\|"]:
                ret = [re.sub(v,".",f) for f in ret]
	
	ret2 = []
	for r in ret:
		if r[0] in ['0','1','2','3','4','5','6','7','8','9']:
			ret2.append("f_"+r)
		else: ret2.append(r)	
				
	return ret2 
		

def rename_same_subcl(cl,subcl):
	toc = []
	for sc in set(subcl):
		if len(set([cl[i] for i in range(len(subcl)) if sc == subcl[i]])) > 1:
			toc.append(sc)
	new_subcl = []
	for i,sc in enumerate(subcl):
		if sc in toc: new_subcl.append(cl[i]+"_"+sc)
		else: new_subcl.append(sc)
	return new_subcl
	
	
#*************************************************************************************
#*  Modifications by George Weingart,  Jan 15, 2014                                  *
#*  If the input file is biom:                                                       *
#*  a. Load an AbundanceTable (Using breadcrumbs)                                    *
#*  b. Create a sequential file from the AbundanceTable (de-facto - pcl)             *
#*  c. Use that file as input to the rest of the program                             *
#*  d. Calculate the c,s,and u parameters, either from the values the User entered   *
#*     from the meta data values in the biom file or set up defaults                 * 
#*  <<<-------------  I M P O R T A N T     N O T E ------------------->>            *
#*  breadcrumbs src directory must be included in the PYTHONPATH                     *
#*  <<<-------------  I M P O R T A N T     N O T E ------------------->>            *	
#*************************************************************************************	
def biom_processing(inp_file):
	CommonArea = dict()			#* Set up a dictionary to return
	CommonArea['abndData']   = AbundanceTable.funcMakeFromFile(inp_file,	#* Create AbundanceTable from input biom file
		cDelimiter = None,
		sMetadataID = None,
		sLastMetadataRow = None,
		sLastMetadata = None,
		strFormat = None)

	#****************************************************************
	#*  Building the data element here                              *
	#****************************************************************
	ResolvedData = list()		#This is the Resolved data that will be returned
	IDMetadataName  = CommonArea['abndData'].funcGetIDMetadataName()   #* ID Metadataname 
	IDMetadata = [CommonArea['abndData'].funcGetIDMetadataName()]  #* The first Row
	for IDMetadataEntry in CommonArea['abndData'].funcGetMetadataCopy()[IDMetadataName]:  #* Loop on all the metadata values
		IDMetadata.append(IDMetadataEntry)
	ResolvedData.append(IDMetadata)					#Add the IDMetadata with all its values to the resolved area
	for key, value in  CommonArea['abndData'].funcGetMetadataCopy().iteritems(): 
		if  key  != IDMetadataName:
			MetadataEntry = list()		#*  Set it up
			MetadataEntry.append(key)	#*	And post it to the area
			for x in value:
				MetadataEntry.append(x)		#* Append the metadata value name
			ResolvedData.append(MetadataEntry)
	for AbundanceDataEntry in    CommonArea['abndData'].funcGetAbundanceCopy(): 		#* The Abundance Data
		lstAbundanceDataEntry = list(AbundanceDataEntry)	#Convert tuple to list
		ResolvedData.append(lstAbundanceDataEntry)			#Append the list to the metadata list
	CommonArea['ReturnedData'] = 	ResolvedData			#Post the results 
	return CommonArea   

	
#*******************************************************************************
#*    Check the params and override in the case of biom                        *
#*******************************************************************************
def  check_params_for_biom_case(params, CommonArea):
	CommonArea['MetadataNames'] = list()			#Metadata  names
	params['original_class'] = params['class']			#Save the original class
	params['original_subclass'] = params['subclass']	#Save the original subclass	
	params['original_subject'] = params['subject']	#Save the original subclass	


	TotalMetadataEntriesAndIDInBiomFile = len(CommonArea['abndData'].funcGetMetadataCopy())  # The number of metadata entries
	for i in range(0,TotalMetadataEntriesAndIDInBiomFile): 	#* Populate the meta data names table
		CommonArea['MetadataNames'].append(CommonArea['ReturnedData'][i][0])	#Add the metadata name
	

	#****************************************************
	#* Setting the params here                          *
	#****************************************************
	
	if TotalMetadataEntriesAndIDInBiomFile > 0:		#If there is at least one entry - has to be the subject
		params['subject'] =  1
	if TotalMetadataEntriesAndIDInBiomFile == 2:		#If there are 2 - The first is the subject and the second has to be the metadata, and that is the class
		params['class'] =  2
	if TotalMetadataEntriesAndIDInBiomFile == 3:		#If there are 3:  Set up default that the second entry is the class and the third is the subclass
		params['class'] =  2
		params['subclass'] =  3
		FlagError = False								#Set up error flag

		if not params['biom_class'] is None and not params['biom_subclass'] is None:				#Check if the User passed a valid class and subclass
			if  params['biom_class'] in CommonArea['MetadataNames']:
				params['class'] =  CommonArea['MetadataNames'].index(params['biom_class']) +1	#* Set up the index for that metadata
			else:
				FlagError = True
			if  params['biom_subclass'] in  CommonArea['MetadataNames']:
				params['subclass'] =  CommonArea['MetadataNames'].index(params['biom_subclass']) +1 #* Set up the index for that metadata
			else:
				FlagError = True
		if FlagError == True:		#* If the User passed an invalid class
			print "**Invalid biom class or subclass passed - Using defaults: First metadata=class, Second Metadata=subclass\n"
			params['class'] =  2
			params['subclass'] =  3
	return params
 	
	

if  __name__ == '__main__':
	CommonArea = dict()			#Build a Common Area to pass variables in the biom case
	params = read_params(sys.argv)

	#*************************************************************
	#* Conditionally import breadcrumbs if file is a biom file   *
	#* If it is and no breadcrumbs found - abnormally exit       *
	#*************************************************************
	if  params['input_file'].endswith('.biom'):
		try:
			from lefsebiom.ConstantsBreadCrumbs import *	 
			from lefsebiom.AbundanceTable import *
		except ImportError:
			sys.stderr.write("************************************************************************************************************ \n")
			sys.stderr.write("* Error:   Breadcrumbs libraries not detected - required to process biom files - run abnormally terminated * \n")
			sys.stderr.write("************************************************************************************************************ \n")
			exit(1)

	
	if type(params['subclass']) is int and int(params['subclass']) < 1:
		params['subclass'] = None
	if type(params['subject']) is int and int(params['subject']) < 1:
		params['subject'] = None


	CommonArea = read_input_file(sys.argv[1], CommonArea)		#Pass The CommonArea to the Read
	data = CommonArea['ReturnedData']					#Select the data

	if sys.argv[1].endswith('biom'):	#*	Check if biom:
		params = check_params_for_biom_case(params, CommonArea)	#Check the params for the biom case

	if params['feats_dir'] == "c":
		data = transpose(data)

	ncl = 1
	if not params['subclass'] is None: ncl += 1	
	if not params['subject'] is None: ncl += 1	

	first_line = zip(*data)[0]
	
	first_line = modify_feature_names(list(first_line))

	data = zip(	first_line,
			*sort_by_cl(zip(*data)[1:],
			  ncl,
			  params['class']-1,
			  params['subclass']-1 if not params['subclass'] is None else None,
			  params['subject']-1 if not params['subject'] is None else None))
#	data.insert(0,first_line)
#	data = remove_missing(data,params['missing_p'])
	cls = {}

	cls_i = [('class',params['class']-1)]
	if params['subclass'] > 0: cls_i.append(('subclass',params['subclass']-1))
	if params['subject'] > 0: cls_i.append(('subject',params['subject']-1))
	cls_i.sort(lambda x, y: -cmp(x[1],y[1]))
	for v in cls_i: cls[v[0]] = data.pop(v[1])[1:]
	if not params['subclass'] > 0: cls['subclass'] = [str(cl)+"_subcl" for cl in cls['class']]
	
	cls['subclass'] = rename_same_subcl(cls['class'],cls['subclass'])
#	if 'subclass' in cls.keys(): cls = group_small_subclasses(cls,params['subcl_min_card'])
	class_sl,subclass_sl,class_hierarchy = get_class_slices(zip(*cls.values()))
    
	feats = dict([(d[0],d[1:]) for d in data])
    
	feats = add_missing_levels(feats)
    
	feats = numerical_values(feats,params['norm_v'])
	out = {}
	out['feats'] = feats
	out['norm'] = params['norm_v'] 
	out['cls'] = cls
	out['class_sl'] = class_sl
	out['subclass_sl'] = subclass_sl
	out['class_hierarchy'] = class_hierarchy

	if params['output_table']:
		with open( params['output_table'], "w") as outf: 
			if 'class' in cls: outf.write( "\t".join(list(["class"])+list(cls['class'])) + "\n" )
			if 'subclass' in cls: outf.write( "\t".join(list(["subclass"])+list(cls['subclass'])) + "\n" )
			if 'subject' in cls: outf.write( "\t".join(list(["subject"])+list(cls['subject']))  + "\n" )
			for k,v in out['feats'].items(): outf.write( "\t".join([k]+[str(vv) for vv in v]) + "\n" )

	with open(params['output_file'], 'wb') as back_file:
		pickle.dump(out,back_file)    	

