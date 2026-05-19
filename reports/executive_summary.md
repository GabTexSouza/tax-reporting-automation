# Resumo executivo

Este projeto simulou uma rotina de conferência fiscal mensal com foco em consolidação de notas fiscais, cálculo estimado de tributos e identificação de inconsistências.

## Contexto

Em uma rotina fiscal mensal, arquivos de notas fiscais precisam ser consolidados, revisados e analisados antes do fechamento.

O processo manual em planilhas pode gerar retrabalho, atrasos e maior risco de erro, principalmente quando há múltiplos arquivos mensais e campos fiscais obrigatórios.

## Solução criada

Foi desenvolvido um pipeline em Python para consolidar arquivos mensais de notas fiscais simuladas, calcular valores fiscais estimados e gerar saídas para conferência.

O pipeline gera:

- base fiscal consolidada;
- tabelas resumo por mês;
- tabelas por UF;
- tabelas por CFOP;
- relatório de inconsistências;
- gráficos de análise;
- log de execução.

## Principais análises

A análise permite acompanhar:

- faturamento líquido mensal;
- tributos estimados por mês;
- tributos por UF;
- carga tributária estimada;
- faturamento por CFOP;
- inconsistências fiscais por tipo.

## Valor para o negócio

A automação reduz trabalho manual, melhora a padronização dos dados e facilita a identificação de registros que precisam de revisão.

Além disso, as tabelas e gráficos gerados ajudam a transformar uma rotina operacional em uma visão mais clara para conferência e tomada de decisão.

## Possíveis próximos passos

- Criar validações fiscais mais detalhadas por CFOP e CST.
- Adicionar regras específicas por UF.
- Gerar um relatório em Excel com abas separadas.
- Criar um dashboard em Power BI.
- Agendar a execução automática do pipeline.