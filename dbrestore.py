
# Methods to restore the database after the migration. applied by Rick.  
import sys
import pickle
import neuroelectro.models as m
import xlrd
import re
from db_add import add_single_article_full

sys.path.append('code')

def main():
    update_concept_maps()
    update_ephys_defs()
    assign_robot()
    # update_articles() # this one will take a while and prob fail

def prog(num,denom):
    fract = float(num)/denom
    hyphens = int(round(50*fract))
    spaces = int(round(50*(1-fract)))
    sys.stdout.write('\r%.2f%% [%s%s]' % (100*fract,'-'*hyphens,' '*spaces))
    sys.stdout.flush() 

def update_concept_maps():
    ncm_fields, ecm_fields, nedm_fields = load()
    datatables = m.DataTable.objects.all()
    print 'Getting or creating data sources'
    for i,x in enumerate(datatables):
        prog(i,datatables.count())
        m.DataSource.objects.get_or_create(data_table=x)
    
    anon_user = m.get_anon_user()
    robot_user = m.get_robot_user()
    print 'Updating nedm fields'
    for nedm_field in nedm_fields:
        nedm=m.NeuronEphysDataMap.objects.get(pk=nedm_field['pk'])
        data_source = m.DataSource.objects.get(data_table=nedm_field['fields']['data_table'])
        nedm.source = data_source
        if nedm.added_by_old == 'human':
            nedm.added_by = anon_user
        else:
            nedm.added_by = robot_user
        nedm.save()

    print 'Updating ncm fields'
    for ncm_field in ncm_fields:
        ncm=m.NeuronConceptMap.objects.get(pk=ncm_field['pk'])
	data_source = m.DataSource.objects.get(data_table=ncm_field['fields']['data_table'])
	ncm.source = data_source
	if ncm.added_by_old == 'human':
            ncm.added_by = anon_user
	else:
            ncm.added_by = robot_user
	ncm.save()
    
    print 'Updating ecm fields'
    for ecm_field in ecm_fields:
        ecm=m.EphysConceptMap.objects.get(pk=ecm_field['pk'])
	data_source = m.DataSource.objects.get(data_table=ecm_field['fields']['data_table'])
	ecm.source = data_source
	if ecm.added_by_old == 'human':
            ecm.added_by = anon_user
	else:
            ecm.added_by = robot_user
	ecm.save()
	    
def update_ephys_defs():
    print 'Updating ephys defs'
    table, nrows, ncols = load_ephys_defs()
    for i in range(1,nrows):
        ephysProp = table[i][0]
	rawSyns = table[i][2]
	ephysDef = table[i][1]
	unit = table[i][3]
	unit_main = table[i][4]
	unit_sub = table[i][5]
	ephysOb = m.EphysProp.objects.get_or_create(name = ephysProp)[0]
	if unit_main != '':
            u = m.Unit.objects.get_or_create(name = '%s' % unit_main, prefix = '%s' % unit_sub)[0]
	    ephysOb.units = u
	if ephysDef != '':
            ephysOb.definition = ephysDef
	print u.pk,ephysDef
        ephysOb.save()

def assign_robot():
    nams = m.NeuronArticleMap.objects.all()
    u = m.get_robot_user()
    for nam in nams:
        nam.added_by = u
        nam.save()
        
def update_articles():
    print 'Updating articles'
    all_arts = m.Article.objects.all()
    pmid_list = [a.pmid for a in all_arts]
    pmid_list_len = len(pmid_list)
    for i,pmid in enumerate(pmid_list):
        prog(i, pmid_list_len)
        a = m.Article.objects.filter(pmid=pmid)[0]
        if a.author_list_str is None:
            add_single_article_full(pmid)

def load():
    print 'Loading files'
    pkl_file = open('user_contrib_data', 'rb')
    myData = pickle.load(pkl_file)
    pkl_file.close()
    ncm_fields, ecm_fields, nedm_fields = myData
    return (ncm_fields, ecm_fields, nedm_fields)
	
def load_ephys_defs():
    print 'Loading ephys defs'
    book = xlrd.open_workbook("data/Ephys_prop_definitions_3.xlsx")
    #os.chdir('C:\Python27\Scripts\Biophys')
    sheet = book.sheet_by_index(0)
    ncols = sheet.ncols
    nrows = sheet.nrows

    table= [ [ 0 for i in range(ncols) ] for j in range(nrows ) ]
    for i in range(nrows):
        for j in range(ncols):
            table[i][j] = sheet.cell(i,j).value
    return table, nrows, ncols
