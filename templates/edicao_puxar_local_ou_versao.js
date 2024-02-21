{% comment %}
    Desenvolvido para o Projeto Final de Engenharia
    Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
    Data: 21 de Fevereiro de 2024
{% endcomment %}

{% if not selecionada %}
    // Se veio uma versão definida, não puxar o cache
    var filterEdicao = localStorage.getItem("filterEdicao");
    if (filterEdicao !== null && $("#filterEdicao option[value='"+filterEdicao+"']").length > 0 ) {
        $('#filterEdicao').val(filterEdicao).trigger('change');
    }
{% else %}
    $("#filterEdicao").trigger("change");
{% endif %}
