<h1 align="center" style="font-weight: bold;">
  CampoConecta
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/GCC129-Sistemas_Distribu%C3%ADdos-1F6FEB?style=for-the-badge" alt="GCC129 — Sistemas Distribuídos" />
  <img src="https://img.shields.io/badge/Per%C3%ADodo-2026%2F2-2EA44F?style=for-the-badge" alt="Período 2026/2" />
  <img src="https://img.shields.io/badge/Status-Em_desenvolvimento-DBAB09?style=for-the-badge" alt="Status: em desenvolvimento" />
  <img src="https://img.shields.io/badge/Lei_11.947%2F2009-PNAE-0B7285?style=for-the-badge" alt="Lei 11.947/2009 — PNAE" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Microsservi%C3%A7os-4_servi%C3%A7os-6F42C1?style=for-the-badge" alt="4 microsserviços" />
  <img src="https://img.shields.io/badge/Database_per_Service-1_banco_por_servi%C3%A7o-6F42C1?style=for-the-badge" alt="Database per service" />
  <img src="https://img.shields.io/badge/API_Gateway-Routing-6F42C1?style=for-the-badge" alt="API Gateway" />
  <img src="https://img.shields.io/badge/BFF-2_clientes-6F42C1?style=for-the-badge" alt="2 BFFs" />
  <img src="https://img.shields.io/badge/SAGA-Compensa%C3%A7%C3%B5es-6F42C1?style=for-the-badge" alt="SAGA" />
  <img src="https://img.shields.io/badge/CQRS-Leitura_e_Escrita-6F42C1?style=for-the-badge" alt="CQRS" />
  <img src="https://img.shields.io/badge/Outbox-Eventos-6F42C1?style=for-the-badge" alt="Padrão Outbox" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose" />
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" alt="Kubernetes" />
  <img src="https://img.shields.io/badge/OpenAPI-6BA539?style=for-the-badge&logo=openapiinitiative&logoColor=white" alt="OpenAPI" />
  <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain" />
  <img src="https://img.shields.io/badge/RAG-Base_vetorial-8B5CF6?style=for-the-badge" alt="RAG" />
  <img src="https://img.shields.io/badge/LLM-Como_servi%C3%A7o_distribu%C3%ADdo-8B5CF6?style=for-the-badge" alt="LLM como serviço distribuído" />
</p>

## 🌱 Sobre o Projeto

O CampoConecta é o sistema distribuído desenvolvido como Trabalho Prático da disciplina GCC129 (Sistemas Distribuídos, 2026/2). O objetivo da disciplina é que cada grupo constitua uma startup fictícia e desenvolva, ao longo do semestre, um sistema distribuído completo que resolva um problema real com impacto social identificável.

Neste projeto, a startup conecta produtores da agricultura familiar a prefeituras e escolas, viabilizando o cumprimento da cota mínima de 30% de compras institucionais exigida pela Lei do PNAE (Lei nº 11.947/2009).

## 🧩 O Problema

A Lei nº 11.947/2009 exige que ao menos 30% dos recursos do FNDE para merenda escolar sejam usados na compra de produtos da agricultura familiar. Apesar disso, cumprir essa cota está longe de ser trivial.

O próprio FNDE monitora as compras desde 2011 através do sistema SigPC, alimentado pelos gestores municipais e estaduais [1], e chegou a publicar um manual de dez passos só para orientar como comprar da agricultura familiar, incluindo o que fazer quando a chamada pública não acontece [2]. Isso já indica que o processo não é simples nem para quem o desenhou.

Um estudo sobre três municípios mineiros (Divinópolis, Guapé e Lavras) mostra que a compra da agricultura familiar vai muito além de conhecer a lei: gestores despreparados e agricultores desorganizados dificultam o acesso às chamadas públicas [3]. Pesquisas mais recentes relacionam esse desempenho desigual à capacidade administrativa de cada prefeitura [4]. Do lado da oferta, cooperativas de agricultura familiar também enfrentam dificuldades de acesso a esse mercado institucional, dado o número de agentes envolvidos no processo [5].

Existe, portanto, uma lacuna operacional real entre a obrigação legal e a capacidade prática de municípios e produtores executarem esse processo. É essa lacuna que o CampoConecta se propõe a resolver.

**📚 Referências**

1. FNDE. Dados da Agricultura Familiar. Disponível em: https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/programas/pnae/consultas/pnae-dados-da-agricultura-familiar
2. FNDE. Caderno de Compras da Agricultura Familiar para o PNAE. Disponível em: https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/programas/pnae/manuais-e-cartilhas/CadernoDeComprasAF_PNAE.pdf
3. Agricultura familiar e alimentação escolar: desafios para o acesso aos mercados institucionais em três municípios mineiros. SciELO. Disponível em: https://www.scielo.br/j/resr/a/BCkzGpHFdqbMChDYbTkcV4F/?lang=pt
4. Capacidades estatais municipais como condicionantes do desempenho das compras da agricultura familiar no âmbito do PNAE. SciELO. Disponível em: https://www.scielo.br/j/resr/a/sZF4VhcBZGBZ8F4d9k9dZbR/?format=pdf&lang=pt
5. As Cooperativas de Agricultura Familiar e o Mercado de Compras Governamentais em Minas Gerais. SciELO. Disponível em: https://www.scielo.br/j/resr/a/8DRytyzwCn4f84zpSpxVN8h/?format=html&lang=pt&ilang=en

## 🤝 Impacto Social

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

## 🚀 Visão Geral da Solução

Em desenvolvimento pela equipe responsável.

## 👥 Integrantes

<table align="center">
  <tr>
    <td align="center" width="33%">
      <a href="https://github.com/camidebem">
        <img src="https://avatars.githubusercontent.com/u/80923475?v=4" width="100px" alt="Camily Gonçalves de Bem" /><br />
        <sub><b>Camily Gonçalves de Bem</b></sub>
      </a>
    </td>
    <td align="center" width="33%">
      <a href="https://github.com/Clofender">
        <img src="https://avatars.githubusercontent.com/u/73314533?v=4" width="100px" alt="Daniel Silva Ferraz Neto" /><br />
        <sub><b>Daniel Silva Ferraz Neto</b></sub>
      </a>
    </td>
    <td align="center" width="33%">
      <a href="https://github.com/zector1">
        <img src="https://avatars.githubusercontent.com/u/137319815?v=4" width="100px" alt="José Victor Miranda de Oliveira" /><br />
        <sub><b>José Victor Miranda de Oliveira</b></sub>
      </a>
    </td>
  </tr>
</table>
