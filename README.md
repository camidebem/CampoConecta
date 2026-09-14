# CampoConecta

## Sobre o Projeto

O CampoConecta é o sistema distribuído desenvolvido como Trabalho Prático da disciplina GCC129 (Sistemas Distribuídos, 2026/2). O objetivo da disciplina é que cada grupo constitua uma startup fictícia e desenvolva, ao longo do semestre, um sistema distribuído completo que resolva um problema real com impacto social identificável.

Neste projeto, a startup conecta produtores da agricultura familiar a prefeituras e escolas, viabilizando o cumprimento da cota mínima de 30% de compras institucionais exigida pela Lei do PNAE (Lei nº 11.947/2009).

## O Problema

A Lei nº 11.947/2009 exige que ao menos 30% dos recursos do FNDE para merenda escolar sejam usados na compra de produtos da agricultura familiar. Apesar disso, cumprir essa cota está longe de ser trivial.

O próprio FNDE monitora as compras desde 2011 através do sistema SigPC, alimentado pelos gestores municipais e estaduais [1], e chegou a publicar um manual de dez passos só para orientar como comprar da agricultura familiar, incluindo o que fazer quando a chamada pública não acontece [2]. Isso já indica que o processo não é simples nem para quem o desenhou.

Um estudo sobre três municípios mineiros (Divinópolis, Guapé e Lavras) mostra que a compra da agricultura familiar vai muito além de conhecer a lei: gestores despreparados e agricultores desorganizados dificultam o acesso às chamadas públicas [3]. Pesquisas mais recentes relacionam esse desempenho desigual à capacidade administrativa de cada prefeitura [4]. Do lado da oferta, cooperativas de agricultura familiar também enfrentam dificuldades de acesso a esse mercado institucional, dado o número de agentes envolvidos no processo [5].

Existe, portanto, uma lacuna operacional real entre a obrigação legal e a capacidade prática de municípios e produtores executarem esse processo. É essa lacuna que o CampoConecta se propõe a resolver.

**Referências**

1. FNDE. Dados da Agricultura Familiar. Disponível em: https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/programas/pnae/consultas/pnae-dados-da-agricultura-familiar
2. FNDE. Caderno de Compras da Agricultura Familiar para o PNAE. Disponível em: https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/programas/pnae/manuais-e-cartilhas/CadernoDeComprasAF_PNAE.pdf
3. Agricultura familiar e alimentação escolar: desafios para o acesso aos mercados institucionais em três municípios mineiros. SciELO. Disponível em: https://www.scielo.br/j/resr/a/BCkzGpHFdqbMChDYbTkcV4F/?lang=pt
4. Capacidades estatais municipais como condicionantes do desempenho das compras da agricultura familiar no âmbito do PNAE. SciELO. Disponível em: https://www.scielo.br/j/resr/a/sZF4VhcBZGBZ8F4d9k9dZbR/?format=pdf&lang=pt
5. As Cooperativas de Agricultura Familiar e o Mercado de Compras Governamentais em Minas Gerais. SciELO. Disponível em: https://www.scielo.br/j/resr/a/8DRytyzwCn4f84zpSpxVN8h/?format=html&lang=pt&ilang=en

## Impacto Social

O CampoConecta gera impacto direto em três frentes principais:

- **Produtores familiares:** ganham acesso simplificado e desburocratizado a um mercado institucional estável, garantindo escoamento da produção e previsibilidade de renda.
- **Alunos da rede pública:** passam a receber uma alimentação escolar mais diversa, fresca e nutritiva, cumprindo o propósito original da legislação.
- **Prefeituras:** conseguem sair da situação de não conformidade legal com a cota do PNAE, reduzindo o esforço administrativo e burocrático.

Para acompanhar a efetividade da solução, o impacto social pode ser medido por meio das seguintes métricas:

- Percentual de chamadas públicas efetivamente preenchidas na região de atuação.
- Tempo médio entre a publicação do edital e a entrega efetiva dos alimentos nas escolas.
- Número de produtores certificados participando ativamente do sistema ao longo do tempo.
- Aumento no volume de compras da agricultura familiar realizadas por municípios parceiros.
- Índice de satisfação de escolas, gestores e produtores em relação ao processo de compra e entrega.

## Visão Geral da Solução

O CampoConecta atua como uma ponte direta entre a oferta (produtores locais) e a demanda legal obrigatória (prefeituras e escolas), atacando as falhas de comunicação e organização do modelo atual. O sistema foca no fluxo de negócio prático para os usuários, operando da seguinte forma:  

Publicação de Demanda: A prefeitura cadastra e publica um edital de chamada pública detalhando os itens necessários, quantidades e prazos.  

Propostas: Os produtores familiares cadastrados visualizam os editais compatíveis com a sua produção e enviam suas propostas diretamente pela plataforma.  

Alocação: O sistema realiza a distribuição das compras entre os produtores, respeitando a capacidade produtiva de cada um e os critérios definidos no edital.  

Logística: A entrega dos alimentos é agendada e, posteriormente, confirmada fisicamente na escola recebedora.  

Pagamento: Após a confirmação do recebimento da mercadoria, o sistema libera o pagamento ao produtor.

## Integrantes

* Camily Gonçalves de Bem
* Daniel Silva Ferraz Neto
* Jose Victor Miranda de Oliveira
