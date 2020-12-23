#script add_datafiles.py 

import verifica_omf
import verifica_autoextend
import verifica_maxsize
import ajusta_tablespace
import status_tablespaces

# variavel de controle 
v_executa=True

# variavel para ajuste de mensagem ao final do script 
v_status=[]



#### INICIO DA EXECUCAO ####

#  VERIFICA DB_FILE_DEST CONFIGURADO (OMF) 
if (verifica_omf.verificar())==False:
	v_status.append ("OMF nao configurado")
	v_executa=False	

# VERIFICA AUTOEXTEND  
if (verifica_autoextend.verificar())==False:
	v_status.append ("AUTOEXTEND NAO CONFIGURADO")
	v_executa=False	

# VERIFICA MAXSIZE  
if (verifica_maxsize.verificar())==False:
	v_status.append ("MAXSIZE UNLIMITED NAO CONFIGURADO")
        v_execute=False

# AJUSTANDO A TABLESPACE   
if (v_executa==True): 
	ajusta_tablespace.executar()   
else:
	print ("\n STATUS:\n Nao foram executados ajustes.")
	print ("{} \n".format (v_status))



#### FINAL DA EXECUCAO ####

# VERIFICACAO DE TODAS AS TABLESPACES AO FINAL DO SCRIPT 
# Abaixo eh executado mesmo que nenhum ajuste tenha sido executado. 
status_tablespaces.listar() 
print ("\n") 

