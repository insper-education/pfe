{% comment %}
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 21 de Fevereiro de 2024
{% endcomment %}

const itemStr = localStorage.getItem("filterEdicao");
const item = JSON.parse(itemStr);
const filterEdicao = item ? item.value : null;
if (filterEdicao !== null && $("#filterEdicao option[value='"+filterEdicao+"']").length > 0 ) {
  const prazo = 3600000; // 1 hora
  const now = new Date().getTime();
  // Verifica se não venceu
  if (now > item.expiry + prazo) {
    localStorage.removeItem("filterEdicao");
  } else {
    if(filterEdicao != "todas") { // Evita todas pois é muito lento
      $("#filterEdicao").val(filterEdicao)
    }
  }
}
