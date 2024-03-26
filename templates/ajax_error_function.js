{% comment %}
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 26 de Março de 2024
{% endcomment %}

error: function(request, status, error) {
  {% comment %} {% if user.tipo_de_usuario == 4 and debug %}  {% endcomment %}
  {% if user.tipo_de_usuario == 4 %} 
    if(request.responseText){
      alert(request.responseText);
      jQuery("body").html(request.responseText.replace(/\n/g,"<br>"));
      console.log("error"+request.responseText);
    } else {
      jQuery("body").html("Erro no servidor. Por favor contactar: <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>");
    }
  {% else %}
    jQuery("body").html("Erro no servidor. Por favor contactar: <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>");
  {% endif %}
}