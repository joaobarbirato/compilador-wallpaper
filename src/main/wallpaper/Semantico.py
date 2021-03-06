from wallpaperParser import wallpaperParser
from wallpaperVisitor import wallpaperVisitor
from Simbolo import Simbolo, TabelaSimbolo, ListaTabela


class Erros:
    def __init__(self):
        self.texto = ""

    def existe_texto(self, arg_str=None):
        return self.texto.find(arg_str) > -1

    def adiciona_erro(self, arg_str=None):
        if str is not None:
            if not self.existe_texto(arg_str=arg_str):
                self.texto += arg_str + '\n'

    def print(self):
        print(self.texto)


class Semantico(wallpaperVisitor):
    def __init__(self):
        self.erros = Erros()
        self.imagens = ListaTabela()
        self.formas = ListaTabela()
        # tabela auxiliar para guardar a tabela atual de imagem
        # permite passar uma tabela pelas funções
        self.tabela_imagem = None
        # tabela auxiliar para guardar a tabela atual de forma
        # permite passar uma tabela pelas funções
        self.tabela_forma = None
        self.conteudoImagem = []
        self.caminhos_importado = None
        self.filtro = None
        self.existe_erros = False

    def visitPrograma(self, ctx: wallpaperParser.ProgramaContext):
        if ctx.corpo():
            wallpaperVisitor.visitPrograma(self, ctx)
            for tabela in self.imagens.tabelas:
                # lidando com erros de falta de propriedades
                if tabela.getSimbolo('cor') is None or tabela.getSimbolo('tamanho') is None:
                    if tabela.getSimbolo('cor') is None:
                        self.erros.adiciona_erro(
                            "Erro: cor em " + tabela.nome_tabela + " não identificada.")
                    if tabela.getSimbolo('tamanho') is None:
                        self.erros.adiciona_erro(
                            "Erro: tamanho em " + tabela.nome_tabela + " não identificado.")
                    self.existe_erros = True
                    return
        else:
            self.erros.adiciona_erro("Erro: propriedades não identificadas.")

        return self.existe_erros

    def visitImagem(self, ctx: wallpaperParser.ImagemContext):
        if self.imagens.exist(ctx.IDENT()):
            self.erros.adiciona_erro('Erro: O identificador ' + str(ctx.IDENT()) + ' já foi declarado.')
        else:
            self.imagens.addTabela(TabelaSimbolo(ctx.IDENT().getText()))

    def visitCorpo(self, ctx: wallpaperParser.CorpoContext):
        if not self.imagens.exist(ctx.IDENT()):
            self.erros.adiciona_erro('Erro: O identificador ' + str(ctx.IDENT()) + ' não foi declarado.')
        else:
            self.tabela_imagem = self.imagens.getTabela(ctx.IDENT())
            if ctx.propriedade():
                self.visitPropriedade(ctx.propriedade())

            else:
                self.erros.adiciona_erro("Erro: Nome não identificado.")

    def visitPropriedade(self, ctx: wallpaperParser.PropriedadeContext):
        if ctx.cor():
            if not self.tabela_imagem.getSimbolo('cor'):
                self.tabela_imagem.addSimbolo(Simbolo('cor', ctx.cor().HEX().getText()))
            else:
                self.erros.adiciona_erro('Erro: A cor já foi adicionada à imagem.')
                self.existe_erros = True
                return

        elif ctx.tamanho():
            tam = ctx.tamanho()
            # print(tam.getText())
            if tam:
                if not self.tabela_imagem.getSimbolo('tamanho'):
                    # print("opa")
                    self.tabela_imagem.addSimbolo(
                        Simbolo('tamanho', (int(tam.NUM_INT(0).getText()), int(tam.NUM_INT(1).getText()))))
                else:
                    self.erros.adiciona_erro('Erro: O tamanho já foi adicionado à imagem.')
                    self.existe_erros = True
                    return
            else:
                self.erros.adiciona_erro('Erro: tamanho em '+ self.tabela_imagem.nome_tabela + ' nao definido')

        elif ctx.nome_arquivo():
            if not self.tabela_imagem.getSimbolo('nome'):
                self.tabela_imagem.addSimbolo(Simbolo('nome',ctx.nome_arquivo().CAMINHO().getText().replace('"','')))
            else:
                self.erros.adiciona_erro('Erro: Imagem já possui um nome de arquivo.')
                self.existe_erros = True
                return

        elif ctx.conteudo():
            for conteudo in self.conteudoImagem:
                if conteudo == self.tabela_imagem.nome_tabela:
                    print('Imagem ', self.tabela_imagem.nome_tabela,'  já possui um conteúdo.')
                    self.existe_erros = True
                    return

            self.conteudoImagem.append(self.tabela_imagem.nome_tabela)
            self.visitConteudo(ctx.conteudo())

        elif ctx.filtro():
            self.visitFiltro(ctx.filtro())

    def visitFiltro(self, ctx: wallpaperParser.FiltroContext):
            self.visitFiltro_opcoes(ctx.filtro_opcoes())

    def visitFiltro_opcoes(self, ctx: wallpaperParser.Filtro_opcoesContext):
        filtro = ctx.getText()
        self.tabela_imagem.addSimbolo(Simbolo("filtro", filtro))

    def visitConteudo(self, ctx: wallpaperParser.ConteudoContext):
        for valor in ctx.valores():
            self.visitValores(valor)

        for referencia in ctx.referencia():
            self.visitReferencia(referencia)

    def visitReferencia(self, ctx: wallpaperParser.ReferenciaContext):
        # verificar primeiro IDENT tabela de imagens
        # verificar segundo IDENT tabela de formas
        # verificar terceiro IDENT que é o chave da nova forma

        copy_forma = self.formas.getTabela(ctx.IDENT(1))
        self.tabela_forma = TabelaSimbolo(ctx.IDENT(2).getText())
        self.tabela_imagem.addSimbolo(Simbolo('chave', ctx.IDENT(2).getText()))

        if ctx.cor():
            self.tabela_forma.addSimbolo(Simbolo('cor', ctx.cor().HEX()))
        else:
            self.tabela_forma.addSimbolo(Simbolo('cor', copy_forma.getSimbolo('cor').valor))

        if ctx.posicao():
            posicao = ctx.posicao()
            self.tabela_forma.addSimbolo(
                Simbolo('posicao', (int(posicao.NUM_INT(0).getText()), int(posicao.NUM_INT(1).getText()),
                                    int(posicao.NUM_INT(2).getText()), int(posicao.NUM_INT(3).getText()))))
        else:
            self.tabela_forma.addSimbolo(Simbolo('posicao', copy_forma.getSimbolo('posicao').valor))

        self.tabela_forma.addSimbolo(Simbolo('formato', copy_forma.getSimbolo('formato').valor))

        self.formas.addTabela(self.tabela_forma)
        self.tabela_forma = None

    def visitValores(self, ctx: wallpaperParser.ValoresContext):
        if ctx.forma() is not None:
            self.visitAtributos(ctx.atributos())
            if self.tabela_forma is not None:
                self.tabela_forma.addSimbolo(Simbolo('formato', ctx.forma().getText()))
        elif ctx.caminho() is not None:
            if ctx.chave() is not None:
                self.visitCaminho(ctx.caminho())
                __tamanho = (int(ctx.tamanho().NUM_INT(0).getText()), int(ctx.tamanho().NUM_INT(1).getText())) \
                    if ctx.tamanho() else None

                self.tabela_imagem.addSimbolo(Simbolo('importado', (self.caminhos_importado, __tamanho)))

            else:
                self.existe_erros = True

    def visitCaminho(self, ctx:wallpaperParser.CaminhoContext):
        caminhos = ctx.CAMINHO()
        if caminhos:
            self.caminhos_importado = caminhos.getText().replace('"','')

    def visitAtributos(self, ctx:wallpaperParser.AtributosContext):

        if not ctx.chave().getText():
            self.existe_erros = True
            return  # exit()
        # Verifica se já foi declarado o identificador da forma (chave)
        if self.formas.exist(ctx.chave().IDENT()) or self.imagens.exist(ctx.chave().IDENT()):
            self.erros.adiciona_erro('Erro: O identificador ' + ctx.chave().IDENT().getText() + ' já foi declarado.')
            self.existe_erros = True
            return
        else:
            # adiciona uma entrada do tipo chave na tabela de simbolos da imagem
            self.tabela_imagem.addSimbolo(Simbolo('chave', ctx.chave().IDENT().getText()))

            # atribui a tabela de forma para a tabela auxiliar
            self.tabela_forma = TabelaSimbolo(ctx.chave().IDENT().getText())
            self.formas.addTabela(self.tabela_forma)

        if not ctx.cor().HEX():
            self.existe_erros = True
            return

        self.tabela_forma.addSimbolo(Simbolo('cor', ctx.cor().HEX().getText()))

        if not ctx.posicao().NUM_INT():
            self.existe_erros = True
            return

        posicao = ctx.posicao()
        if ctx.posicao().NUM_INT(5) == None:
            self.tabela_forma.addSimbolo(
                Simbolo('posicao', (int(posicao.NUM_INT(0).getText()), int(posicao.NUM_INT(1).getText()),
                                    int(posicao.NUM_INT(2).getText()), int(posicao.NUM_INT(3).getText()))))

        else:
            self.tabela_forma.addSimbolo(
                Simbolo('posicao', (int(posicao.NUM_INT(0).getText()), int(posicao.NUM_INT(1).getText()),
                                    int(posicao.NUM_INT(2).getText()), int(posicao.NUM_INT(3).getText()),
                                    int(posicao.NUM_INT(4).getText()), int(posicao.NUM_INT(5).getText()))))
