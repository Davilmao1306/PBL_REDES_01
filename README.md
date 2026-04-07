# IoT Forno - Integracao com sockets TCP/UDP

Este projeto simula uma solucao de Internet das Coisas para desacoplar sensores,
atuadores e aplicacoes cliente. A comunicacao foi implementada diretamente com
sockets da Internet, sem MQTT, AMQP, Kafka, RabbitMQ ou outro framework de troca
de mensagens.

## Arquitetura

- `broker/`: servico de integracao. Mantem o estado conhecido dos dispositivos,
  recebe telemetria dos sensores e encaminha comandos aos atuadores.
- `sensors/`: dispositivos virtuais que geram telemetria continua.
- `actuators/`: dispositivos virtuais que recebem comandos remotos.
- `client/`: aplicacao de terminal para listar dispositivos, monitorar dados em
  tempo real e enviar comandos.
- `shared/`: protocolo textual simples usado por todos os componentes.

O desacoplamento acontece porque sensores e atuadores conhecem apenas o broker.
As aplicacoes cliente tambem conhecem apenas o broker. Assim, um sensor nao
precisa abrir conexoes diretas com painel, banco de dados, alarme ou qualquer
outro consumidor.

## Perfis de trafego

- Telemetria: usa UDP na porta `5001`. Esse caminho prioriza velocidade e baixa
  sobrecarga. Perdas ocasionais sao aceitaveis porque as leituras sao continuas
  e rapidamente substituidas por novas amostras.
- Controle: usa TCP na porta `5002`. Esse caminho prioriza entrega ordenada e
  confiavel para comandos criticos como ligar, desligar ou acionar alarme.

O TCP usa mensagens delimitadas por quebra de linha. Isso e necessario porque
TCP entrega um fluxo de bytes, nao mensagens prontas.

## Execucao com Docker

Suba o broker, sensores e atuadores:

```bash
docker compose up --build broker sensor_temp sensor_fumaca atuador_aquecedor atuador_exaustor
```

Em outro terminal, abra o cliente interativo:

```bash
docker compose run --rm client
```

Opcoes principais do cliente:

- `1`: listar sensores registrados.
- `2`: listar atuadores registrados.
- `5`: enviar comando para atuador.
- `6`: monitorar um sensor em tempo real.

IDs disponiveis na configuracao padrao:

- Sensores: `sensor_temp`, `sensor_fumaca`.
- Atuadores: `atuador_aquecedor`, `atuador_exaustor`.

Comandos aceitos:

- `atuador_aquecedor`: `ON`, `OFF`, `DESLIGAR`.
- `atuador_exaustor`: `ON`, `OFF`, `ACIONAR_ALARME`.

## Roteiro de apresentacao

1. Mostrar o `docker-compose.yml` e explicar que cada componente roda em um
   conteiner separado na mesma rede Docker.
2. Subir broker, sensores e atuadores.
3. Abrir o cliente e listar sensores/atuadores.
4. Monitorar `sensor_temp` ou `sensor_fumaca` em tempo real.
5. Enviar `ON` e `OFF` para `atuador_aquecedor`.
6. Enviar `ACIONAR_ALARME` para `atuador_exaustor`.
7. Explicar que o broker substitui a comunicacao ponto-a-ponto por uma
   arquitetura de integracao centralizada usando apenas TCP e UDP nativos.

## Observacoes de implementacao

O estado fica em memoria no broker porque o objetivo do trabalho e demonstrar
conectividade e integracao. Em um ambiente de producao, esse ponto poderia ser
evoluido com persistencia, autenticacao, TLS, reconexao automatica mais robusta
e historico de telemetria.
