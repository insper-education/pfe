{% comment %}
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 21 de Fevereiro de 2024
{% endcomment %}

{% comment %} Essa rotina é responsável por puxar a última edição selecionada e passa o valor para o seletor. {% endcomment %}

$(document).ready(function() {
  const itemStr = localStorage.getItem("filterEdicao");
  if(!itemStr) return;
  const item = JSON.parse(itemStr);
  const filterEdicao = item?.value;
  const filterEdicaoOption = document.querySelector(`#filterEdicao option[value='${filterEdicao}']`);
  if(filterEdicao && filterEdicaoOption) {
    const prazo = 3600000; // 1 hour
    const now = Date.now();
    if (now > item.expiry + prazo) {  // Verifica se não venceu
      localStorage.removeItem("filterEdicao");
    } else {
      {% if not selecionada_edicao %}  // Só faz se não tiver nada selecionado
        if(filterEdicao != "todas") { // Evita todas pois é muito lento
          document.getElementById("filterEdicao").value = filterEdicao;
        }
      {% endif %}
    }
  }
});
