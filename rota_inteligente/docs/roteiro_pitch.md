# Roteiro do vídeo pitch (até 4 minutos)

> Dica: deixe abertos antes de gravar o terminal na pasta do projeto, o `README.md` no GitHub e o `outputs/mapa_rotas.svg` no navegador.

**0:00–0:30 | Apresentação e problema.** Olá! Sou Felipe Cavalcante Marinho, do curso GTI. Este é o projeto Rota Inteligente, para a empresa fictícia Sabor Express. Hoje as rotas são definidas na experiência dos entregadores, e nos horários de pico isso gera atrasos, mais combustível e clientes insatisfeitos.

**0:30–1:05 | Modelagem.** Transformei a região em um grafo: 25 pontos, que são cruzamentos e locais de entrega, ligados por 40 ruas. Cada rua tem um peso, que é o tempo estimado em minutos. Tudo vem de arquivos CSV, com dados fictícios. *(Mostrar o mapa: depósito amarelo, entregas azuis, números nas ruas.)*

**1:05–2:00 | IA e algoritmos.** São três etapas. Primeiro, o K-Means, aprendizado não supervisionado, agrupa os oito pedidos em zonas, uma por entregador. Segundo, o A\* calcula o caminho de menor tempo entre cada par de paradas, usando a distância em linha reta como heurística, que nunca superestima o custo. Para validar, comparo com Dijkstra, que dá sempre o mesmo resultado, e com BFS e DFS, que mostram que menos ruas ou um caminho qualquer não significam menor tempo. Terceiro, testo todas as ordens possíveis de visita em cada grupo e escolho a mais rápida.

**2:00–3:05 | Demonstração.** *(Terminal)* `python -m src.main --entregadores 2`. O entregador 1 tinha uma rota de 62 minutos na ordem de chegada dos pedidos; trocando a ordem de duas entregas, caiu para 50. O entregador 2 já estava na ordem ótima. No total, de 94 para 82 minutos: 12,8% de economia. Na comparação de buscas, A\* e Dijkstra empatam no custo, mas o A\* expande menos nós; o BFS gasta 4 minutos a mais e o DFS até seis vezes mais. *(Abrir o mapa e mostrar as cores dos entregadores.)* Por fim, `python -m unittest discover -s tests -v`: 14 testes passando, incluindo A\* igual a Dijkstra em todos os 625 pares de nós.

**3:05–3:45 | Resultados e limites.** Com um único entregador a otimização economiza 61%, porque a ordem de chegada cruza o mapa várias vezes. Mas um achado importante: como o K-Means agrupa só por distância, colocar mais motos quase não reduz o tempo da maior rota. Também não considero trânsito real, capacidade das motos nem horário prometido. Como evolução, usaria mapas reais do OpenStreetMap, trânsito em tempo real e um modelo de roteamento com capacidade e janelas de tempo.

**3:45–4:00 | Encerramento.** O repositório público tem o código, os dados, os testes, os resultados e a documentação. Obrigado!

## Publicação
Grave a tela com narração (OBS Studio ou Xbox Game Bar no Windows: `Win + Alt + R`), confira se tem **no máximo 4 minutos**, publique no YouTube como **não listado** ou público, cole o link no `README.md` e envie para avaliação.
