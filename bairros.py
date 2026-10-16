# bairros

def bairros (entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'bairros' AS tipo_registro,
                MD5(CONCAT(bairro.id_municipio, bairro.bairro)) as HASH,	   
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(bairro.id_municipio, bairro.bairro)),     
                        'content',					 	                  
                            JSON_OBJECT(
                                    'nome', bairro.bairro,									                 
                                'municipio', JSON_OBJECT('id', CAST(bairro.id_municipio AS SIGNED))
                            )
                ) AS js,
                JSON_OBJECT('id_municipio', bairro.id_municipio, 'bairro', bairro.bairro)
        FROM (SELECT 
                        (SELECT reg.id 
                        FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'municipios'
                            AND reg.JSON_store->>'$.content.uf' = ender.unidade_federacao
                            AND reg.JSON_store->>'$.content.nome' = ender.cidade) AS 'id_municipio',
                        ender.bairro
                FROM credores ender 
                WHERE ender.bairro IS NOT NULL 
                GROUP BY id_municipio, bairro ) AS bairro 
        WHERE bairro.id_municipio IS NOT NULL AND 
                NOT EXISTS(SELECT 1 
                            FROM registro_lotes reg 
                            WHERE reg.tipo_registro = 'bairros'
                                    AND reg.JSON_store->>'$.content.nome' = bairro.bairro
                                        AND reg.JSON_store->>'$.content.municipio.id' = bairro.id_municipio)
    """
    return sql
    