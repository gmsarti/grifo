# Linguagem intermediaria


# Selecao de objetos

a cama
qualquer cama
os movies

porta
pilar
janela

os moveis com excecao da cama

a cama e os armarios e o criado mudo

(a selecao é sempre E mas internamente decide se é E ou OU)


#  Selecao de linhas

a parede
as paredes
todas as paredes

???


# Selecao de zonas

??


# Selecao de lados

frente,

fundos ou costas

direito

esquerdo

nome especial para um lado de um objeto em particular

# Regras

circulacao de X entre <objetos> (+ defaults)

<objetos> devem estar dentro de <zona> e  <objeto>

    <lado> do <objeto> deve estar encostado em <paredes>
    <lado> do <objeto> nao deve estar encostado em <paredes> 

<objeto> deve esta a uma distancia maxima de X de <objeto> ou <parede?>


<objeto> deve esta a uma distancia minima de X de <objeto> ou <parede?>

   <objeto> deve estar virado para <objeto> ou <parede>  (frente)
   o lado <lado> do <objeto> deve estar virado para <objeto> ou <parede>

<objetos> devem estar na mesma direcao

  deve haver obstruçao entre <objeto> e <objeto>
  nao deve have obstruçao entre <objeto> e <objeto>


  o core de <objetos> nao devem ter sobreposicao
  o acesso de <objetos> nao devem ter sobreposicao
  o core de <objeto> não deve ter superposicao com o acesso de <objeto>


<objeto> deve ter uma projecao ortogonal de no minimo X% do <objeto> 

# Preferencias

preferencialmente (distancia e projecao ortogonal)

preferencialmente <objetos> devem estar o mais longe possivel

preferencialmente escolher <objeto> em vez de <objeto>


# Grids

<objeto> pode estar em qualquer ponto no reticulado de X por Y

<objeto> pode estar em qualquer ponto da <parede> num passo de X
