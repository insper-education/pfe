{% comment %}
    Desenvolvido para o Projeto Final de Engenharia
    Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
    Data: 5 de Dezembro de 2020
{% endcomment %}

{% comment %} Código para apresentar tooltips nos objetos {% endcomment %}





{% comment %} OBSOLETO {% endcomment %} 

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip('dispose').tooltip({boundary: 'window'});
});
