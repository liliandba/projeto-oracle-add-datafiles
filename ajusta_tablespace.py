#script ajusta_tablespace.py

import cx_Oracle
import db_config

con = cx_Oracle.connect(db_config.user, db_config.pw, db_config.dsn)

def executar():
	cur = con.cursor()
	cur.execute("""
			select  a.tablespace_name tbs_name, 1 -- este 1 eh gambiarra para format do nome da tablespace saindo da tupla. 
				from 	DBA_TABLESPACE_USAGE_METRICS a, 
					dba_tablespaces b
				where a.tablespace_name=b.tablespace_name
				/* abaixo, definicao do threshold. Podera ser ajustada no python. */
				and a.USED_PERCENT >1 
				and b.contents='PERMANENT'  
				and b.bigfile='NO'
		   """)
	print("\n STATUS: \n Iniciando a adicao de datafiles. \n") 			   
	for t_tbs_name , t_gambiarra in cur:
	    v_sql= ("alter tablespace  {} add datafile ".format(t_tbs_name))
	    #print (v_sql) 
	    #cur.execute (v_sql) 
	    print (" ajustada a tablespace {} com sucesso. ".format(t_tbs_name)) 
