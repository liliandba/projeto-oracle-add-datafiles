#script ajusta_oracle_tablespaces.py 
 
import cx_Oracle
import db_config

con = cx_Oracle.connect(db_config.user, db_config.pw, db_config.dsn)


# variavel de controle 
v_executa=True 

#definicao do threshold
v_threshold=90

################  VERIFICA DB_FILE_DEST CONFIGURADO (OMF) 
cur = con.cursor()
cur.execute("""select distinct count(*) 
		from gv$parameter  
		where name ='db_create_file_dest'   
		and value is not null """)
for t_qtd_omf in cur:  
	v_qtd_omf=int(t_qtd_omf[0])  #t_qtd eh do tipo tupla. Precisa converter para usar o if 
	### print v_qtd_omf  # linha para debug - caso necessario saber o valor de t_qtd_omf 
	if (v_qtd_omf == 1):
		print ('OK: Parametro db_create_file_dest esta corretamente configurado. ') 
	else:
		print ('Falha: Parametro db_create_file_dest nao esta correto. Verificar. ') 
		v_executa=False 

################ VERIFICA AUTOEXTEND  
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
	### print v_autoextent  # linha para debug - caso necessario saber o valor de v_qtd 
	if (v_autoextent == 0):
		print ('OK: Todos os datafiles estao com autoextend on. ') 
	else:
		print ('Falha: ha datafiles com autoextend off. Verificar ') 
		v_executa=False 
 
################ VERIFICA MAXSIZE  
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
	### print v_maxsize  # linha para debug - caso necessario saber o valor de v_maxsize 
	if (v_maxsize == 0):
		print ('OK: Todos os datafiles estao com maxsize unlimited configurados. ') 
	else:
		print ('Falha: ha datafiles com maxsize unlimited descofigurado. Verificar.') 
		v_executa=False 

################  VERIFICA SE Ha TABLESPACES COM O THRESHOLD INDICADO  
while (v_executa==True):
	cur = con.cursor()
	cur.execute(""" select count(a.tablespace_name) 
			from DBA_TABLESPACE_USAGE_METRICS a, dba_tablespaces b 
			where a.USED_PERCENT > :v_1 
			and b.contents='PERMANENT'  
			and b.bigfile='NO' 
			 """,
			 v_1=v_threshold)
	for t_metrics in cur:  
		v_metrics=int(t_metrics[0])  #t_qtd eh do tipo tupla. Precisa converter para usar o if 
		### print v_metrics  # linha para debug - caso necessario saber o valor de v_metrics 
		if (v_metrics == 0):
			print ('OK: Todas as tablespaces estao abaixo do threshold. Nada para ajustar. ') 
			v_executa=False 
		else:
			print ('Atencao: Ha {} tablespaces que serao ajustadas.'.format (v_metrics))
				
	################  VERIFICA QUAL A TABLESPACE DEVERA SER AJUSTADA, COLETANDO SEUS DADOS ANTES PARA LOG
	if (v_executa==True): 
		print(" --------- ABAIXO, TABLESPACE(S) COM CONSUMO ACIMA DO THRESHOLD ------------ ")
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
					/* abaixo, definicao do threshold. Podera ser ajustada no python. */
					and a.USED_PERCENT > 90
					and b.contents='PERMANENT'  
					and b.bigfile='NO'
					group by a.tablespace_name, 
						round(a.used_space*b.block_size/1048576) , 
						round(a.tablespace_size*b.block_size/1048576), 
						round(a.used_percent) 
					order by 2 desc 
			   """)
			   
		for t_tbs_name, t_used_percent, t_qtd_datafiles, t_tamanho_atual_MB, t_usado_MB, t_tamanho_max_possivel_mb in cur:
		    print("Tablespace: {}".format(t_tbs_name))
		    print("Uso: {} % ".format( t_used_percent))
		    print("Quantia de Datafiles: {}".format(t_qtd_datafiles))
		    print("Tamanho fisico atual: {} MB".format (t_tamanho_atual_MB))
		    print("Utilizacao Logica atual: {} MB".format (t_usado_MB))
		    print("Tamanho maximo fisico possivel: {} MB".format (t_tamanho_max_possivel_mb)) 
		    print(" --------------------- \n")
		    
				
				
		################  AJUSTANDO A TABLESPACE   
		cur = con.cursor()
		cur.execute("""
				select  a.tablespace_name tbs_name, 1 -- este 1 eh gambiarra para format do nome da tablespace saindo da tupla. 
					from 	DBA_TABLESPACE_USAGE_METRICS a, 
						dba_tablespaces b
					where a.tablespace_name=b.tablespace_name
					/* abaixo, definicao do threshold. Podera ser ajustada no python. */
					and a.USED_PERCENT > 90
					and b.contents='PERMANENT'  
					and b.bigfile='NO'
			   """)
			   
		for t_tbs_name , t_gambiarra in cur:
		    v_sql= ("alter tablespace  {} add datafile ".format(t_tbs_name))
		    print (v_sql) 
		    cur.execute (v_sql) 
	    


			################	INVESTIGAR ERRO:  ELE ADICIONA APENAS 1 DATAFILE. depois, retorna o erro abaixo: 
			################		Traceback (most recent call last):
			################		  File "<stdin>", line 2, in <module>
			################		cx_Oracle.InterfaceError: not a query


################  VERIFICACAO DE TODAS AS TABLESPACES AO FINAL DO SCRIPT 
# Abaixo eh executado mesmo que nenhum ajuste tenha sido executado. 
if (v_executa==False): 
	print(" --------- LISTAGEM GERAL DAS TABLESPACES POR ORDEM DE UTILIZACAO  ------------ ")
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

