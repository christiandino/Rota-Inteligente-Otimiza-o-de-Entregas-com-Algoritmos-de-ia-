# Como publicar no GitHub (passo a passo)

1. Entre em https://github.com/new e crie um repositório **Public** chamado `rota-inteligente-sabor-express` (não marque "Add a README", o projeto já tem um).
2. No terminal, dentro da pasta `rota_inteligente`:

```bash
git init
git add .
git commit -m "Rota Inteligente: A*, K-Means e otimização de entregas"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/rota-inteligente-sabor-express.git
git push -u origin main
```

3. Abra o repositório no navegador e confira se o README aparece formatado e se o mapa (`outputs/mapa_rotas.svg`) aparece na seção 4.
4. Edite a tabela de links no topo do `README.md` com o endereço real do repositório e do vídeo (pode editar direto no GitHub, no ícone de lápis).
5. Teste em uma janela anônima se o link abre sem login (prova de que está público).

Alternativa sem terminal: em "Add file → Upload files" no GitHub, arraste todas as pastas e arquivos do projeto (exceto `__pycache__`).
