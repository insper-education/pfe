{% comment %}
    Desenvolvido para o Projeto Final de Engenharia
    Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
    Data: 4 de Fevereiro de 2021
{% endcomment %}



{% comment %} OBSOLETO {% endcomment %}
{% comment %}
$("#spinner").css("visibility", "visible");
var edicao = $("#filterEdicao option:selected").attr("value");
$.ajax({
    type: "POST",
    //url: "Normalmente a mesma página",
    data: {
        edicao: edicao,
        'csrfmiddlewaretoken': '{{ csrf_token }}',
    },
    success: function(response){
        $(".atualizar").replaceWith($(".atualizar",response));
        {% include "tooltips.js" %}
        {% if tabela %}
            {% include "tabelas_scripts.js" %}
            // {% if media %}
            //     var media = table.column({{media}}).data().average();
            //     var media_num = parseFloat(media)
            //     if(!isNaN(media_num)) {
            //         $('#media').html(media_num.toFixed(2));
            //     }
            // {% endif %}
        {% endif %}
        {% if graficos %}
            carrega_graficos();
        {% endif %}
        $("#spinner").css("visibility", "hidden");
    },
    error: function (request, status, error) {
        {% if user.tipo_de_usuario == 4 %} 
            alert(request.responseText);
            jQuery("body").html(request.responseText.replace(/\n/g,"<br>"));
            console.log('error'+request.responseText);
        {% else %}
            jQuery("body").html("Erro no servidor do PFE. Por favor contactar: <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>");
        {% endif %}
    }
});
{% endcomment %}
