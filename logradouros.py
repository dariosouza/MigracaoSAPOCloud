# logradouros
# BuscaEhSalvaJsonSistemasContabil(token, url, 'tipos-logradouros', conn)

def logradouros(entidade = 1, ano = 2022):
    sql = f"""
            SELECT
                    'logradouros' AS tipo_registro,
                    MD5(CONCAT(logr.id_municipio, logr.tipo, logr.endereco, coalesce(logr.cep,''))) as HASH,	   
                    JSON_OBJECT(
                            'idIntegracao', MD5(CONCAT(logr.id_municipio, logr.tipo, logr.endereco, coalesce(logr.cep,''))),     
                                'content',
                                    JSON_MERGE_PRESERVE(
                                    JSON_OBJECT(
                                            'nome', logr.endereco,
                                        'tipo', JSON_OBJECT('id', CAST(logr.tipo AS SIGNED)),
                                        'municipio', JSON_OBJECT('id', CAST(logr.id_municipio AS SIGNED))
                                    ),
                                    if(logr.cep IS NOT NULL AND LENGTH(logr.cep) = 8, JSON_OBJECT('cep', cast(logr.cep AS CHAR)), JSON_OBJECT())
                                )
                        ) AS js,
                        json_object('endereco', logr.endereco, 'cep', logr.cep, 'municipio', id_municipio, 'tipo', logr.tipo ) 		  
                FROM(SELECT 
                        (SELECT reg.id 
                        FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'municipios'
                            AND reg.JSON_store->>'$.content.uf' = ender.unidade_federacao
                            AND reg.JSON_store->>'$.content.nome' = ender.cidade) AS 'id_municipio',
                            
                        coalesce((SELECT MAX(reg.id)
                                        FROM registro_lotes reg
                                    WHERE reg.tipo_registro = 'tipos-logradouros' 
                                            AND (ender.endereco LIKE CONCAT('%',reg.JSON_store->>'$.content.descricao','%')
                                                OR ender.endereco LIKE CONCAT(reg.JSON_store->>'$.content.descricao','%')) ), 		  		  
                                    (SELECT MAX(reg.id)
                                    FROM registro_lotes reg
                                    WHERE reg.tipo_registro = 'tipos-logradouros' 
                                            AND reg.JSON_store->>'$.content.descricao' = 'Rua')) AS 'tipo',

                        left(ender.endereco,50) AS 'endereco',
                        ender.cep
                FROM credores ender 
                WHERE (ender.endereco IS NOT NULL OR ender.endereco != '') 
                        AND ender.cidade IS NOT NULL
                        AND ender.unidade_federacao IS NOT NULL ) AS logr
                WHERE logr.id_municipio IS NOT NULL  
                        AND NOT EXISTS(SELECT 1 
                                         FROM registro_lotes reg
                                   WHERE reg.tipo_registro = 'logradouros'
                                         AND reg.JSON_store->>'$.content.tipo.id' = logr.tipo
                                         AND reg.JSON_store->>'$.content.municipio.id' = logr.id_municipio
                                         AND reg.JSON_store->>'$.content.nome' = logr.endereco)
                GROUP BY logr.id_municipio, logr.tipo, logr.endereco, logr.cep
                    """
    return sql
    
