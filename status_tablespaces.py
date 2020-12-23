#script status_tablespaces.py

import cx_Oracle
import db_config

con = cx_Oracle.connect(db_config.user, db_config.pw, db_config.dsn)

def listar():
	print(" \n --------- LISTAGEM GERAL DAS TABLESPACES POR ORDEM DE UTILIZACAO  ------------ \n")
	cur = con.cursor()
	cur.execute("""
			select  a.tablespace_name tbs_name, 
					round(a.used_percent) used_percent,
					count(c.file_name) qtd_datafiles, 
					round(a.tablespace_size*b.block_size/1048576) tamanho_atual_MB,	
					/* abaixo, coluna used_space esta em blocos. Por isso a multiplicacao pelo block_size, que esta em kb. */ 
					round(a.used_space*b.block_size/1048576) usado_MB, 
					round(sum(c.maxbytes/1048576)) tamanho_max_possivel_mb 
				from 	DBA_TABLESPACE_USAGE_METRICS a, 
					dba_tablespaces b, 
					dba_data_files c
				where a.tablespace_name=b.tablespace_name
				and a.tablespace_name=c.tablespace_name 
				and b.contents='PERMANENT'  
				and b.bigfile='NO'
				group by a.tablespace_name, 
					round(a.used_space*b.block_size/1048576) , 
					round(a.tablespace_size*b.block_size/1048576), 
					round(a.used_percent) 
				order by 2 desc  
		   """)
		   
	for t_tbs_name, t_used_percent, t_qtd_datafiles, t_tamanho_atual_MB, t_usado_MB, t_tamanho_max_possivel_mb in cur:
	    print(" --------------------- ")
	    print("Tablespace: {}".format(t_tbs_name))
	    print("Uso: {} % ".format( t_used_percent))
	    print("Quantia de Datafiles: {}".format(t_qtd_datafiles))
	    print("Tamanho fisico atual: {} MB".format (t_tamanho_atual_MB))
	    print("Utilizacao Logica atual: {} MB".format (t_usado_MB))
	    print("Tamanho maximo fisico possivel: {} MB".format (t_tamanho_max_possivel_mb)) 

