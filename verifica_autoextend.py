#script verifica_autoextend.py 
 
import cx_Oracle
import db_config

con = cx_Oracle.connect(db_config.user, db_config.pw, db_config.dsn)

def verificar():
	cur = con.cursor()
	cur.execute("""select distinct count(*) 
			from gv$parameter  
			where name ='db_create_file_dest'   
			and value is not null """)
	for t_qtd_omf in cur:  
		v_qtd_omf=int(t_qtd_omf[0])  #t_qtd eh do tipo tupla. Precisa converter para usar o if 
		if (v_qtd_omf == 1):
			return True
		else:
			return False	

[oracle@oracle11g-xe-vagrant projeto-oracle-add-datafiles]$ cat verifica_autoextend.py
#script verifica_autoextend.py 
 
# variavel de controle 

import cx_Oracle
import db_config

con = cx_Oracle.connect(db_config.user, db_config.pw, db_config.dsn)

################ VERIFICA AUTOEXTEND  
def verificar():
	cur = con.cursor()
	cur.execute("""select a.qtd - b.autoext 
		from 
		/* abaixo, num. de datafiles existentes */ 
		( select count(a.file_name)  qtd
			from dba_data_files a, dba_tablespaces b 
			where a.tablespace_name=b.tablespace_name 
			and b.contents='PERMANENT'  
			and b.bigfile='NO') a, 
		/* abaixo, verificando qtos datafiles estao em autoextend=on */
		( select count(a.autoextensible)  autoext
			from dba_data_files a, dba_tablespaces b 
			where a.tablespace_name=b.tablespace_name 
				and b.contents='PERMANENT' 
				and b.bigfile='NO'
				and autoextensible='YES') b  """)
				
	for t_autoextent in cur:  
		v_autoextent=int(t_autoextent[0])  #t_qtd eh do tipo tupla. Precisa converter para usar o if 
		if (v_autoextent == 0):
			return True
		else:
			return False 

