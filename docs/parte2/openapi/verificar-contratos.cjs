// Verificação estática complementar ao Redocly. Sem dependências externas.
// Uso, a partir da raiz: node docs/parte2/openapi/verificar-contratos.cjs
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const names = ['editais', 'ofertas', 'compras', 'entregas', 'bff-prefeitura', 'bff-produtor'];
const docs = Object.fromEntries(names.map(name => [name, JSON.parse(fs.readFileSync(path.join(__dirname, name + '.openapi.json'), 'utf8'))]));
const verbs = new Set(['get', 'post', 'patch', 'put', 'delete', 'head', 'options']);
const operations = new Set();
let count = 0;
let links = 0;
let origins = 0;
const resolve = (doc, value) => value?.$ref
  ? value.$ref.slice(2).split('/').reduce((acc, key) => acc[key.replace(/~1/g, '/').replace(/~0/g, '~')], doc)
  : value;
const examples = media => [
  ...(media?.example === undefined ? [] : [media.example]),
  ...Object.values(media?.examples || {}).filter(item => item.value !== undefined).map(item => item.value)
];
function checkLinks(doc, value) {
  if (!value || typeof value !== 'object') return;
  if (value._links && typeof value._links.self?.href === 'string') {
    for (const [rel, item] of Object.entries(value._links)) {
      assert(item.href.startsWith('/'), 'Link deve ser relativo à origem: ' + item.href);
      const prefix = new URL(doc.servers[0].url).pathname;
      assert(item.href.startsWith(prefix + '/'), 'Prefixo de link incorreto: ' + item.href);
      const target = item.href.slice(prefix.length);
      const route = Object.keys(doc.paths).find(route => {
        const segments = route.split('/').map(s => /^\{.+\}$/.test(s) ? '[0-9a-f-]{36}' : s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
        return new RegExp('^' + segments.join('/') + '$').test(target);
      });
      assert(route && doc.paths[route][item.method.toLowerCase()], 'Link sem operação: ' + item.method + ' ' + item.href);
      if (rel === 'confirmar-recebimento') {
        assert(doc === docs['bff-prefeitura'], 'Recebimento só no BFF prefeitura');
        assert.equal(value.status, 'CONFIRMADA');
        assert.equal(value.entrega.status, 'AGENDADA');
      }
      if (rel === 'liberacao-pagamento') assert.equal(value.status, 'RECEBIDA');
      links++;
    }
  }
  for (const item of Object.values(value)) checkLinks(doc, item);
}
for (const [name, doc] of Object.entries(docs)) {
  assert.equal(doc.openapi, '3.1.0');
  assert(doc.security?.length, 'Segurança global ausente');
  const scan = value => {
    if (!value || typeof value !== 'object') return;
    if (value.$ref) {
      assert(value.$ref.startsWith('#/'), 'Contrato deve ser autocontido');
      assert(resolve(doc, value), 'Referência ausente: ' + value.$ref);
    }
    for (const item of Object.values(value)) scan(item);
  };
  scan(doc);
  for (const [route, methods] of Object.entries(doc.paths)) {
    for (const [method, operation] of Object.entries(methods)) {
      if (!verbs.has(method)) continue;
      count++;
      assert(!operations.has(operation.operationId), 'operationId duplicado');
      operations.add(operation.operationId);
      assert(operation['x-papeis']?.length && operation['x-autorizacao'], 'Autorização não documentada');
      const params = (operation.parameters || []).map(p => resolve(doc, p));
      for (const match of route.matchAll(/\{([^}]+)\}/g)) assert(params.some(p => p.name === match[1] && p.in === 'path' && p.required));
      if (method !== 'get') assert(params.some(p => p.name === 'Idempotency-Key' && p.required), 'Escrita sem chave idempotente');
      for (const raw of Object.values(operation.responses)) {
        const response = resolve(doc, raw);
        for (const media of Object.values(response.content || {})) for (const ex of examples(media)) checkLinks(doc, ex);
      }
      if (operation.responses['304']) {
        assert.equal(operation.responses['304'].content, undefined, '304 não pode ter corpo');
        assert(params.some(p => p.name === 'If-None-Match'));
      }
      for (const origin of operation['x-origens'] || []) {
        const service = docs[origin.servico];
        assert(service, 'Origem de domínio desconhecida');
        assert(service.paths[origin.caminho.replace(/^\/api\/v1/, '')]?.[origin.metodo.toLowerCase()], 'Origem sem operação de domínio');
        if (name === 'bff-prefeitura') assert.notEqual(origin.servico, 'ofertas');
        origins++;
      }
      if (name === 'bff-produtor') {
        assert.deepEqual(operation['x-papeis'], ['produtor']);
        assert(!operation.responses['200']?.content?.['application/json']?.example?.paginacao, 'Coleção móvel sem adaptação');
      }
      if (name === 'bff-prefeitura') assert(operation['x-papeis'].every(p => ['gestor', 'escola'].includes(p)));
    }
  }
  console.log(name + ': referências, identidade, rotas e links OK');
}
const requiredOperations = {
  "editais": [
    [
      "post",
      "/prefeituras"
    ],
    [
      "get",
      "/prefeituras/{id}"
    ],
    [
      "post",
      "/escolas"
    ],
    [
      "get",
      "/escolas"
    ],
    [
      "get",
      "/escolas/{id}"
    ],
    [
      "post",
      "/editais"
    ],
    [
      "get",
      "/editais"
    ],
    [
      "get",
      "/editais/{id}"
    ],
    [
      "patch",
      "/editais/{id}"
    ],
    [
      "post",
      "/editais/{id}/publicacoes"
    ],
    [
      "post",
      "/editais/{id}/encerramentos"
    ]
  ],
  "ofertas": [
    [
      "post",
      "/produtores"
    ],
    [
      "get",
      "/produtores/{id}"
    ],
    [
      "patch",
      "/produtores/{id}"
    ],
    [
      "post",
      "/ofertas"
    ],
    [
      "get",
      "/ofertas"
    ],
    [
      "get",
      "/ofertas/{id}"
    ],
    [
      "patch",
      "/ofertas/{id}"
    ],
    [
      "get",
      "/reservas/{id}"
    ]
  ],
  "compras": [
    [
      "post",
      "/propostas"
    ],
    [
      "get",
      "/propostas"
    ],
    [
      "get",
      "/propostas/{id}"
    ],
    [
      "post",
      "/propostas/{id}/retiradas"
    ],
    [
      "post",
      "/planos-alocacao"
    ],
    [
      "get",
      "/planos-alocacao/{id}"
    ],
    [
      "patch",
      "/planos-alocacao/{id}"
    ],
    [
      "post",
      "/planos-alocacao/{id}/homologacoes"
    ],
    [
      "get",
      "/compras"
    ],
    [
      "get",
      "/compras/{id}"
    ],
    [
      "get",
      "/compras/{id}/acompanhamento"
    ],
    [
      "get",
      "/compras/{id}/liberacao-pagamento"
    ]
  ],
  "entregas": [
    [
      "post",
      "/capacidades"
    ],
    [
      "get",
      "/capacidades"
    ],
    [
      "patch",
      "/capacidades/{id}"
    ],
    [
      "get",
      "/entregas"
    ],
    [
      "get",
      "/entregas/{id}"
    ],
    [
      "post",
      "/entregas/{id}/recebimentos"
    ]
  ]
};
let required = 0;
for (const [owner, routes] of Object.entries(requiredOperations)) {
  for (const [method, route] of routes) {
    assert(docs[owner].paths[route]?.[method], "Operação REST ausente em " + owner + ": " + method + " " + route);
    required++;
  }
}
assert(!docs.compras.paths['/compras'].post, 'Não pode criar compra diretamente');
assert.deepEqual(docs.entregas.paths['/entregas/{id}/recebimentos'].post['x-papeis'], ['escola']);
assert(docs['bff-prefeitura'].paths['/dashboard']);
assert(docs['bff-produtor'].paths['/inicio']);
assert(!docs['bff-produtor'].paths['/entregas/{id}/recebimentos']);
const school = docs['bff-prefeitura'].paths['/compras/{id}'].get.responses['200'].content['application/json'].examples;
assert(school.escola.value._links['confirmar-recebimento']);
assert(!school.confirmada.value._links['confirmar-recebimento']);
assert(!school.escolaRecebida.value._links['liberacao-pagamento']);
console.log(`${count} operações; ${required} operações mínimas; ${origins} origens; ${links} links de exemplos verificados.`);
