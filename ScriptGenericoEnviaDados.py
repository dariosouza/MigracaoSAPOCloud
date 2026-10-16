import json
import requests
import mysql.connector
from tqdm import tqdm
import logging
import time
from naturezasjuridicas import sqlPrc # pyright: ignore[reportMissingImports]
from programas import programas_sql # type: ignore
from acoes import acoes_sql # type: ignore
from organogramas import organogramas_sql  # type: ignore
from naturezas_despesas import naturezas_despesas_sql  # type: ignore
from recursos import recursos_sql # type: ignore
from naturezas_receitas import naturezas_receitas_sql # type: ignore
from devolucoes_receitas import devolucoes_receitas_sql # type: ignore
from receitas import receitas_sql  # type: ignore
from localizadores import localizadores_sql  # type: ignore
from configuracoesFuncionais import configuracoesFuncionais_sql # type: ignore
from subfuncoes import subfuncoes_sql # type: ignore
from funcoes import funcoes_sql # type: ignore
from grupos_despesas_loa import grupos_despesas_loa_sql # type: ignore
from despesas_loa import despesas_loa_sql
from receitas_nao_previstas import receitas_nao_previstas_sql  # type: ignore
from despesas_nao_previstas import despesas_nao_previstas_sql  # type: ignore
from receitas_extras import receitas_extras_sql  # type: ignore
from receitas_extras_exercicios import receitas_extras_exercicios_sql # type: ignore
from origens_creditos_orcamentarios import origens_creditos_orcamentarios_sql # type: ignore
from origens_creditos_orcamentarios_exercic import origens_creditos_orcamentarios_exercicios_sql # type: ignore
from recursos_superavit_financeiro import recursos_superavit_financeiro
from creditos_orcamentarios import processa_suplementacoes
from creditos_orcamentarios_sancoes import creditos_orcamentarios_sancoes_sql
from transacoes_financeiras import transacoes_financeiras_sql
from bancos import bancos
from contas_bancarias_entidades import contas_bancarias_entidades_sql
from logradouros import logradouros
from bairros import bairros
from credores import credores
from tipos_comprovantes import tipos_comprovantes_sql
from comprovantes import comprovantes
from retencoes import retencoes
from tiposprecatorios import tiposprecatorios
from tipos_dividas import tipos_dividas
from dividas import dividas
from deducoes_receitas import deducoes_receitas
from lancamentos_receitas import processa_lancamento_receita #precisa de revisão 



def busca_dados_data_api_rest(token, url, offset=0, limit=100):
    BASE_URL = url
    HEADERS = {'Authorization': f"""Bearer {token}""",  # Substitua pelo seu token
               'Content-Type': 'application/json',
               'Accept': 'application/json',}
    try:
        params = {'offset': offset, 'limit': limit}
        response = requests.get(BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None
    
def InfoBuscaDadosEntidade(token_migacao): 
    headers = {'Authorization': f'Bearer {token_migacao}'}
    url_info_token = f"https://plataforma-oauth.betha.cloud/auth/oauth2/tokeninfo?access_token={token_migacao}"
    response = requests.get(url_info_token)
    result = response.json()
    if("client" in result):
        attributes = json.loads(result["user"]["attributes"]["singleAccess"])
        entityId = attributes["entityId"]
        response_entidade = requests.get(f"https://e-gov.betha.com.br/glb/service-layer/v2/api/entidades/{entityId}", headers=headers)
        info_entidade =  response_entidade.json()        
        result = {"nome": info_entidade["nome"], "entidade": entityId, "cnpj": info_entidade["cnpj"]}
        try:
            return result
        except Exception as err:
            logging.exception(err)
            raise
    return None

def envio_dados_post(token, sqlinstr, conn, url, maxenvio = 10):
    lotes = []
    cur = conn.cursor(buffered=True)    
    cur.execute(sqlinstr)  
    HEADERS = {
        'Authorization': f"""Bearer {token}""", 
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }      
    with tqdm(total=cur.rowcount, unit='B', unit_scale=True, desc="Envio de Dados..", ncols=120) as pbar:        
        while True:
            jsondata = []
            jsonrefdados = []
            fetch = cur.fetchmany(maxenvio)
            if not fetch:
                break
            for row in fetch:
                pbar.update(1)                
                jsondata.append( json.loads(row[2]) )                
                #(jsonrefdados.append( json.loads(row[3]) ) if row[3] is not None else None)
            time.sleep(6)            
                        
            # response = requests.post(url + row[0], headers=HEADERS, data=json.dumps(jsondata) )
            # jsresult = response.json()            
            # lotes.append({ "idLote": jsresult.get('idLote'), "tipo_registro": row[0], "js": jsondata })
            
            try:
                response = requests.post(
                    url + row[0],
                    headers=HEADERS,
                    data=json.dumps(jsondata),                    
                    timeout=60
                )

                # Verifica se HTTP retornou erro (400, 401, 404, 500 etc.)
                response.raise_for_status()

                try:
                    jsresult = response.json()
                except requests.exceptions.JSONDecodeError:
                    print(f"[ERRO JSON] {row[0]}")
                    print(f"Status: {response.status_code}")
                    print(f"Resposta: {response.text}")
                    continue

                # JSON válido
                lotes.append({
                    "idLote": jsresult.get("idLote"),
                    "tipo_registro": row[0],
                    "js": jsondata,
                    "refdados": jsonrefdados
                })

            except requests.exceptions.RequestException as e:
                print(f"[ERRO HTTP] {row[0]}: {e}")
                continue
            
            
            # if jsresult.get('idLote') is None:
            #     print( json.dumps(jsondata) )
        cur.close()
        curinsert = conn.cursor()
        for lt in lotes:
            if lt.get('tipo_registro') is not None: # and lt.get('idLote') is not None:
                idLote = (lt.get('idLote') if lt.get('idLote') is not None else None)
                tipo_registro = lt.get('tipo_registro')                
                if idLote is not None:
                    curinsert.execute(f"""insert into lotes (lote, tipo_registro, atualizado) values (%s, %s, %s) on duplicate key update lote = %s and tipo_registro = %s""", [idLote, tipo_registro, 'N', idLote, tipo_registro] )                                
                for itx in lt.get('js'):                    
                    jsid = itx.get("idIntegracao")
                    InsertOrUpdate(updatevalues='Y',
                                   table="registro_lotes",
                                   listkeys=['lote', 'tipo_registro', 'idIntegracao'],
                                   dicfieldsValues={'id': None,
                                                    'STATUS': 'NAO_PROCESSADO',
                                                    'mensagem': None,
                                                    'lote': idLote,
                                                    'tipo_registro': tipo_registro,
                                                    'idIntegracao': jsid,
                                                    "JSON_store": json.dumps(itx)},
                                   conn = conn,
                                   chkdupli = True)
        curinsert.close()
        conn.commit()

    # with tqdm(total=len(lotes), unit='B', unit_scale=True, desc="Buscando Lotes..", ncols=120) as pbar:
    #     for idxlotes in lotes:
    #         pbar.update(1)
    #         if idxlotes.get('tipo_registro') is not None and idxlotes.get('idLote') is not None:
    #             time.sleep(3)
    #             processa_registro_lotes(token, conn, idxlotes.get('tipo_registro'), idxlotes.get('idLote') )

def envio_dados_delete(token, sqlinstr, conn, url, maxenvio = 10):
    lotes = []
    cur = conn.cursor(buffered=True)    
    cur.execute(sqlinstr)  
    HEADERS = {
        'Authorization': f"""Bearer {token}""", 
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }      
    with tqdm(total=cur.rowcount, unit='B', unit_scale=True, desc="Envio de Dados para exclusao", ncols=120) as pbar:        
        while True:
            jsondata = []
            fetch = cur.fetchmany(maxenvio)
            if not fetch:
                break
            for row in fetch:
                pbar.update(1)
                jsondata.append( json.loads(row[2]) )
            time.sleep(15)
                        
            # response = requests.post(url + row[0], headers=HEADERS, data=json.dumps(jsondata) )
            # jsresult = response.json()            
            # lotes.append({ "idLote": jsresult.get('idLote'), "tipo_registro": row[0], "js": jsondata })
            
            try:
                response = requests.delete(
                    url + row[0],
                    headers=HEADERS,
                    data=json.dumps(jsondata),
                    timeout=60
                )

                # Verifica se HTTP retornou erro (400, 401, 404, 500 etc.)
                response.raise_for_status()

                try:
                    jsresult = response.json()
                except requests.exceptions.JSONDecodeError:
                    print(f"[ERRO JSON] {row[0]}")
                    print(f"Status: {response.status_code}")
                    print(f"Resposta: {response.text}")
                    continue

                # JSON válido
                lotes.append({
                    "idLote": jsresult.get("idLote"),
                    "tipo_registro": row[0],
                    "js": jsondata
                })

            except requests.exceptions.RequestException as e:
                print(f"[ERRO HTTP] {row[0]}: {e}")
                continue
            
            
            # if jsresult.get('idLote') is None:
            #     print( json.dumps(jsondata) )
        cur.close()
        curinsert = conn.cursor()
        for lt in lotes:
            if lt.get('tipo_registro') is not None: # and lt.get('idLote') is not None:
                idLote = (lt.get('idLote') if lt.get('idLote') is not None else None)
                tipo_registro = lt.get('tipo_registro')
                if idLote is not None:
                    curinsert.execute(f"""insert into lotes (lote, tipo_registro, atualizado) values (%s, %s, %s) on duplicate key update lote = %s and tipo_registro = %s""", [idLote, tipo_registro, 'N', idLote, tipo_registro] )
                for itx in lt.get('js'):
                    jsid = itx.get("idIntegracao")
                    InsertOrUpdate(updatevalues='Y',
                                   table="registro_lotes",
                                   listkeys=['lote', 'tipo_registro', 'idIntegracao'],
                                   dicfieldsValues={'id': None,  'STATUS': 'NAO_PROCESSADO', 'mensagem': None, 'lote': idLote, 'tipo_registro': tipo_registro, 'idIntegracao': jsid, "JSON_store": json.dumps(itx) } ,
                                   conn = conn,
                                   chkdupli = False)
        curinsert.close()
        conn.commit()

def InsertOrUpdate(updatevalues='N', table="", listkeys=[], dicfieldsValues={}, conn = None, chkdupli = True):
        
        filter = ""
        fields = ""
        question = ""
        questupdate = ""
        sql = ""
        result = []
        resultInsert = []   
        resultupdate = []
        
        sqlselect = f"""SELECT 1 FROM {table} WHERE """
        sqlinsert = f"""INSERT INTO {table} ("""
        sqlupdate = f"""UPDATE {table} SET """
        
        for field in dicfieldsValues.keys():
            for key in listkeys:
                if field == key:
                    filter += key + (" = %s" if dicfieldsValues[field] is not None else " is %s") + " and "
                    result.append(dicfieldsValues[field])
            fields += field + ","
            question += "%s,"
            questupdate += field + " = %s, "
            resultInsert.append(dicfieldsValues[field])
                               
        questupdate = questupdate[0:len(questupdate)-2]
        question = question[0:len(question)-1]
        fields = fields[0:len(fields)-1] + ") VALUES (" + question + ");"
        filter = filter[0:len(filter)-5]
        sqlinsert += fields
        sqlselect += filter
        sqlupdate += questupdate + " WHERE " + filter        
        try:
            checkresult = []
            if chkdupli:
                cur = conn.cursor()
                cur.execute(sqlselect, result)
                for row in cur:
                    checkresult.append(row)
                cur.close()
            if len(checkresult) == 0:
                sql = sqlinsert
                curinsert = conn.cursor()
                curinsert.execute(sqlinsert, resultInsert)
                curinsert.close()
            else:
                sql = sqlupdate
                for inser in resultInsert:
                    resultupdate.append(inser)
                for whe in result:
                    resultupdate.append(whe)
                if updatevalues == 'Y':
                    curupdate = conn.cursor()
                    curupdate.execute(sqlupdate, resultupdate)
                    curupdate.close()
        except Exception as err:
            logging.exception(err)
            raise
        return sql

def BuscaEhSalvaJsonSistemasContabil(token, url, tipo_reg, conn):
    offset = 0
    limit = 100    
    hasNext = True
    
    cur = conn.cursor()
    cur.execute(f"""SELECT COALESCE(MAX(OFFSET),0) FROM registro_lotes  WHERE tipo_registro = '{tipo_reg}' AND OFFSET IS NOT NULL""")
    for row in cur.fetchall():
        offset = int(row[0])
    cur.close()
        
    url = f"""{url}{tipo_reg}"""
    with tqdm(total=100000, unit='B', unit_scale=True, desc="Busca de dados..", ncols=120) as pbar:
        while hasNext:            
            dados = busca_dados_data_api_rest(token, url, offset=offset, limit=limit)
            if not dados:
                break
            time.sleep(3)  
                    
            cur = conn.cursor()
            hasNext = dados.get('hasNext')
            for itemdados in dados.get('content', []):                 
                id            = (itemdados["idGerado"]["id"] if "idGerado" in itemdados is not None else itemdados["content"]["id"] )
                status        = 'SUCESSO'
                mensagem      = None
                lote          = None
                tipo_registro = tipo_reg
                idIntegracao  = id
                # cur.execute(f"""insert into registro_lotes (id, status, mensagem, lote, tipo_registro, idIntegracao, json_store) values (%s, %s, %s, %s, %s, %s, %s) """,
                #             [id, status, mensagem, lote, tipo_registro, idIntegracao, json.dumps(itemdados)] )
                InsertOrUpdate( 
                    updatevalues='Y',
                    table='registro_lotes',
                    listkeys=['tipo_registro', 'id'],
                    dicfieldsValues={'id': id,  'STATUS': status, 'mensagem': mensagem, 'lote': lote, 
                                     'tipo_registro': tipo_registro, 'idIntegracao': idIntegracao, 'JSON_store': json.dumps(itemdados), 'offset': offset},
                    conn = conn,
                    chkdupli = True
                )
                pbar.update(1)
            offset += limit 
            cur.close()
            conn.commit()

def processa_registro_lotes(token, url, conn, tipo_registro): 
    js = None    
    urllote = url + "lotes/"
    HEADERS = {
        'Authorization': f"""Bearer {token}""", 
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }      
    cur = conn.cursor(buffered=True)   
    cur.execute("SELECT distinct lote FROM registro_lotes WHERE id IS NULL AND STATUS != 'ERRO' AND lote IS NOT NULL AND tipo_registro = %s", [tipo_registro])    
    with tqdm(total=cur.rowcount, unit='B', unit_scale=True, desc=f"""Buscando Lotes {tipo_registro} .. """, ncols=120) as pbar:
        for row in cur.fetchall():
            pbar.update(1)
            while True:        
                response = requests.get(urllote + row[0] , headers=HEADERS)
                js = response.json()                
                time.sleep(5)
                if js.get('status') not in ('AGUARDANDO_EXECUCAO','NAO_PROCESSADO'):
                    for jsret in js.get('retorno', []):
                        id              = None
                        idIntegracao    = jsret.get('idIntegracao')
                        status          = jsret.get('status')
                        mensagem        = (jsret.get('mensagem') if jsret.get('mensagem') is not None else None)
                        if status == 'SUCESSO':
                            id = jsret.get('idGerado').get('id')
                        if jsret.get('idExistente') is not None:
                            for idx in jsret.get('idExistente'):
                                id = idx
                        InsertOrUpdate( 
                            updatevalues='Y',
                            table="registro_lotes",
                            listkeys=['lote', 'tipo_registro', 'idIntegracao'],
                            dicfieldsValues={'id': id,  'STATUS': status, 'mensagem': mensagem, 'lote': row[0], 'tipo_registro': tipo_registro, 'idIntegracao': idIntegracao},
                            conn = conn,
                            chkdupli = True
                        )
                    conn.commit()
                    break
    cur.close()


if __name__ == "__main__":

    token = "f27bb5d3-7b59-47b4-b10c-a2ed2dfd165c"
    url = "https://con-sl-rest.betha.cloud/contabil/service-layer/v2/api/"
    # url = "https://pla-sl-rest.betha.cloud/planejamento/service-layer/v2/api/"

    infoent = InfoBuscaDadosEntidade(token)
    print( infoent )

    conn = mysql.connector.connect(host='localhost', user='root', password='dario699', database='sapo_pm_tapaua', port=3307)

    sql = processa_lancamento_receita(conn, 1, 2022)

    # envio_dados_delete(token, sql, conn, url, 10 )
    # BuscaEhSalvaJsonSistemasContabil(token, url, 'recursos', conn)
    # envio_dados_post(token, sql, conn, url, 20 )
    # processa_registro_lotes(token, url, conn, 'arrecadacoes-orcamentarias')

    conn.close()