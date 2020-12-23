#script verifica_maxsize.py 
 
import cx_Oracle
import db_config

con = cx_Oracle.connect(db_config.user, db_config.pw, db_config.dsn)

def verificar():
	cur = con.cursor()
	cur.execute(""" select a.valor_medio -  b.parametrizado 
			from 
				(select round (avg(maxbytes/1024/1024/1024)) as valor_medio 
					from dba_data_files) a, 
				(select round (( avg(block_size) * 4194303 ) /1024/1024/1024) parametrizado 
					from dba_tablespaces 
					where CONTENTS='PERMANENT') b 
			 """)
	for t_maxsize in cur:  
		v_maxsize=int(t_maxsize[0])  #t_qtd eh do tipo tupla. Precisa converter para usar o if 
		if (v_maxsize == 0):
			return True	
		else:
			return False


