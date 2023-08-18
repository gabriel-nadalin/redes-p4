class CamadaEnlace:
    ignore_checksum = False

    def __init__(self, linhas_seriais):
        """
        Inicia uma camada de enlace com um ou mais enlaces, cada um conectado
        a uma linha serial distinta. O argumento linhas_seriais é um dicionário
        no formato {ip_outra_ponta: linha_serial}. O ip_outra_ponta é o IP do
        host ou roteador que se encontra na outra ponta do enlace, escrito como
        uma string no formato 'x.y.z.w'. A linha_serial é um objeto da classe
        PTY (vide camadafisica.py) ou de outra classe que implemente os métodos
        registrar_recebedor e enviar.
        """
        self.enlaces = {}
        self.callback = None
        # Constrói um Enlace para cada linha serial
        for ip_outra_ponta, linha_serial in linhas_seriais.items():
            enlace = Enlace(linha_serial)
            self.enlaces[ip_outra_ponta] = enlace
            enlace.registrar_recebedor(self._callback)

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de enlace
        """
        self.callback = callback

    def enviar(self, datagrama, next_hop):
        """
        Envia datagrama para next_hop, onde next_hop é um endereço IPv4
        fornecido como string (no formato x.y.z.w). A camada de enlace se
        responsabilizará por encontrar em qual enlace se encontra o next_hop.
        """
        # Encontra o Enlace capaz de alcançar next_hop e envia por ele
        self.enlaces[next_hop].enviar(datagrama)

    def _callback(self, datagrama):
        if self.callback:
            self.callback(datagrama)


class Enlace:

    def __init__(self, linha_serial):
        self.linha_serial = linha_serial
        self.linha_serial.registrar_recebedor(self.__raw_recv)
        self.datagramaAux = b''

    def registrar_recebedor(self, callback):
        self.callback = callback

    def enviar(self, datagrama):
        # TODO: Preencha aqui com o código para enviar o datagrama pela linha
        # serial, fazendo corretamente a delimitação de quadros e o escape de
        # sequências especiais, de acordo com o protocolo CamadaEnlace (RFC 1055).
        datagrama = datagrama.replace(b'\xdb', b'\xdb\xdd')
        datagrama = datagrama.replace(b'\xc0', b'\xdb\xdc')
        self.linha_serial.enviar(b'\xc0' + datagrama + b'\xc0')
        pass

    def __raw_recv(self, dados):

        # inicia os dados com o buffer
        datagrama = self.datagramaAux + dados

        # se houverem dados 
        if(datagrama != b''):
            iniLen = len(datagrama)
            datagrama = datagrama.split(b'\xc0')

            # caso tenha terminado, limpa o buffer
            if len(datagrama) < iniLen:
                self.datagramaAux = b''

                # tratamento final byte a byte
                for i in range(len(datagrama)-1):
                    # tratamento das informacoes previamente convertidas
                    datagrama[i] = datagrama[i].replace(b'\xdb\xdd', b'\xdb')
                    datagrama[i] = datagrama[i].replace(b'\xdb\xdc', b'\xc0')

                    if datagrama[i] != b'':
                        try:
                            self.callback(datagrama[i])
                        except:
                            # ignora a exceção, mas mostra na tela
                            import traceback
                            traceback.print_exc()
                        finally:
                            dados = b''
                            datagrama = b''

            # se não, salva no buffer
            else:
                self.datagramaAux = datagrama[len(datagrama)-1]

        pass
