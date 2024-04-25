{% comment %}
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 5 de Dezembro de 2020
{% endcomment %}

{% comment %} Código para apresentar tooltips nos objetos {% endcomment %}
{% comment %} Deixar sempre o document.ready para garantir que o código só será executado após o carregamento completo da página. {% endcomment %}
$(document).ready(function() {
  {% if tipo_tooltip == "lento" %}
    $("[data-toggle='tooltip']").tooltip("dispose").tooltip({trigger : "hover", boundary: "window", delay: { "show": 500, "hide": 1000 } });
  {% else %}
    $("[data-toggle='tooltip']").tooltip("dispose").tooltip({trigger : "hover", boundary: "window"});
  {% endif %}
});
