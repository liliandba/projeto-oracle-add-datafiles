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
