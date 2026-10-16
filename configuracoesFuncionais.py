# configuracoesFuncionais
# BuscaEhSalvaJsonSistemasContabil(token, url, 'configuracoes-funcionais', conn)

def configuracoesFuncionais_sql (entidade = 1, ano = 2022):
    
    sql = f""" SELECT 'configuracoes-funcionais' AS tipo_registro,
                MD5('MOG - PORTARIA Nº 42/99') as HASH,
                JSON_OBJECT(
                        'idIntegracao', MD5('MOG - PORTARIA Nº 42/99'),
                            'content',
                            JSON_OBJECT(
                                        'descricao', 'MOG - PORTARIA Nº 42/99'
                            )
                    ) AS js  """
    return sql